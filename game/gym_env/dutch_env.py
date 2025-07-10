"""
Gymnasium Environment for Dutch Cabo Card Game

Provides standard RL interface compatible with stable-baselines3 and other RL frameworks
"""

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from typing import Dict, Tuple, Any, Optional, List
import random

from ..engine.game_engine import GameEngine
from ..engine.player_base import PlayerBase
from ..engine.card import Card


class DutchCaboGymPlayer(PlayerBase):
    """
    Special player class for Gym environment that receives actions from RL agent
    """
    
    def __init__(self, name: str = "GymAgent"):
        super().__init__(name)
        self.pending_action: Optional[Dict[str, Any]] = None
        self.last_drawn_card: Optional[Card] = None
        
    def set_action(self, action: Dict[str, Any]):
        """Set action from RL agent"""
        self.pending_action = action
        
    def choose_initial_peek(self) -> int:
        """Choose initial peek position"""
        if self.pending_action and "initial_peek" in self.pending_action:
            return self.pending_action["initial_peek"]
        return random.randint(0, 3)
    
    def choose_action(self, drawn_card: Card, game_state: dict) -> dict:
        """Return action from RL agent"""
        self.last_drawn_card = drawn_card
        if self.pending_action:
            action = self.pending_action
            self.pending_action = None
            return action
        
        # Fallback action if no action set
        return {"action": "discard"}
    
    def choose_swap_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[PlayerBase, int]:
        """Choose swap target for Jack ability"""
        if self.pending_action and "swap_target" in self.pending_action:
            target_idx = self.pending_action["swap_target"]
            position = self.pending_action.get("swap_position", 0)
            if 0 <= target_idx < len(opponents):
                return opponents[target_idx], position
        
        # Fallback to random
        target_opponent = random.choice(opponents)
        valid_positions = target_opponent.get_valid_positions()
        target_position = random.choice(valid_positions)
        return target_opponent, target_position
    
    def choose_peek_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[Optional[PlayerBase], int]:
        """Choose peek target for Queen ability"""
        if self.pending_action and "peek_target" in self.pending_action:
            target_idx = self.pending_action["peek_target"]
            position = self.pending_action.get("peek_position", 0)
            
            if target_idx == -1:  # Peek at own card
                return None, position
            elif 0 <= target_idx < len(opponents):
                return opponents[target_idx], position
        
        # Fallback to own card
        unknown_positions = [i for i in range(4) if self.hand[i] is not None and not self.known_cards[i]]
        if unknown_positions:
            return None, random.choice(unknown_positions)
        return None, 0


