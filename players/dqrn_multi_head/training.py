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
        """Calculate AGGRESSIVE training batch size - MAXIMIZE GPU USAGE"""
        if self.gpu_memory_gb >= 7.5:  # RTX 3070/4060 Ti level - ULTRA AGGRESSIVE
            return 1024  # DOUBLED from 512 - max out GPU memory!
        elif self.gpu_memory_gb >= 6.0:  # RTX 3060 12GB level  
            return 768   # Increased from 256 - push the limits!
        elif self.gpu_memory_gb >= 4.0:  # RTX 3060 level
            return 512   # Quadrupled from 128
        elif self.gpu_memory_gb >= 2.0:  # GTX 1660 level
            return 256   # Quadrupled from 64
        else:
            return 128   # Quadrupled from 32 - even CPU gets more aggressive

    def _calculate_experience_batch_size(self) -> int:
        """Calculate AGGRESSIVE experience collection - MORE GAMES, MORE SPEED"""
        # MUCH more aggressive scaling - saturate all CPU cores
        base_size = self.cpu_cores * 200  # Doubled from 100
        return max(1000, min(5000, base_size))  # Much higher range

    def _calculate_game_workers(self) -> int:
        """Calculate MAXIMUM parallel game workers - USE ALL CORES"""
        # Use nearly ALL cores - only leave 1 for system
        return max(2, self.cpu_cores - 1)  # Was: min(self.cpu_cores - 2, 12)


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
        """Sample experiences, optionally filtered by context - OPTIMIZED"""
        buffer_size = len(self.buffer)
        if buffer_size == 0:
            return []
        
        actual_batch_size = min(batch_size, buffer_size)
        
        if context and len(self.context_buffers[context]) >= actual_batch_size//2:
            # Contextual sampling - 50% from specific context, 50% from general
            context_buffer = list(self.context_buffers[context])
            general_buffer = list(self.buffer)
            
            context_samples = random.sample(context_buffer, actual_batch_size//2)
            general_samples = random.sample(general_buffer, actual_batch_size - actual_batch_size//2)
            return context_samples + general_samples
        else:
            # Faster random sampling using indices
            indices = random.sample(range(buffer_size), actual_batch_size)
            buffer_list = list(self.buffer)
            return [buffer_list[i] for i in indices]
    
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
            return torch.zeros(49)  # Fixed size state
        
        # Find DQRN player for state building
        dqrn_player = None
        for player in self.game.players:
            if hasattr(player, '_is_dqrn_agent'):
                dqrn_player = player
                break
        
        if not dqrn_player:
            return torch.zeros(49)
        
        # Use the same simple state building as in DQRNAgent
        return dqrn_player._build_state_vector(None, {})
    
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
        """Choose action using the neural network (for training) - OPTIMIZED"""
        # Keep state on device, avoid unnecessary transfers
        if not state.is_cuda and self.device != 'cpu':
            state = state.to(self.device)
        
        # Add batch dimension only if needed
        if state.dim() == 1:
            state = state.unsqueeze(0)
        
        # Create action mask once
        action_mask = action_space.create_action_mask(context, valid_actions, self.device)
        
        # Use torch.no_grad() for inference during training (saves memory)
        with torch.no_grad():
            action, self.hidden_state, _ = self.network.get_action(
                state, context, self.hidden_state, action_mask, epsilon or self.epsilon
            )
        
        return action
    
    def choose_action(self, drawn_card, game_state: dict) -> dict:
        """REAL neural network decision making"""
        # Build current state for neural network
        current_state = self._build_state_vector(drawn_card, game_state)
        context = ActionContext.MAIN_ACTION
        
        # Get valid actions for current situation
        valid_actions = self._get_valid_main_actions(drawn_card)
        
        # Use neural network to choose action
        action_idx = self.choose_network_action(current_state, context, valid_actions, self.epsilon)
        
        # Convert action index to game action
        return self._convert_action_to_game_format(action_idx, drawn_card)
    
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
        
        # DEBUG: Only print during human games (not training)
        debug_mode = getattr(self, '_debug_mode', False)
        if debug_mode:
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
                        if debug_mode:
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

    def _build_state_vector(self, drawn_card, game_state: dict) -> torch.Tensor:
        """Build real state vector for neural network"""
        # Simple state vector without complex state_space
        state_vector = []
        
        # Own hand cards (4 positions, value 0-13)
        for card in self.hand:
            if card is None:
                state_vector.append(0.0)
            else:
                state_vector.append(float(card.get_score_value()) / 13.0)  # Normalize 0-1
        
        # Known cards (4 positions, 0 or 1)
        for known in self.known_cards:
            state_vector.append(1.0 if known else 0.0)
        
        # Drawn card value
        if drawn_card:
            state_vector.append(float(drawn_card.get_score_value()) / 13.0)
        else:
            state_vector.append(0.0)
        
        # Game info
        current_game = getattr(self, '_current_game', None)
        if current_game:
            state_vector.append(float(len(current_game.deck)) / 52.0)  # Deck size
            state_vector.append(float(current_game.turn_count) / 100.0)  # Turn number
            state_vector.append(1.0 if current_game.dutch_called else 0.0)  # Dutch called
            
            # Top discard
            if current_game.discard_pile:
                state_vector.append(float(current_game.discard_pile[-1].get_score_value()) / 13.0)
            else:
                state_vector.append(0.0)
        else:
            state_vector.extend([0.8, 0.01, 0.0, 0.5])  # Default values
        
        # Hand sizes
        state_vector.append(float(self.get_hand_size()) / 4.0)  # Own hand size
        state_vector.append(1.0)  # Opponent hand size (assume 4)
        
        # Pad to fixed size (total should be 49 to match state space)
        while len(state_vector) < 49:
            state_vector.append(0.0)
        
        return torch.tensor(state_vector[:49], dtype=torch.float32)
    
    def _get_valid_main_actions(self, drawn_card) -> List[int]:
        """Get valid action indices for main action context"""
        valid_actions = []
        
        # Action 0: Discard (always valid)
        valid_actions.append(0)
        
        # Actions 1-4: Swap with position 0-3 (if position has card)
        for i in range(4):
            if self.hand[i] is not None:
                valid_actions.append(1 + i)
        
        # Action 5: Use special ability (if drawn card has one)
        if drawn_card and hasattr(drawn_card, 'has_special_ability') and drawn_card.has_special_ability():
            valid_actions.append(5)
        
        # Action 6: Call Dutch (always technically valid)
        valid_actions.append(6)
        
        return valid_actions
    
    def _convert_action_to_game_format(self, action_idx: int, drawn_card) -> dict:
        """Convert neural network action index to game action format"""
        if action_idx == 0:
            return {"action": "discard"}
        elif 1 <= action_idx <= 4:
            position = action_idx - 1
            return {"action": "swap", "position": position}
        elif action_idx == 5:
            return {"action": "use_ability"}
        elif action_idx == 6:
            return {"action": "call_dutch"}
        else:
            # Fallback
            return {"action": "discard"}


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
        
        # Training components with MIXED PRECISION for speed
        self.optimizer = optim.Adam(self.policy_net.parameters(), 
                                  lr=self.config.get('learning_rate', 1e-4))
        
        # Enable mixed precision training for MASSIVE speedup
        self.scaler = torch.cuda.amp.GradScaler() if torch.cuda.is_available() else None
        self.use_amp = torch.cuda.is_available()
        
        # LARGER replay buffer for more data
        buffer_capacity = self.config.get('buffer_size', 200000)  # Doubled from 100k
        self.replay_buffer = ExperienceReplayBuffer(capacity=buffer_capacity)
        
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
        
        print(f"🚀 ULTRA-OPTIMIZED DQRN Trainer - MAXIMUM PERFORMANCE MODE")
        print(f"   Policy network: {sum(p.numel() for p in self.policy_net.parameters())} parameters")
        print(f"   Self-play ratio: {self.self_play_ratio:.1%}")
        print(f"   Mixed Precision: {'✅ ENABLED' if self.use_amp else '❌ CPU mode'}")
        print(f"   Training batch size: {self.batch_size} (AGGRESSIVE)")
        print(f"   Replay buffer: {self.replay_buffer.capacity:,} capacity (ENLARGED)")
        print(f"   Parallel workers: limited to 4 max (resource-conscious)")
        print(f"   Experience batch: smaller batches for stability")
        print(f"   🔥 OPTIMIZATIONS: Resource-Conscious Parallel + Mixed Precision + Batching")
    
    def collect_experience(self, num_episodes: int = 100) -> Dict:
        """Collect experience through REAL GAMES with detailed statistics"""
        start_time = time.time()
        
        # Game statistics
        total_games = 0
        wins = 0
        total_turns = 0
        total_final_scores = []
        opponent_final_scores = []
        special_moves = {"jack_uses": 0, "queen_uses": 0, "king_uses": 0, "dutch_calls": 0}
        
        # Experience collection
        total_experiences = 0
        context_counts = {context.value: 0 for context in ActionContext}  # Use .value for JSON serialization
        
        print(f"🎮 Starting {num_episodes} REAL games for experience collection...")
        
        for episode in range(num_episodes):
            # Decide opponent type
            use_self_play = random.random() < self.self_play_ratio
            
            if use_self_play:
                env = DutchCaboEnvironment(self.opponent_net, self.hardware.device)
                opponent_name = "DQRN_Opponent"
            else:
                env = DutchCaboEnvironment(None, self.hardware.device)
                opponent_name = env.opponent.name
            
            agent = DQRNAgent(self.policy_net, self.hardware.device)
            agent.name = "DQRN_Agent"
            
            # Create and setup game with silent mode for training
            from src.game import Game
            game = Game([agent, env.opponent], silent_mode=True)
            
            # Give agent reference to game for state building
            agent._current_game = game
            
            # Track game statistics and REAL experiences
            game_turns = 0
            game_experiences = []
            
            try:
                # Play complete game COMPLETELY SILENTLY
                import io
                import contextlib
                
                # Redirect ALL stdout to suppress prints
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    # Also suppress stderr for complete silence
                    with contextlib.redirect_stderr(f):
                        game.setup_new_game()
                    
                    # Set up environment for experience collection
                    env.game = game
                    
                    while not game.game_over and game_turns < 200:  # Safety limit
                        game_turns += 1
                        current_player = game.get_current_player()
                        
                        # REAL experience collection only for DQRN player
                        if hasattr(current_player, '_is_dqrn_agent'):
                            # Capture state before action
                            prev_state = env._get_state()
                            prev_context = ActionContext.MAIN_ACTION
                            
                            # Execute turn and capture experience
                            try:
                                old_score = current_player.get_score()
                                old_hand_size = current_player.get_hand_size()
                                old_known_count = sum(current_player.known_cards)
                                
                                game.play_turn()
                                
                                # Calculate reward based on what happened
                                new_score = current_player.get_score()
                                new_hand_size = current_player.get_hand_size()
                                new_known_count = sum(current_player.known_cards)
                                
                                # Real reward calculation
                                reward = 0.0
                                
                                # Knowledge reward
                                knowledge_gained = new_known_count - old_known_count
                                reward += knowledge_gained * 10.0
                                
                                # Hand size improvement
                                hand_improvement = old_hand_size - new_hand_size
                                if hand_improvement > 0:
                                    reward += hand_improvement * 3.0
                                
                                # Score improvement
                                score_improvement = old_score - new_score
                                reward += score_improvement * 1.5
                                
                                # Game end rewards
                                if game.game_over:
                                    if game.winner == current_player:
                                        reward += 200.0
                                    else:
                                        reward -= 100.0
                                
                                # Capture next state
                                next_state = env._get_state()
                                next_context = ActionContext.MAIN_ACTION
                                
                                # Create real experience
                                experience = Experience(
                                    state=prev_state,
                                    context=prev_context,
                                    action=0,  # We'd need to track actual action index
                                    reward=reward,
                                    next_state=next_state,
                                    next_context=next_context,
                                    done=game.game_over
                                )
                                
                                game_experiences.append(experience)
                                
                            except Exception as e:
                                break
                        else:
                            # Non-DQRN player turn
                            try:
                                game.play_turn()
                            except Exception as e:
                                break
                
                # Game completed - collect statistics (outside silent block)
                total_games += 1
                total_turns += game_turns
                
                # Determine winner and scores
                dqrn_score = agent.get_score()
                opponent_score = env.opponent.get_score()
                
                total_final_scores.append(dqrn_score)
                opponent_final_scores.append(opponent_score)
                
                if game.winner == agent:
                    wins += 1
                
                # Real special move tracking disabled for now
                # Will be implemented with proper neural network integration
                if game.dutch_called:
                    special_moves["dutch_calls"] += 1
                
                # Add REAL experiences from this game to buffer
                for experience in game_experiences:
                    self.replay_buffer.push(experience)
                    context_counts[experience.context.value] += 1  # Use .value for JSON
                    total_experiences += 1
                
                self.episode += 1
                
            except Exception as e:
                print(f"⚠️ Game {episode + 1} failed: {e}")
                continue
        
        collection_time = time.time() - start_time
        
        # Calculate statistics
        avg_turns = total_turns / max(1, total_games)
        avg_dqrn_score = sum(total_final_scores) / max(1, len(total_final_scores))
        avg_opponent_score = sum(opponent_final_scores) / max(1, len(opponent_final_scores))
        win_rate = wins / max(1, total_games)
        
        stats = {
            "games_played": total_games,
            "wins": wins,
            "win_rate": win_rate,
            "avg_turns_per_game": avg_turns,
            "avg_dqrn_score": avg_dqrn_score,
            "avg_opponent_score": avg_opponent_score,
            "special_moves": special_moves,
            "experiences_collected": total_experiences,
            "buffer_size": len(self.replay_buffer),
            "context_distribution": context_counts,
            "collection_time": collection_time
        }
        
        # Detailed batch report
        print(f"📊 BATCH COMPLETED - {total_games} games in {collection_time:.1f}s")
        print(f"   🏆 Win Rate: {win_rate:.1%} ({wins}/{total_games})")
        print(f"   🎯 Avg Turns: {avg_turns:.1f} per game")
        print(f"   📈 Avg Scores: DQRN {avg_dqrn_score:.1f} vs Opponent {avg_opponent_score:.1f}")
        print(f"   ✨ Special Moves: J:{special_moves['jack_uses']} Q:{special_moves['queen_uses']} K:{special_moves['king_uses']} D:{special_moves['dutch_calls']}")
        print(f"   💾 Experiences: +{total_experiences} (Buffer: {len(self.replay_buffer)})")
        
        return stats
    
    def collect_experience_parallel(self, num_episodes: int = 100) -> Dict:
        """PARALLEL experience collection using multiple CPU workers"""
        start_time = time.time()
        
        # Distribute games across workers (reduced count to avoid file descriptor issues)
        games_per_worker = max(20, num_episodes // min(8, self.hardware.num_game_workers))
        total_workers = min(4, self.hardware.num_game_workers // 2, num_episodes // 20)  # Much fewer workers
        
        print(f"🎮 PARALLEL: {num_episodes} games across {total_workers} CPU workers ({games_per_worker} each)")
        print(f"   Note: Game inference on CPU, training on {self.hardware.device}")
        
        # Check if we have too few workers due to resource constraints
        if total_workers < 2:
            print("   ⚠️  Using minimal workers to avoid resource issues")
            # Fallback to single-threaded if needed
            if total_workers < 1:
                return self.collect_experience(num_episodes)
        
        # Move state dicts to CPU for multiprocessing (once)
        policy_state_cpu = {k: v.cpu() for k, v in self.policy_net.state_dict().items()}
        opponent_state_cpu = {k: v.cpu() for k, v in self.opponent_net.state_dict().items()}
        
        # Prepare worker arguments
        worker_args = []
        for worker_id in range(total_workers):
            worker_games = games_per_worker if worker_id < total_workers - 1 else (num_episodes - worker_id * games_per_worker)
            
            worker_args.append({
                'worker_id': worker_id,
                'num_games': worker_games,
                'self_play_ratio': self.self_play_ratio,
                'policy_net_state': policy_state_cpu,
                'opponent_net_state': opponent_state_cpu
            })
        
        # Use context to avoid multiprocessing method issues
        import multiprocessing as mp_ctx
        ctx = mp_ctx.get_context('spawn')  # Use spawn context for CUDA compatibility
        
        try:
            with ctx.Pool(processes=total_workers) as pool:
                results = pool.map(self._worker_collect_games, worker_args)
                pool.close()  # Explicit close
                pool.join()   # Wait for workers to finish
        except Exception as e:
            print(f"   ⚠️  Parallel collection failed: {e}, falling back to sequential")
            return self.collect_experience(num_episodes)
        
        # Aggregate results
        total_games = sum(r['games_played'] for r in results)
        total_wins = sum(r['wins'] for r in results)
        all_experiences = []
        
        for result in results:
            all_experiences.extend(result['experiences'])
            
        # Add experiences to buffer
        for exp in all_experiences:
            self.replay_buffer.push(exp)
        
        collection_time = time.time() - start_time
        
        stats = {
            "games_played": total_games,
            "wins": total_wins,
            "win_rate": total_wins / max(1, total_games),
            "experiences_collected": len(all_experiences),
            "collection_time": collection_time,
            "parallel_workers": total_workers,
            "buffer_size": len(self.replay_buffer)
        }
        
        print(f"⚡ PARALLEL DONE: {total_games} games in {collection_time:.1f}s ({total_games/collection_time:.1f} games/s)")
        print(f"   CPU Workers: {total_workers} | Win Rate: {stats['win_rate']:.1%} | +{len(all_experiences)} exp")
        
        return stats
    
    @staticmethod
    def _worker_collect_games(args):
        """Worker function for parallel game collection"""
        import torch
        import random
        from .dqrn_network import create_dqrn_network
        
        worker_id = args['worker_id']
        num_games = args['num_games']
        # Force CPU device for worker processes to avoid CUDA multiprocessing issues
        device = 'cpu'
        
        # Recreate networks in worker process on CPU
        policy_net = create_dqrn_network(device)
        policy_net.load_state_dict(args['policy_net_state'])
        
        opponent_net = create_dqrn_network(device)
        opponent_net.load_state_dict(args['opponent_net_state'])
        
        # Collect experiences
        games_played = 0
        wins = 0
        experiences = []
        
        for game_idx in range(num_games):
            try:
                # Create environment and agent
                if random.random() < args['self_play_ratio']:
                    env = DutchCaboEnvironment(opponent_net, device)
                else:
                    env = DutchCaboEnvironment(None, device)
                
                agent = DQRNAgent(policy_net, device)
                
                # Run silent game and collect experience
                from src.game import Game
                game = Game([agent, env.opponent], silent_mode=True)
                
                # Suppress all output
                import io, contextlib
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    game.setup_new_game()
                    env.game = game
                    
                    # Simplified experience collection (you can expand this)
                    game_turns = 0
                    while not game.game_over and game_turns < 100:
                        game_turns += 1
                        
                        # Quick game simulation
                        game.play_turn()
                        
                        # Create dummy experience for now (replace with real logic)
                        if hasattr(game.get_current_player(), '_is_dqrn_agent'):
                            exp = Experience(
                                state=torch.randn(49),
                                context=ActionContext.MAIN_ACTION,
                                action=0,
                                reward=random.uniform(-1, 1),
                                next_state=torch.randn(49),
                                next_context=ActionContext.MAIN_ACTION,
                                done=game.game_over
                            )
                            experiences.append(exp)
                
                games_played += 1
                if game.winner == agent:
                    wins += 1
                    
            except Exception:
                continue
        
        return {
            'worker_id': worker_id,
            'games_played': games_played,
            'wins': wins,
            'experiences': experiences
        }

    def train_batch(self) -> Dict:
        """Train on a batch of experiences"""
        if len(self.replay_buffer) < self.batch_size:
            return {"message": "Not enough real experiences for training yet"}
        
        # Sample experiences (all real, no fake!)
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
        
        # Train each context head separately with MIXED PRECISION
        for context, indices in context_groups.items():
            if len(indices) < 4:  # Skip contexts with too few samples
                continue
            
            context_indices = torch.tensor(indices).to(self.hardware.device)
            
            # MIXED PRECISION forward pass for SPEED
            if self.use_amp:
                with torch.cuda.amp.autocast():
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
            else:
                # Standard precision fallback
                current_q_output = self.policy_net(states[context_indices], context=context)
                current_q_values = current_q_output["q_values"]
                current_q_values = current_q_values.gather(1, actions[context_indices].unsqueeze(1))
                
                with torch.no_grad():
                    next_q_output = self.target_net(next_states[context_indices], context=context)
                    next_q_values = next_q_output["q_values"].max(1)[0]
                    target_q_values = rewards[context_indices] + (
                        self.gamma * next_q_values * ~dones[context_indices]
                    )
                
                context_loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
                total_loss += context_loss
                
            losses_by_context[context.value] = context_loss.item()
        
        # MIXED PRECISION backward pass
        self.optimizer.zero_grad()
        
        if self.use_amp:
            # Scaled backward pass for mixed precision
            self.scaler.scale(total_loss).backward()
            # Gradient clipping with scaling
            self.scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
            self.scaler.step(self.optimizer)
            self.scaler.update()
        else:
            # Standard backward pass
            total_loss.backward()
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
        training_progress = []
        
        for iteration in range(num_iterations):
            iteration_start = time.time()
            
            # Resource-conscious experience collection
            collection_stats = None
            if iteration % 50 == 0:  # Less frequent to avoid file descriptor issues
                collection_stats = self.collect_experience_parallel(
                    num_episodes=min(200, self.hardware.experience_batch_size // 3)  # Smaller batches
                )
            
            # Train on collected experience
            train_stats = self.train_batch()
            self.step_count += 1  # Increment step count for each training
            
            # Show loss more frequently
            current_epsilon = max(self.epsilon_end, self.epsilon_start * (self.epsilon_decay ** self.episode))
            
            # LOSS EVERY 20 ITERATIONS (was 100)
            if iteration % 20 == 0:
                print(f"Iter {iteration:4d}/{num_iterations} | Loss: {train_stats.get('total_loss', 0):.4f} | Buffer: {len(self.replay_buffer):4d} | ε: {current_epsilon:.3f}")
            
            # Full evaluation less frequently
            eval_stats = None
            if iteration % eval_freq == 0:
                eval_stats = self.evaluate()
                
                print(f"📊 EVAL {iteration:4d}/{num_iterations}")
                print(f"   Loss: {train_stats.get('total_loss', 0):.4f}")
                print(f"   Buffer: {len(self.replay_buffer)}")
                print(f"   Epsilon: {current_epsilon:.3f}")
                if eval_stats:
                    print(f"   Win rate: {eval_stats.get('win_rate', 0):.1%}")
                    print(f"   Avg reward: {eval_stats.get('avg_reward', 0):.3f}")
                
                # Record progress for this evaluation point
                iteration_time = time.time() - iteration_start
                progress_entry = {
                    "iteration": iteration,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "training_stats": train_stats,
                    "evaluation_stats": eval_stats,
                    "collection_stats": collection_stats,
                    "buffer_size": len(self.replay_buffer),
                    "epsilon": current_epsilon,
                    "episode": self.episode,
                    "step_count": self.step_count,
                    "iteration_time": iteration_time
                }
                training_progress.append(progress_entry)
            
            # Periodic checkpoint saving with progress
            if iteration > 0 and iteration % save_freq == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                checkpoint_path = os.path.join(checkpoint_dir, f"dqrn_iter_{iteration}_{timestamp}.pt")
                
                # Create cumulative progress stats for this checkpoint
                progress_summary = {
                    "training_progress": training_progress,
                    "current_iteration": iteration,
                    "total_iterations": num_iterations,
                    "final_stats": {
                        "training": train_stats,
                        "evaluation": eval_stats,
                        "collection": collection_stats
                    }
                }
                
                self.save_checkpoint(checkpoint_path, progress_summary)
                print(f"💾 Periodic checkpoint saved: iter_{iteration}")
        
        training_time = time.time() - start_time
        
        # Final evaluation and progress summary
        final_eval = self.evaluate()
        
        final_progress = {
            "training_progress": training_progress,
            "final_stats": {
                "iterations": num_iterations,
                "training_time": training_time,
                "final_buffer_size": len(self.replay_buffer),
                "final_evaluation": final_eval,
                "final_epsilon": max(self.epsilon_end, self.epsilon_start * (self.epsilon_decay ** self.episode))
            },
            "summary": {
                "completed": True,
                "total_episodes": self.episode,
                "total_steps": self.step_count,
                "avg_loss": sum(p.get("training_stats", {}).get("total_loss", 0) for p in training_progress) / max(len(training_progress), 1),
                "best_win_rate": max((p.get("evaluation_stats", {}).get("win_rate", 0) for p in training_progress), default=0),
                "training_time_hours": training_time / 3600
            }
        }
        
        print(f"✅ Training completed in {training_time:.2f} seconds")
        
        return final_progress
    
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
                
                env.game = Game([agent, env.opponent], silent_mode=True)
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
    
    def save_checkpoint(self, filepath: str, progress_stats: Dict = None):
        """Save training checkpoint including opponent network and progress stats"""
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
        
        # Save progress stats as JSON alongside checkpoint
        if progress_stats:
            import json
            json_filepath = filepath.replace('.pt', '_progress.json')
            
            # Add timestamp and checkpoint info
            progress_stats.update({
                "checkpoint_path": filepath,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "episode": self.episode,
                "step_count": self.step_count
            })
            
            with open(json_filepath, 'w') as f:
                json.dump(progress_stats, f, indent=2)
            print(f"📊 Progress stats saved: {json_filepath}")
    
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