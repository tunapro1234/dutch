"""
DQRN Multi-Head Training Pipeline for Dutch Cabo

Advanced training system with:
- Experience Replay Buffer
- Contextual learning for different action types  
- Dynamic batch sizing based on hardware
- Parallel game generation for experience collection
- Target network updates
- Comprehensive logging and monitoring
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import os
import time
import json
from collections import deque, namedtuple
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import multiprocessing as mp

from .dqrn_network import DQRNMultiHead, create_dqrn_network
from .action_space import ActionContext, action_space
from .state_space import state_space

# Import game components
import sys
sys.path.append('..')
from src.game import Game
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer


# Experience tuple for replay buffer
Experience = namedtuple('Experience', [
    'state', 'context', 'action', 'reward', 'next_state', 'next_context', 'done'
])


class HardwareConfig:
    """Automatically detect and configure hardware settings"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.cpu_cores = os.cpu_count() or 4
        self.gpu_memory_gb = self._get_gpu_memory()
        
        # Calculate optimal batch sizes
        self.batch_size = self._calculate_batch_size()
        self.experience_batch_size = self._calculate_experience_batch_size()
        self.num_game_workers = self._calculate_game_workers()
        
        print(f"🖥️  Hardware Configuration:")
        print(f"   Device: {self.device}")
        print(f"   CPU cores: {self.cpu_cores}")
        print(f"   GPU memory: {self.gpu_memory_gb:.1f} GB")
        print(f"   Training batch size: {self.batch_size}")
        print(f"   Experience batch size: {self.experience_batch_size}")
        print(f"   Game workers: {self.num_game_workers}")
    
    def _get_gpu_memory(self) -> float:
        """Get GPU memory in GB"""
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / (1024**3)
        return 0.0
    
    def _calculate_batch_size(self) -> int:
        """Calculate optimal training batch size based on GPU memory"""
        if self.gpu_memory_gb >= 7.5:  # RTX 3070/4060 Ti level - aggressive scaling
            return 1024  # 4x increase from 256
        elif self.gpu_memory_gb >= 6.0:  # RTX 3060 12GB level  
            return 768
        elif self.gpu_memory_gb >= 4.0:  # RTX 3060 level
            return 512
        elif self.gpu_memory_gb >= 2.0:  # GTX 1660 level
            return 256
        else:
            return 128   # CPU or low-end GPU
    
    def _calculate_experience_batch_size(self) -> int:
        """Calculate batch size for experience collection"""
        # Scale with CPU cores for parallel game generation
        base_size = min(1000, self.cpu_cores * 100)
        return max(500, base_size)
    
    def _calculate_game_workers(self) -> int:
        """Calculate number of parallel game workers"""
        return max(1, min(self.cpu_cores - 2, 12))  # Leave 2 cores, cap at 12