class DutchCaboEnv(gym.Env):
    """
    Dutch Cabo Gymnasium Environment
    
    Observation Space:
        - Own hand state (16 values): 4 cards * (value + is_known + position_valid + is_revealed)
        - Game state (8 values): turn_count, deck_size, discard_top_value, dutch_called, final_round, player_count, current_player_idx, hand_size
        - Opponent info (12 values): 3 opponents * (hand_size + known_cards + estimated_score + is_current_player)
        Total: 36 dimensional observation space
    
    Action Space:
        Discrete(N) where actions are encoded as integers:
        - 0-3: Draw from deck + swap with position 0-3
        - 4-7: Draw from discard + swap with position 0-3  
        - 8: Draw from deck + discard
        - 9: Draw from discard + discard (if allowed)
        - 10: Draw + use special ability
        - 11: Call Dutch
        - 12-15: Discard matching cards from positions 0-3
        - 16: Do nothing / skip
    """
    
    metadata = {"render_modes": ["human", "none", "gui"], "render_fps": 1}
    
    def __init__(self, 
                 opponent_players: Optional[List[PlayerBase]] = None,
                 max_episodes: int = 1000,
                 render_mode: Optional[str] = None,
                 reward_shaping: bool = True):
        """
        Initialize Dutch Cabo environment
        
        Args:
            opponent_players: List of opponent AI players (default: SimpleAI players)
            max_episodes: Maximum number of episodes per reset
            render_mode: Rendering mode ('human' or 'none')
            reward_shaping: Whether to use reward shaping for better training
        """
        super().__init__()
        
        self.render_mode = render_mode
        self.reward_shaping = reward_shaping
        self.max_episodes = max_episodes
        self.episode_count = 0
        
        # GUI support
        self.gui = None
        if render_mode == "gui":
            try:
                from ..gui.simple_gui import SimpleGameGUI
                self.gui = SimpleGameGUI("Dutch Cabo - RL Training")
                self._setup_gui()
            except ImportError:
                print("Warning: GUI not available, falling back to human mode")
                self.render_mode = "human"
        
        # Create default opponents if none provided
        if opponent_players is None:
            try:
                # Try relative import first (when imported as package)
                from ...players.simple_ai import SimpleAI
            except ImportError:
                # Fall back to absolute import (when run as script)
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from players.simple_ai import SimpleAI
            
            opponent_players = [
                SimpleAI("Opponent1"),
                SimpleAI("Opponent2"), 
                SimpleAI("Opponent3")
            ]
        
        self.opponent_players = opponent_players
        self.gym_player = DutchCaboGymPlayer("GymAgent")
        
        # Create all players list
        self.all_players = [self.gym_player] + self.opponent_players
        
        # Initialize game engine
        self.engine = GameEngine(self.all_players)
        
        # Define observation space (36 dimensional)
        self.observation_space = spaces.Box(
            low=-1.0, 
            high=20.0,  # Max possible values
            shape=(36,),
            dtype=np.float32
        )
        
        # Define action space (17 possible actions)
        self.action_space = spaces.Discrete(17)
        
        # Tracking variables
        self.current_step = 0
        self.max_steps_per_episode = 100  # Prevent infinite games
        self.last_score = 0
        self.initial_score_estimate = 0
        
    def _get_observation(self) -> np.ndarray:
        """
        Get current observation state
        
        Returns:
            36-dimensional observation vector
        """
        obs = np.zeros(36, dtype=np.float32)
        idx = 0
        
        # Own hand state (16 values: 4 cards * 4 attributes each)
        for i in range(4):
            if i < len(self.gym_player.hand) and self.gym_player.hand[i] is not None:
                card = self.gym_player.hand[i]
                obs[idx] = card.get_score_value()  # Card value
                obs[idx + 1] = 1.0 if self.gym_player.known_cards[i] else 0.0  # Is known
                obs[idx + 2] = 1.0  # Position is valid (has card)
                obs[idx + 3] = 1.0 if self.gym_player.known_cards[i] else 0.0  # Is revealed (same as known)
            else:
                obs[idx:idx + 4] = [-1.0, 0.0, 0.0, 0.0]  # Empty position
            idx += 4
        
        # Game state (8 values)
        game_state = self.engine.get_game_state()
        obs[idx] = min(game_state.get("turn_count", 0) / 50.0, 1.0)  # Normalized turn count
        obs[idx + 1] = game_state.get("deck_size", 0) / 52.0  # Normalized deck size
        
        # Top discard card value
        if self.engine.discard_pile:
            obs[idx + 2] = self.engine.discard_pile[-1].get_score_value()
        else:
            obs[idx + 2] = -1.0
            
        obs[idx + 3] = 1.0 if game_state.get("dutch_called", False) else 0.0
        obs[idx + 4] = 1.0 if game_state.get("final_round", False) else 0.0
        obs[idx + 5] = len(self.all_players) / 4.0  # Normalized player count
        
        # Current player indicator
        current_player_name = game_state.get("current_player", "")
        obs[idx + 6] = 1.0 if current_player_name == self.gym_player.name else 0.0
        
        obs[idx + 7] = self.gym_player.get_hand_size() / 4.0  # Normalized hand size
        idx += 8
        
        # Opponent info (12 values: 3 opponents * 4 attributes each)
        for i, opponent in enumerate(self.opponent_players[:3]):  # Max 3 opponents
            if i < len(self.opponent_players):
                obs[idx] = opponent.get_hand_size() / 4.0  # Normalized hand size
                obs[idx + 1] = sum(opponent.known_cards) / 4.0  # Proportion of known cards
                obs[idx + 2] = min(opponent.get_score() / 40.0, 1.0)  # Normalized estimated score
                obs[idx + 3] = 1.0 if current_player_name == opponent.name else 0.0  # Is current player
            else:
                obs[idx:idx + 4] = [0.0, 0.0, 0.0, 0.0]  # No opponent
            idx += 4
        
        return obs
    
    def _decode_action(self, action: int) -> Dict[str, Any]:
        """
        Decode integer action to game action dictionary
        
        Args:
            action: Integer action from 0-16
            
        Returns:
            Game action dictionary
        """
        if 0 <= action <= 3:
            # Draw from deck + swap with position
            return {
                "action": "swap",
                "position": action,
                "draw_source": "deck"
            }
        elif 4 <= action <= 7:
            # Draw from discard + swap with position
            return {
                "action": "swap", 
                "position": action - 4,
                "draw_source": "discard"
            }
        elif action == 8:
            # Draw from deck + discard
            return {"action": "discard", "draw_source": "deck"}
        elif action == 9:
            # Draw from discard + discard
            return {"action": "discard", "draw_source": "discard"}
        elif action == 10:
            # Use special ability
            return {"action": "use_ability"}
        elif action == 11:
            # Call Dutch
            return {"action": "call_dutch"}
        elif 12 <= action <= 15:
            # Discard matching cards
            return {
                "action": "discard_matches",
                "position": action - 12
            }
        else:  # action == 16
            # Skip/do nothing (fallback to discard)
            return {"action": "discard"}
    
    def _calculate_reward(self, game_ended: bool, winner_name: Optional[str]) -> float:
        """
        Calculate reward for current step
        
        Args:
            game_ended: Whether the game has ended
            winner_name: Name of the winner (if game ended)
            
        Returns:
            Reward value
        """
        reward = 0.0
        current_score = self.gym_player.get_score()
        
        if game_ended:
            if winner_name == self.gym_player.name:
                # Won the game!
                reward += 100.0
                # Bonus for low score wins
                reward += max(0, 20 - current_score)
            else:
                # Lost the game
                reward -= 50.0
                # Penalty proportional to score difference
                if winner_name:
                    for player in self.all_players:
                        if player.name == winner_name:
                            winner_score = player.get_score()
                            score_diff = current_score - winner_score
                            reward -= score_diff * 2.0  # Penalty for losing by large margin
                            break
        
        # Reward shaping during game
        if self.reward_shaping and not game_ended:
            # Small reward for learning about cards
            known_cards = sum(self.gym_player.known_cards)
            reward += known_cards * 0.5
            
            # Small penalty for high score
            reward -= current_score * 0.1
            
            # Reward for improvement
            if current_score < self.last_score:
                reward += (self.last_score - current_score) * 2.0
        
        self.last_score = current_score
        return reward
    
    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, dict]:
        """
        Reset environment to initial state
        
        Args:
            seed: Random seed for reproducibility
            options: Additional options
            
        Returns:
            Tuple of (observation, info)
        """
        super().reset(seed=seed)
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Reset game engine
        self.engine = GameEngine(self.all_players)
        
        # Reset players
        for player in self.all_players:
            player.reset_for_new_game()
        
        # Setup new game
        setup_results = self.engine.setup_new_game()
        
        # Reset tracking variables
        self.current_step = 0
        self.last_score = self.gym_player.get_score()
        self.initial_score_estimate = self.last_score
        self.episode_count += 1
        
        observation = self._get_observation()
        
        info = {
            "episode": self.episode_count,
            "setup_results": setup_results,
            "current_player": self.engine.get_current_player().name
        }
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        """
        Execute one step in the environment
        
        Args:
            action: Integer action to execute
            
        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        self.current_step += 1
        
        # Check if it's gym player's turn
        current_player = self.engine.get_current_player()
        
        if current_player == self.gym_player:
            # Decode and set action for gym player
            game_action = self._decode_action(action)
            self.gym_player.set_action(game_action)
        
        # Execute game turn
        turn_result = self.engine.play_turn()
        
        # Check if game ended
        game_ended = turn_result.get("game_ended", False)
        winner_name = turn_result.get("winner", None)
        
        # Check for truncation (max steps reached)
        truncated = self.current_step >= self.max_steps_per_episode
        
        # Calculate reward
        reward = self._calculate_reward(game_ended, winner_name)
        
        # Get new observation
        observation = self._get_observation()
        
        # Prepare info
        info = {
            "turn_result": turn_result,
            "current_player": self.engine.get_current_player().name if not game_ended else None,
            "game_ended": game_ended,
            "winner": winner_name,
            "gym_player_score": self.gym_player.get_score(),
            "step": self.current_step
        }
        
        if game_ended:
            # Add final game statistics
            final_results = self.engine.get_final_results()
            info["final_results"] = final_results
        
        return observation, reward, game_ended, truncated, info
    
    def _setup_gui(self):
        """Setup GUI with players"""
        if self.gui is None:
            return
            
        # Add gym player first
        self.gui.add_player(self.gym_player.name, is_gym_player=True)
        
        # Add opponents
        for opponent in self.opponent_players:
            self.gui.add_player(opponent.name, is_gym_player=False)
        
        # Start GUI in background
        import threading
        gui_thread = threading.Thread(target=self.gui.start_gui, daemon=True)
        gui_thread.start()
    
    def _update_gui(self):
        """Update GUI with current game state"""
        if self.gui is None:
            return
            
        try:
            # Update game state
            game_state = self.engine.get_game_state()
            current_player = self.engine.get_current_player()
            
            gui_state = {
                "turn_count": game_state.get("turn_count", 0),
                "current_player": current_player.name if current_player else "",
                "dutch_called": self.engine.dutch_called,
                "deck_size": len(self.engine.deck),
                "top_discard": str(self.engine.discard_pile[-1]) if self.engine.discard_pile else None
            }
            
            self.gui.update_game_state(gui_state)
            
            # Update players
            for player in self.all_players:
                player_data = {
                    "hand": [str(card) if card else None for card in player.hand],
                    "known_cards": player.known_cards,
                    "score": player.get_score(),
                    "hand_size": player.get_hand_size()
                }
                self.gui.update_player(player.name, player_data)
                
        except Exception as e:
            print(f"GUI update error: {e}")
    
    def render(self):
        """Render the environment"""
        if self.render_mode == "human":
            print(f"\n=== Dutch Cabo Game State (Step {self.current_step}) ===")
            print(f"Current Player: {self.engine.get_current_player().name}")
            print(f"Dutch Called: {self.engine.dutch_called}")
            print(f"Final Round: {self.engine.final_round}")
            
            # Show gym player's hand
            print(f"\nGym Player ({self.gym_player.name}) Hand:")
            hand_display = self.gym_player.display_hand()
            print(hand_display)
            print(f"Score: {self.gym_player.get_score()}")
            
            # Show opponents
            for opponent in self.opponent_players:
                print(f"{opponent.name}: {opponent.get_hand_size()} cards, Score: {opponent.get_score()}")
            
            # Show discard pile
            if self.engine.discard_pile:
                print(f"Discard Pile Top: {self.engine.discard_pile[-1]}")
            
            print("=" * 50)
            
        elif self.render_mode == "gui":
            self._update_gui()
    
    def close(self):
        """Clean up environment"""
        if self.gui is not None:
            try:
                self.gui.close()
            except:
                pass


# Register environment with Gymnasium
gym.register(
    id='DutchCabo-v0',
    entry_point='game.gym_env:DutchCaboEnv',
    max_episode_steps=100,
    kwargs={'reward_shaping': True}
) 