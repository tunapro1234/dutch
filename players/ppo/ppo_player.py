"""
PPO Player - A player that uses a trained PPO model to play Dutch Cabo

This class wraps a trained Stable Baselines3 PPO model and provides the 
standard PlayerBase interface for use in games.
"""

import os
import sys
import numpy as np
from typing import List, Tuple, Optional, Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from game.engine.player_base import PlayerBase
from game.engine.card import Card

try:
    from stable_baselines3 import PPO
except ImportError:
    PPO = None
    print("⚠️ Stable Baselines3 not available. PPO models cannot be loaded.")


class PPOPlayer(PlayerBase):
    """
    AI Player using a trained PPO model from Stable Baselines3
    
    This player converts the game state to the same observation format
    used during training and uses the trained neural network to make decisions.
    """
    
    def __init__(self, name: str = "PPO_Agent", model_path: Optional[str] = None):
        """
        Initialize PPO player
        
        Args:
            name: Player name
            model_path: Path to the trained PPO model (.zip file)
        """
        super().__init__(name)
        self.model = None
        self.model_path = model_path
        
        # Action decoding mapping (matches dutch_env.py)
        self.action_map = {
            # 0-3: Draw from deck + swap with position
            0: {"action": "swap", "position": 0, "draw_source": "deck"},
            1: {"action": "swap", "position": 1, "draw_source": "deck"},
            2: {"action": "swap", "position": 2, "draw_source": "deck"},
            3: {"action": "swap", "position": 3, "draw_source": "deck"},
            
            # 4-7: Draw from discard + swap with position
            4: {"action": "swap", "position": 0, "draw_source": "discard"},
            5: {"action": "swap", "position": 1, "draw_source": "discard"},
            6: {"action": "swap", "position": 2, "draw_source": "discard"},
            7: {"action": "swap", "position": 3, "draw_source": "discard"},
            
            # 8: Draw from deck and discard
            8: {"action": "discard", "draw_source": "deck"},
            
            # 9: Use special ability
            9: {"action": "use_ability"},
            
            # 10: Call Dutch
            10: {"action": "call_dutch"},
            
            # 11-14: Discard matching cards
            11: {"action": "discard_matches", "position": 0},
            12: {"action": "discard_matches", "position": 1},
            13: {"action": "discard_matches", "position": 2},
            14: {"action": "discard_matches", "position": 3},
            
            # 15: Skip/fallback
            15: {"action": "discard"}
        }
        
        # Load model if path provided
        if model_path:
            self.load_model(model_path)
    
    def load_model(self, model_path: str) -> bool:
        """
        Load a trained PPO model
        
        Args:
            model_path: Path to the model file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if PPO is None:
            print("❌ Cannot load PPO model: Stable Baselines3 not available")
            return False
        
        try:
            if not os.path.exists(model_path):
                print(f"❌ Model file not found: {model_path}")
                return False
                
            self.model = PPO.load(model_path)
            self.model_path = model_path
            print(f"✅ PPO model loaded from: {model_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load PPO model: {e}")
            return False
    
    def set_live_model(self, live_model):
        """
        🔥 ALPHA ZERO STYLE: Set a live model reference for real-time self-play
        
        This allows the opponent to use the same model that's being trained,
        creating true self-play where the agent trains against its current self.
        
        Args:
            live_model: The PPO model being trained (shared reference)
        """
        self.model = live_model
        self.model_path = "live_model"
        print(f"🎯 {self.name}: Using LIVE MODEL for real-time self-play")
    
    def _get_observation(self, game_state: Dict[str, Any]) -> np.ndarray:
        """
        Convert current game state to model observation format
        This must match exactly the observation format used during training
        
        Args:
            game_state: Current game state information
            
        Returns:
            36-dimensional observation vector
        """
        obs = np.zeros(36, dtype=np.float32)
        idx = 0
        
        # Own hand state (16 values: 4 cards * 4 attributes each)
        for i in range(4):
            if i < len(self.hand) and self.hand[i] is not None:
                card = self.hand[i]
                obs[idx] = card.get_score_value()  # Card value
                obs[idx + 1] = 1.0 if self.known_cards[i] else 0.0  # Is known
                obs[idx + 2] = 1.0  # Position is valid (has card)
                obs[idx + 3] = 1.0 if self.known_cards[i] else 0.0  # Is revealed
            else:
                obs[idx:idx + 4] = [-1.0, 0.0, 0.0, 0.0]  # Empty position
            idx += 4
        
        # Game state (8 values)
        obs[idx] = min(game_state.get("turn_count", 0) / 50.0, 1.0)  # Normalized turn count
        obs[idx + 1] = game_state.get("deck_size", 0) / 52.0  # Normalized deck size
        
        # Top discard card value
        top_discard = game_state.get("top_discard_card")
        if top_discard is not None:
            obs[idx + 2] = top_discard.get_score_value()
        else:
            obs[idx + 2] = -1.0
            
        obs[idx + 3] = 1.0 if game_state.get("dutch_called", False) else 0.0
        obs[idx + 4] = 1.0 if game_state.get("final_round", False) else 0.0
        obs[idx + 5] = len(game_state.get("all_players", [])) / 4.0  # Normalized player count
        
        # Current player indicator
        current_player_name = game_state.get("current_player", "")
        obs[idx + 6] = 1.0 if current_player_name == self.name else 0.0
        
        obs[idx + 7] = self.get_hand_size() / 4.0  # Normalized hand size
        idx += 8
        
        # Opponent info (12 values: 3 opponents * 4 attributes each)
        opponents = game_state.get("opponents", [])
        for i in range(3):  # Max 3 opponents
            if i < len(opponents):
                opponent = opponents[i]
                obs[idx] = opponent.get_hand_size() / 4.0  # Normalized hand size
                obs[idx + 1] = sum(opponent.known_cards) / 4.0  # Proportion of known cards
                obs[idx + 2] = min(opponent.get_score() / 40.0, 1.0)  # Normalized estimated score
                obs[idx + 3] = 1.0 if current_player_name == opponent.name else 0.0  # Is current player
            else:
                obs[idx:idx + 4] = [0.0, 0.0, 0.0, 0.0]  # No opponent
            idx += 4
        
        return obs
    
    def choose_action(self, drawn_card: Card, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Choose action using the trained PPO model
        
        Args:
            drawn_card: The card that was just drawn
            game_state: Current game state
            
        Returns:
            Action dictionary
        """
        if self.model is None:
            # Fallback to simple strategy if no model
            return self._fallback_action(drawn_card, game_state)
        
        try:
            # Get observation in the same format as training
            obs = self._get_observation(game_state)
            
            # Get action from model (deterministic for stable play)
            action, _ = self.model.predict(obs, deterministic=True)
            
            # Convert numpy array to int
            action_int = int(action) if hasattr(action, 'item') else int(action)
            
            # Convert to action dictionary
            if action_int in self.action_map:
                chosen_action = self.action_map[action_int].copy()
                
                # Validate action based on current game state
                validated_action = self._validate_action(chosen_action, drawn_card, game_state)
                
                return validated_action
            else:
                print(f"⚠️ PPO model returned invalid action: {action}")
                return self._fallback_action(drawn_card, game_state)
                
        except Exception as e:
            print(f"⚠️ Error in PPO prediction: {e}")
            return self._fallback_action(drawn_card, game_state)
    
    def _validate_action(self, action: Dict[str, Any], drawn_card: Card, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and potentially modify the action to ensure it's legal
        
        Args:
            action: Action chosen by the model
            drawn_card: The drawn card
            game_state: Current game state
            
        Returns:
            Valid action dictionary
        """
        action_type = action.get("action", "discard")
        
        # Validate swap actions
        if action_type == "swap":
            position = action.get("position", 0)
            # Ensure position is valid
            if position < 0 or position >= len(self.hand) or self.hand[position] is None:
                # Find a valid position or fallback to discard
                valid_positions = [i for i in range(len(self.hand)) if self.hand[i] is not None]
                if valid_positions:
                    action["position"] = valid_positions[0]
                else:
                    return {"action": "discard"}
        
        # Validate discard pile draw
        elif action_type in ["swap", "discard"] and action.get("draw_source") == "discard":
            top_discard = game_state.get("top_discard_card")
            if top_discard is None:
                # Can't draw from empty discard pile
                action["draw_source"] = "deck"
        
        # Validate matching action
        elif action_type == "discard_matches":
            position = action.get("position", 0)
            if position >= len(self.hand) or self.hand[position] is None:
                return {"action": "discard"}
            
            # Check if card actually matches top discard
            top_discard = game_state.get("top_discard_card")
            if top_discard is None or not self.known_cards[position]:
                return {"action": "discard"}
            
            if self.hand[position].value != top_discard.value:
                return {"action": "discard"}
        
        # Validate special ability usage
        elif action_type == "use_ability":
            if drawn_card is None or drawn_card.value not in [11, 12]:  # Jack or Queen
                return {"action": "discard"}
        
        return action
    
    def _fallback_action(self, drawn_card: Card, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple fallback strategy when model is not available
        
        Args:
            drawn_card: The drawn card
            game_state: Current game state
            
        Returns:
            Simple action
        """
        # Simple strategy: always discard unless it's a really good card
        if drawn_card is not None and drawn_card.get_score_value() <= 3:
            # Good card, try to swap with highest position
            for i in range(len(self.hand) - 1, -1, -1):
                if self.hand[i] is not None:
                    return {"action": "swap", "position": i}
        
        return {"action": "discard"}
    
    def choose_initial_peek(self) -> int:
        """Choose initial card to peek at (corners are statistically better)"""
        if self.model is None:
            # Corner positions are generally better
            return 0 if np.random.random() < 0.5 else 3
        
        # Use model for initial peek decision
        # Create dummy observation for initial state
        obs = np.zeros(36, dtype=np.float32)
        
        try:
            action, _ = self.model.predict(obs, deterministic=True)
            # Convert numpy array to int and map to peek position (0-3)
            action_int = int(action) if hasattr(action, 'item') else int(action)
            return action_int % 4
        except:
            return 0
    
    def choose_swap_target(self, opponents: List[PlayerBase], game_state: Dict[str, Any]) -> Tuple[PlayerBase, int]:
        """Choose swap target for Jack ability"""
        # Simple heuristic: target player with most unknown cards in corner positions
        best_target = None
        best_position = 0
        best_score = -1
        
        for opponent in opponents:
            for pos in [0, 3, 1, 2]:  # Prefer corners
                if pos < len(opponent.hand) and opponent.hand[pos] is not None:
                    # Score based on unknown status and position preference
                    score = (2 if not opponent.known_cards[pos] else 1)
                    score += (2 if pos in [0, 3] else 1)  # Corner bonus
                    
                    if score > best_score:
                        best_score = score
                        best_target = opponent
                        best_position = pos
        
        if best_target is None:
            # Fallback
            return opponents[0], 0
        
        return best_target, best_position
    
    def choose_own_swap_position(self, game_state: Dict[str, Any]) -> int:
        """Choose own card position to give away in Jack swap"""
        # Give away the highest known card, prefer corners
        best_position = 0
        best_value = -1
        
        for i in [0, 3, 1, 2]:  # Prefer corners
            if i < len(self.hand) and self.hand[i] is not None and self.known_cards[i]:
                card_value = self.hand[i].get_score_value()
                if card_value > best_value:
                    best_value = card_value
                    best_position = i
        
        return best_position
    
    def choose_peek_target(self, opponents: List[PlayerBase], game_state: Dict[str, Any]) -> Tuple[Optional[PlayerBase], int]:
        """Choose peek target for Queen ability"""
        # Peek at own unknown cards first, prioritizing corners
        for pos in [0, 3, 1, 2]:
            if pos < len(self.hand) and self.hand[pos] is not None and not self.known_cards[pos]:
                return None, pos  # Peek at own card
        
        # If all own cards are known, peek at opponent corners
        for opponent in opponents:
            for pos in [0, 3]:  # Corner positions
                if pos < len(opponent.hand) and opponent.hand[pos] is not None:
                    return opponent, pos
        
        # Fallback
        return None, 0
    
    def should_call_dutch(self, game_state: Dict[str, Any]) -> bool:
        """Decide whether to call Dutch"""
        if self.model is None:
            # Simple heuristic: call if estimated score is very low
            return self.get_score() <= 6
        
        # Use model prediction (action 10 = call Dutch)
        try:
            obs = self._get_observation(game_state)
            action, _ = self.model.predict(obs, deterministic=True)
            action_int = int(action) if hasattr(action, 'item') else int(action)
            return action_int == 10
        except:
            return self.get_score() <= 6
    
    def get_strategy_info(self) -> str:
        """Return information about this player's strategy"""
        if self.model is None:
            return f"{self.name}: PPO model not loaded (fallback strategy)"
        else:
            return f"{self.name}: PPO-trained neural network agent" 