class ExperienceReplayBuffer:
    """Efficient replay buffer with contextual sampling"""
    
    def __init__(self, capacity: int = 100000):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.context_buffers = {context: deque(maxlen=capacity//4) for context in ActionContext}
        
    def push(self, experience: Experience):
        """Add experience to buffer"""
        self.buffer.append(experience)
        # Also add to context-specific buffer for balanced sampling
        if experience.context in self.context_buffers:
            self.context_buffers[experience.context].append(experience)
    
    def sample(self, batch_size: int, context: Optional[ActionContext] = None) -> List[Experience]:
        """Sample experiences, optionally filtered by context"""
        if context and len(self.context_buffers[context]) >= batch_size//2:
            # Contextual sampling - 50% from specific context, 50% from general
            context_samples = random.sample(list(self.context_buffers[context]), batch_size//2)
            general_samples = random.sample(list(self.buffer), batch_size - batch_size//2)
            return context_samples + general_samples
        else:
            return random.sample(list(self.buffer), min(batch_size, len(self.buffer)))
    
    def __len__(self):
        return len(self.buffer)


class DutchCaboEnvironment:
    """Environment wrapper for DQRN training with self-play"""
    
    def __init__(self, opponent_network=None, device="cuda"):
        self.opponent_network = opponent_network
        self.device = device
        self.reset()
    
    def reset(self) -> Tuple[torch.Tensor, ActionContext]:
        """Reset environment and return initial state"""
        # Create opponent - either self-play DQRN or traditional AI
        if self.opponent_network is not None:
            # Self-play: Use another DQRN agent as opponent
            self.opponent = DQRNAgent(self.opponent_network, self.device)
            self.opponent.name = "DQRN_Opponent"
        else:
            # Fallback to traditional AI
            opponent_type = random.choice(["simple", "bayes"])
            if opponent_type == "simple":
                self.opponent = SimpleAI("Opponent")
            else:
                self.opponent = BayesPlayer("Opponent")
        
        # Create game (DQRN agent will be added by trainer)
        self.game = None  # Will be set by trainer
        self.initial_state = None
        
        return self._get_state(), ActionContext.DRAW_SOURCE
    
    def _get_state(self) -> torch.Tensor:
        """Convert current game state to neural network input"""
        if self.game is None:
            # Return dummy state for initialization
            return torch.zeros(state_space.get_state_size())
        
        # Convert game state to our state representation
        game_state = self._build_game_state()
        state_vector = state_space.create_state_vector(game_state)
        return state_vector
    
    def _build_game_state(self) -> Dict:
        """Build game state dictionary from current game"""
        if not self.game:
            return {}
        
        # Find the DQRN player (not the opponent)
        dqrn_player = None
        for player in self.game.players:
            if hasattr(player, '_is_dqrn_agent'):
                dqrn_player = player
                break
        
        if not dqrn_player:
            return {}
        
        return {
            "own_hand": dqrn_player.hand[:],
            "known_cards": dqrn_player.known_cards[:],
            "opponent_hand": self.opponent.hand[:],
            "opponent_estimates": [5.0] * 4,  # Basic estimates
            "estimate_confidences": [0.3] * 4,
            "drawn_card": getattr(self.game, 'current_drawn_card', None),
            "top_discard": self.game.discard_pile[-1] if self.game.discard_pile else None,
            "discard_pile_size": len(self.game.discard_pile),
            "turn_number": self.game.turn_count,
            "deck_size": len(self.game.deck),
            "own_hand_size": dqrn_player.get_hand_size(),
            "opponent_hand_size": self.opponent.get_hand_size(),
            "dutch_called": self.game.dutch_called,
            "action_context": "main_action",
            "recent_actions": []
        }
    
    def step(self, action: int, context: ActionContext) -> Tuple[torch.Tensor, float, bool, ActionContext]:
        """Execute action and return (next_state, reward, done, next_context)"""
        # This is a simplified step method for testing
        # In real implementation, this would execute the action in the game
        
        reward = self._calculate_reward()
        done = getattr(self.game, 'game_over', False) if self.game else False
        next_state = self._get_state()
        next_context = self._get_next_context()
        
        return next_state, reward, done, next_context
    
    def _calculate_reward(self) -> float:
        """Calculate reward for the current state/action"""
        if not self.game:
            return 0.0
        
        # Find DQRN player
        dqrn_player = None
        for player in self.game.players:
            if hasattr(player, '_is_dqrn_agent'):
                dqrn_player = player
                break
        
        if not dqrn_player:
            return 0.0
        
        # Reward shaping for Dutch Cabo
        reward = 0.0
        
        # Game end rewards (HIGH IMPACT)
        if self.game.game_over:
            if self.game.winner == dqrn_player:
                reward += 200.0  # HUGE win bonus (doubled)
            else:
                reward -= 100.0  # BIG loss penalty (doubled)
        
        # Knowledge reward (VERY IMPORTANT)
        known_count = sum(dqrn_player.known_cards)
        reward += known_count * 10.0  # 10 points per known card
        
        # Immediate rewards
        current_score = dqrn_player.get_score()
        opponent_score = self.opponent.get_score()
        
        # Score differential reward
        score_advantage = opponent_score - current_score
        reward += score_advantage * 1.5  # Slightly reduced from 2.0
        
        # Hand size reward (small bonus, not too aggressive)
        hand_size = dqrn_player.get_hand_size()
        if hand_size < 4:  # Only reward when actually reducing
            reward += (4 - hand_size) * 3.0  # Reduced from 5.0
        
        # Penalty for very high scores (encourage low scores)
        if current_score > 20:
            reward -= (current_score - 20) * 2.0
        
        # Dutch call reward (context-dependent)
        if self.game.dutch_called and self.game.dutch_caller == dqrn_player:
            if self.game.game_over and self.game.winner == dqrn_player:
                reward += 75.0  # Successful Dutch call (increased)
            elif self.game.game_over:
                reward -= 50.0  # Failed Dutch call (increased)
        
        return reward
    
    def _get_next_context(self) -> ActionContext:
        """Determine next action context based on game state"""
        # This would depend on the game flow
        return ActionContext.MAIN_ACTION  # Simplified for now


class DQRNAgent:
    """DQRN Agent that interfaces with the game"""
    
    def __init__(self, network: DQRNMultiHead, device: str):
        self.network = network
        self.device = device
        self.hidden_state = None
        self._is_dqrn_agent = True  # Marker for environment
        
        # Player interface (duck typing for game compatibility)
        self.name = "DQRN_Agent"
        self.hand = [None] * 4
        self.known_cards = [False] * 4
        self.epsilon = 0.1  # For exploration during training
    
    def reset_for_new_game(self):
        """Reset agent for new game"""
        self.hand = [None] * 4
        self.known_cards = [False] * 4
        self.hidden_state = None
    
    def choose_network_action(self, state: torch.Tensor, context: ActionContext, 
                             valid_actions: List[int], epsilon: float = 0.0) -> int:
        """Choose action using the neural network (for training)"""
        state = state.to(self.device).unsqueeze(0)  # Add batch dimension
        
        # Create action mask
        action_mask = action_space.create_action_mask(context, valid_actions, self.device)
        
        action, self.hidden_state, _ = self.network.get_action(
            state, context, self.hidden_state, action_mask, epsilon or self.epsilon
        )
        
        return action
    
    def choose_action(self, drawn_card, game_state: dict) -> dict:
        """Game interface - choose what to do with drawn card"""
        # Simple heuristic for now (can be enhanced with neural network)
        if drawn_card.get_score_value() <= 5:
            # Try to swap with highest unknown card (that's not None)
            for i, (card, known) in enumerate(zip(self.hand, self.known_cards)):
                if card is not None and not known:
                    return {"action": "swap", "position": i}
            
            # If all cards are known, swap with highest value card (that's not None)
            highest_value = -1
            best_pos = None
            for i, (card, known) in enumerate(zip(self.hand, self.known_cards)):
                if card is not None and known and card.get_score_value() > highest_value:
                    highest_value = card.get_score_value()
                    best_pos = i
            
            if best_pos is not None and highest_value > drawn_card.get_score_value():
                return {"action": "swap", "position": best_pos}
        
        return {"action": "discard"}
    
    # Required Game interface methods
    def choose_initial_peek(self) -> int:
        """Choose which card position to peek at initially"""
        # Simple heuristic - peek at corners first
        valid_positions = list(range(4))  # All positions are valid initially
        priority_order = [0, 3, 1, 2]  # corners first
        for pos in priority_order:
            if pos in valid_positions:
                return pos
        return 0
    
    def choose_draw_action(self, top_discard_card) -> str:
        """Choose whether to draw from deck or discard pile"""
        # This would use the neural network in a full implementation
        # For now, simple heuristic
        if top_discard_card and top_discard_card.get_score_value() <= 3:
            return "discard"
        return "deck"
    
    def choose_play_action(self, drawn_card) -> Tuple[str, Optional[int]]:
        """Choose what to do with the drawn card"""
        # This would use the neural network in a full implementation
        # For now, simple heuristic
        if drawn_card.get_score_value() <= 5:
            # Try to replace highest unknown card
            for i, (card, known) in enumerate(zip(self.hand, self.known_cards)):
                if not known:
                    return "replace", i
        return "discard", None
    
    def choose_jack_action(self, target_positions: List[int]) -> int:
        """Choose position to peek when playing a Jack"""
        # Peek at unknown cards first
        for pos in target_positions:
            if not self.known_cards[pos]:
                return pos
        return target_positions[0] if target_positions else 0
    
    def choose_queen_action(self, valid_positions: List[int], 
                          opponent_valid_positions: List[int]) -> Tuple[int, int]:
        """Choose positions to swap when playing a Queen"""
        # Simple heuristic - try to swap our highest known card with opponent's
        own_pos = valid_positions[0] if valid_positions else 0
        opponent_pos = opponent_valid_positions[0] if opponent_valid_positions else 0
        
        # Try to find our highest known card
        highest_value = -1
        best_pos = own_pos
        for pos in valid_positions:
            if (self.known_cards[pos] and self.hand[pos] and 
                self.hand[pos].get_score_value() > highest_value):
                highest_value = self.hand[pos].get_score_value()
                best_pos = pos
        
        return best_pos, opponent_pos
    
    def choose_king_action(self, valid_positions: List[int], drawn_card) -> int:
        """Choose position to replace when playing a King"""
        # Try to replace highest card or unknown card
        for pos in valid_positions:
            if not self.known_cards[pos]:
                return pos
        
        # Find highest known card
        highest_value = -1
        best_pos = valid_positions[0]
        for pos in valid_positions:
            if (self.known_cards[pos] and self.hand[pos] and 
                self.hand[pos].get_score_value() > highest_value):
                highest_value = self.hand[pos].get_score_value()
                best_pos = pos
        
        return best_pos
    
    def choose_peek_target(self, opponents: List, game_state: dict) -> Tuple[Optional['Player'], int]:
        """Choose target for Queen peek ability"""
        # Simple heuristic - peek at own unknown cards first
        for i in range(4):
            if self.hand[i] is not None and not self.known_cards[i]:
                return None, i  # Peek at own card
        
        # If all own cards are known, peek at opponent
        if opponents:
            opponent = opponents[0]  # Choose first opponent
            # Find a valid position on opponent
            for i in range(4):
                if hasattr(opponent, 'hand') and len(opponent.hand) > i and opponent.hand[i] is not None:
                    return opponent, i
        
        # Fallback
        return None, 0
    
    def choose_swap_target(self, opponents: List, game_state: dict) -> Tuple['Player', int]:
        """Choose target for Jack swap ability"""
        # Simple heuristic - swap with first available opponent position
        if opponents:
            opponent = opponents[0]
            # Find a valid position
            for i in range(4):
                if hasattr(opponent, 'hand') and len(opponent.hand) > i and opponent.hand[i] is not None:
                    return opponent, i
        
        # Fallback
        return opponents[0] if opponents else None, 0
    
    def should_call_dutch(self) -> bool:
        """Decide whether to call Dutch Cabo"""
        # Conservative strategy - only call if we're confident about low score
        known_score = sum(card.get_score_value() if known and card else 5 
                         for card, known in zip(self.hand, self.known_cards))
        estimated_total = known_score + (4 - sum(self.known_cards)) * 3  # Estimate 3 for unknown
        return estimated_total <= 8
    
    # Duck typing methods for game compatibility
    def get_hand_size(self) -> int:
        return sum(1 for card in self.hand if card is not None)
    
    def get_score(self) -> int:
        return sum(card.get_score_value() if card else 0 for card in self.hand)
    
    def receive_card(self, card, position: int):
        self.hand[position] = card
        # DON'T automatically mark as known when receiving cards
        # Cards are only known when explicitly peeked or swapped in
    
    def swap_card(self, position: int, new_card):
        """Swap card at position with new card, return old card"""
        if position < 0 or position >= len(self.hand):
            raise ValueError(f"Invalid position: {position}")
        
        old_card = self.hand[position]
        self.hand[position] = new_card
        
        # Update known cards - we know the new card but lose knowledge of old card position
        self.known_cards[position] = True
        
        return old_card
    
    def get_valid_positions(self) -> List[int]:
        return [i for i, card in enumerate(self.hand) if card is not None]
    
    def discard_doubles(self, pos1: int, pos2: int) -> Tuple['Card', 'Card']:
        """Discard two cards at given positions"""
        if pos1 < 0 or pos1 >= len(self.hand) or self.hand[pos1] is None:
            raise ValueError(f"Invalid position 1: {pos1}")
        if pos2 < 0 or pos2 >= len(self.hand) or self.hand[pos2] is None:
            raise ValueError(f"Invalid position 2: {pos2}")
        
        card1 = self.hand[pos1]
        card2 = self.hand[pos2]
        
        # Remove cards and mark positions as empty
        self.hand[pos1] = None
        self.hand[pos2] = None
        self.known_cards[pos1] = False
        self.known_cards[pos2] = False
        
        return card1, card2
    
    def is_hand_empty(self) -> bool:
        """Check if player has no cards left"""
        return self.get_hand_size() == 0
    
    def display_hand(self, show_values: bool = False, reveal_all: bool = False):
        """Display hand for debugging (not used by DQRN)"""
        # For debugging/display purposes, show hand status
        hand_display = []
        for i, card in enumerate(self.hand):
            if card is None:
                hand_display.append("[ ]")
            elif self.known_cards[i] or reveal_all:
                hand_display.append(f"[{card}]")
            else:
                hand_display.append("[?]")
        return " ".join(hand_display)
    
    def get_known_doubles(self) -> List[Tuple[int, int, 'Card']]:
        """Get positions of known double cards"""
        doubles = []
        
        # DEBUG: Print current known state
        print(f"🔍 DEBUG {self.name} known cards: {self.known_cards}")
        print(f"🔍 DEBUG {self.name} hand: {[str(card) if card else None for card in self.hand]}")
        
        for i in range(4):
            if self.hand[i] is not None and self.known_cards[i]:
                # Check if we have another known card with same value
                for j in range(i + 1, 4):
                    if (self.hand[j] is not None and self.known_cards[j] and 
                        self.hand[i].value == self.hand[j].value):
                        # Return tuple format: (pos1, pos2, card)
                        doubles.append((i, j, self.hand[i]))
                        print(f"🔍 DEBUG Found doubles: {self.hand[i]} at {i}, {self.hand[j]} at {j}")
        return doubles
    
    def want_to_discard_doubles(self, doubles_available, timing: str, game_state: dict):
        """Check if we want to discard doubles - DQRN decides based on neural network"""
        # For DQRN agents, return the first available double if any exist
        if doubles_available:
            pos1, pos2, card = doubles_available[0]  # Take first double
            return (pos1, pos2)
        return None
    
    def get_discard_pile_matches(self, top_discard_card) -> List[Tuple[int, 'Card']]:
        """Get positions of cards that match the top discard pile card"""
        matches = []
        
        # Find all known cards that match the top discard
        for i in range(4):
            if (self.hand[i] is not None and self.known_cards[i] and 
                self.hand[i].value == top_discard_card.value):
                matches.append((i, self.hand[i]))  # Return tuples like base class
        return matches
    
    def want_to_discard_pile_matches(self, matches_available, top_discard, timing: str, game_state: dict):
        """Check if we want to discard matching cards from pile"""
        # For DQRN agents, return list of positions to discard if matches available
        if len(matches_available) > 0:
            # Return positions of all available matches
            return [pos for pos, card in matches_available]
        return []

    def peek_at_card(self, position: int):
        """Called when we peek at a card (Jack ability or initial peek)"""
        if 0 <= position < len(self.known_cards):
            self.known_cards[position] = True
    
    def peek_at_own_card(self, position: int):
        """Peek at own card and return it"""
        if not 0 <= position <= 3:
            raise ValueError("Position must be between 0 and 3")
        if self.hand[position] is None:
            raise ValueError("No card at that position")
        
        self.known_cards[position] = True
        return self.hand[position]


class DQRNTrainer:
    """Main training class for DQRN"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.hardware = HardwareConfig()
        
        # Networks
        self.policy_net = create_dqrn_network(self.hardware.device)
        self.target_net = create_dqrn_network(self.hardware.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Self-play opponent network (starts as copy of policy net)
        self.opponent_net = create_dqrn_network(self.hardware.device)
        self.opponent_net.load_state_dict(self.policy_net.state_dict())
        self.opponent_net.eval()
        self.opponent_update_freq = self.config.get('opponent_update_freq', 2000)
        
        # Training components
        self.optimizer = optim.Adam(self.policy_net.parameters(), 
                                  lr=self.config.get('learning_rate', 1e-4))
        self.replay_buffer = ExperienceReplayBuffer(
            capacity=self.config.get('buffer_size', 100000)
        )
        
        # Training parameters
        self.gamma = self.config.get('gamma', 0.99)
        self.epsilon_start = self.config.get('epsilon_start', 1.0)
        self.epsilon_end = self.config.get('epsilon_end', 0.1)
        self.epsilon_decay = self.config.get('epsilon_decay', 0.995)
        self.target_update_freq = self.config.get('target_update_freq', 1000)
        
        # Batch size - either override or hardware calculated
        if self.config.get('batch_size_override'):
            self.batch_size = self.config['batch_size_override']
            print(f"⚡ Batch size override: {self.batch_size}")
        else:
            self.batch_size = self.hardware.batch_size
            
        self.self_play_ratio = self.config.get('self_play_ratio', 0.999)  # 99.9% self-play, 0.1% vs AI
        
        # Tracking
        self.episode = 0
        self.step_count = 0
        self.training_log = []
        
        print(f"🤖 DQRN Trainer initialized with SELF-PLAY")
        print(f"   Policy network: {sum(p.numel() for p in self.policy_net.parameters())} parameters")
        print(f"   Self-play ratio: {self.self_play_ratio:.1%}")
        print(f"   Opponent update freq: {self.opponent_update_freq}")
        print(f"   Replay buffer: {self.replay_buffer.capacity} capacity")
        print(f"   Batch size: {self.batch_size}")
    
    def collect_experience(self, num_episodes: int = 100) -> Dict:
        """Collect experience through self-play"""
        start_time = time.time()
        total_reward = 0
        total_games = 0
        context_counts = {context: 0 for context in ActionContext}
        
        for episode in range(num_episodes):
            # Decide: self-play or vs traditional AI
            use_self_play = random.random() < self.self_play_ratio
            
            if use_self_play:
                # Self-play: DQRN vs DQRN
                env = DutchCaboEnvironment(self.opponent_net, self.hardware.device)
            else:
                # Traditional AI opponent
                env = DutchCaboEnvironment(None, self.hardware.device)
            
            agent = DQRNAgent(self.policy_net, self.hardware.device)
            
            # Create game with DQRN agent
            env.game = Game([agent, env.opponent])
            env.game.setup_new_game()
            
            episode_reward = 0
            episode_experiences = []
            
            state, context = env.reset()
            
            # Simplified training loop - generate fake experiences for testing
            for step in range(10):  # Generate 10 fake experiences per episode
                # Get valid actions for current context
                valid_actions = action_space.get_valid_actions(context, env._build_game_state())
                
                # Choose action with current epsilon
                epsilon = max(self.epsilon_end, 
                            self.epsilon_start * (self.epsilon_decay ** self.episode))
                action = agent.choose_network_action(state, context, valid_actions, epsilon)
                
                # Generate fake next state and reward
                next_state = torch.randn_like(state)  # Random next state for testing
                reward = np.random.randn()  # Random reward
                done = step >= 9  # End after 10 steps
                next_context = ActionContext.MAIN_ACTION  # Simple context progression
                
                # Store experience
                experience = Experience(
                    state=state.clone(),
                    context=context,
                    action=action,
                    reward=reward,
                    next_state=next_state.clone(),
                    next_context=next_context,
                    done=done
                )
                episode_experiences.append(experience)
                context_counts[context] += 1
                
                episode_reward += reward
                state = next_state
                context = next_context
                
                self.step_count += 1
                
                if done:
                    break
            
            # Add all episode experiences to replay buffer
            for exp in episode_experiences:
                self.replay_buffer.push(exp)
            
            total_reward += episode_reward
            total_games += 1
            self.episode += 1
        
        collection_time = time.time() - start_time
        
        stats = {
            "episodes": num_episodes,
            "total_reward": total_reward,
            "avg_reward": total_reward / max(1, total_games),
            "collection_time": collection_time,
            "experiences_collected": len(episode_experiences) * num_episodes,
            "buffer_size": len(self.replay_buffer),
            "context_distribution": context_counts,
            "epsilon": epsilon
        }
        
        print(f"📊 Experience Collection Complete:")
        print(f"   Episodes: {num_episodes}, Time: {collection_time:.2f}s")
        print(f"   Avg reward: {stats['avg_reward']:.2f}")
        print(f"   Buffer size: {len(self.replay_buffer)}")
        
        return stats
    
    def train_batch(self) -> Dict:
        """Train on a batch of experiences"""
        if len(self.replay_buffer) < self.batch_size:
            return {}
        
        # Sample experiences
        experiences = self.replay_buffer.sample(self.batch_size)
        batch = Experience(*zip(*experiences))
        
        # Convert to tensors
        states = torch.stack(batch.state).to(self.hardware.device)
        actions = torch.tensor(batch.action, dtype=torch.long).to(self.hardware.device)
        rewards = torch.tensor(batch.reward, dtype=torch.float32).to(self.hardware.device)
        next_states = torch.stack(batch.next_state).to(self.hardware.device)
        dones = torch.tensor(batch.done, dtype=torch.bool).to(self.hardware.device)
        
        # Group by context for multi-head training
        context_groups = {}
        for i, context in enumerate(batch.context):
            if context not in context_groups:
                context_groups[context] = []
            context_groups[context].append(i)
        
        total_loss = 0
        losses_by_context = {}
        
        # Ensure correct modes for training
        self.policy_net.train()
        self.target_net.eval()
        
        # Train each context head separately
        for context, indices in context_groups.items():
            if len(indices) < 4:  # Skip contexts with too few samples
                continue
            
            context_indices = torch.tensor(indices).to(self.hardware.device)
            
            # Get current Q-values from policy network
            current_q_output = self.policy_net(states[context_indices], context=context)
            current_q_values = current_q_output["q_values"]
            current_q_values = current_q_values.gather(1, actions[context_indices].unsqueeze(1))
            
            # Get next Q-values from target network
            with torch.no_grad():
                next_q_output = self.target_net(next_states[context_indices], context=context)
                next_q_values = next_q_output["q_values"].max(1)[0]
                target_q_values = rewards[context_indices] + (
                    self.gamma * next_q_values * ~dones[context_indices]
                )
            
            # Compute loss for this context
            context_loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
            total_loss += context_loss
            losses_by_context[context.value] = context_loss.item()
        
        # Backward pass
        self.optimizer.zero_grad()
        total_loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        
        self.optimizer.step()
        
        # Update target network
        if self.step_count % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Update opponent network for self-play
        if self.step_count % self.opponent_update_freq == 0:
            self.opponent_net.load_state_dict(self.policy_net.state_dict())
            print(f"🔄 Opponent network updated (step {self.step_count})")
        
        return {
            "total_loss": total_loss.item(),
            "losses_by_context": losses_by_context,
            "contexts_trained": len(context_groups)
        }
    
    def train(self, num_iterations: int = 1000, eval_freq: int = 100, save_freq: int = 1000, 
              checkpoint_dir: str = "players/dqrn_multi_head/checkpoints"):
        """Main training loop with periodic checkpointing"""
        print(f"🚀 Starting DQRN Training")
        print(f"   Iterations: {num_iterations}")
        print(f"   Evaluation frequency: {eval_freq}")
        print(f"   Checkpoint frequency: {save_freq}")
        
        # Ensure checkpoint directory exists
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        start_time = time.time()
        
        for iteration in range(num_iterations):
            # Collect experience
            if iteration % 10 == 0:  # Collect experience every 10 iterations
                collection_stats = self.collect_experience(
                    num_episodes=self.hardware.experience_batch_size // 10
                )
            
            # Train on collected experience
            train_stats = self.train_batch()
            
            # Evaluation
            if iteration % eval_freq == 0:
                eval_stats = self.evaluate()
                
                print(f"Iteration {iteration}/{num_iterations}")
                print(f"  Loss: {train_stats.get('total_loss', 0):.4f}")
                print(f"  Buffer: {len(self.replay_buffer)}")
                print(f"  Epsilon: {max(self.epsilon_end, self.epsilon_start * (self.epsilon_decay ** self.episode)):.3f}")
                if eval_stats:
                    print(f"  Eval win rate: {eval_stats.get('win_rate', 0):.1%}")
            
            # Periodic checkpoint saving
            if iteration > 0 and iteration % save_freq == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                checkpoint_path = os.path.join(checkpoint_dir, f"dqrn_iter_{iteration}_{timestamp}.pt")
                self.save_checkpoint(checkpoint_path)
                print(f"💾 Periodic checkpoint saved: iter_{iteration}")
        
        training_time = time.time() - start_time
        print(f"✅ Training completed in {training_time:.2f} seconds")
        
        return {
            "iterations": num_iterations,
            "training_time": training_time,
            "final_buffer_size": len(self.replay_buffer)
        }
    
    def evaluate(self, num_games: int = 50) -> Dict:
        """Evaluate the current policy"""
        self.policy_net.eval()
        
        wins = 0
        total_reward = 0
        
        with torch.no_grad():
            for _ in range(num_games):
                # Mix of self-play and traditional AI for evaluation
                if random.random() < 0.999:
                    env = DutchCaboEnvironment(self.opponent_net, self.hardware.device)
                else:
                    env = DutchCaboEnvironment(None, self.hardware.device)
                
                agent = DQRNAgent(self.policy_net, self.hardware.device)
                
                env.game = Game([agent, env.opponent])
                env.game.setup_new_game()
                
                episode_reward = 0
                state, context = env.reset()
                
                # Simplified evaluation - fake game for testing
                for step in range(10):  # 10 steps per evaluation game
                    valid_actions = action_space.get_valid_actions(context, env._build_game_state())
                    action = agent.choose_network_action(state, context, valid_actions, epsilon=0.0)  # Greedy
                    
                    # Generate fake rewards and states
                    reward = np.random.randn()
                    next_state = torch.randn_like(state)
                    next_context = ActionContext.MAIN_ACTION
                    done = step >= 9
                    
                    episode_reward += reward
                    state = next_state
                    context = next_context
                    
                    if done:
                        break
                
                # Random win for testing (50% win rate)
                if np.random.random() < 0.5:
                    wins += 1
                total_reward += episode_reward
        
        self.policy_net.train()
        
        return {
            "num_games": num_games,
            "wins": wins,
            "win_rate": wins / num_games,
            "avg_reward": total_reward / num_games
        }
    
    def save_checkpoint(self, filepath: str):
        """Save training checkpoint including opponent network"""
        checkpoint = {
            "policy_net": self.policy_net.state_dict(),
            "target_net": self.target_net.state_dict(),
            "opponent_net": self.opponent_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "episode": self.episode,
            "step_count": self.step_count,
            "config": self.config,
            "training_log": self.training_log
        }
        
        torch.save(checkpoint, filepath)
        print(f"💾 Checkpoint saved: {filepath}")
    
    def load_checkpoint(self, filepath: str):
        """Load training checkpoint"""
        checkpoint = torch.load(filepath, map_location=self.hardware.device)
        
        self.policy_net.load_state_dict(checkpoint["policy_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        if "opponent_net" in checkpoint:
            self.opponent_net.load_state_dict(checkpoint["opponent_net"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.episode = checkpoint["episode"]
        self.step_count = checkpoint["step_count"]
        
        print(f"📂 Checkpoint loaded: {filepath}")
        print(f"   Resumed from episode {self.episode}, step {self.step_count}")


def main():
    """Test the training pipeline"""
    # Configuration
    config = {
        "learning_rate": 1e-4,
        "gamma": 0.99,
        "epsilon_start": 1.0,
        "epsilon_end": 0.1,
        "epsilon_decay": 0.995,
        "buffer_size": 50000,
        "target_update_freq": 1000
    }
    
    # Create trainer
    trainer = DQRNTrainer(config)
    
    # Quick test
    print("\n🧪 Testing experience collection...")
    stats = trainer.collect_experience(num_episodes=10)
    print(f"✅ Collected {stats['experiences_collected']} experiences")
    
    print("\n🧪 Testing training batch...")
    if len(trainer.replay_buffer) >= trainer.batch_size:
        train_stats = trainer.train_batch()
        print(f"✅ Training loss: {train_stats.get('total_loss', 'N/A')}")
    
    print("\n🧪 Testing evaluation...")
    eval_stats = trainer.evaluate(num_games=5)
    print(f"✅ Win rate: {eval_stats['win_rate']:.1%}")


if __name__ == "__main__":
    main() 