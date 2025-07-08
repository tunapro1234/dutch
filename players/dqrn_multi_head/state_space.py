"""
State Space Definition for Dutch Cabo DQRN Multi-Head Agent

State representation optimized for recurrent neural networks (LSTM/GRU).
Handles partial observability and temporal dependencies.
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum


class CardEncoding(Enum):
    """Card encoding for neural network input"""
    UNKNOWN = 0
    RED_KING = 1    # 0 points
    ACE = 2         # 1 point  
    TWO = 3         # 2 points
    THREE = 4       # 3 points
    FOUR = 5        # 4 points
    FIVE = 6        # 5 points
    SIX = 7         # 6 points
    SEVEN = 8       # 7 points
    EIGHT = 9       # 8 points
    NINE = 10       # 9 points
    BLACK_KING = 11 # 10 points
    JACK = 12       # 10 points + swap ability
    QUEEN = 13      # 10 points + peek ability


class StateSpace:
    """
    State space representation for Dutch Cabo DQRN agent.
    
    State includes:
    - Own hand representation (4 positions)
    - Opponent hand representation (4 positions) 
    - Current drawn card
    - Discard pile top card
    - Game context information
    - Action history for LSTM memory
    """
    
    def __init__(self):
        self.card_vocab_size = len(CardEncoding)
        self.state_size = self._calculate_state_size()
        self._setup_encoding_maps()
    
    def _calculate_state_size(self) -> int:
        """Calculate total state vector size"""
        size = 0
        
        # Own hand: 4 positions × (card_id + known_flag + confidence) = 4 × 3 = 12
        size += 4 * 3
        
        # Opponent hand: 4 positions × (visible_card_id + estimated_value + confidence) = 4 × 3 = 12  
        size += 4 * 3
        
        # Drawn card: card_id + has_ability = 2
        size += 2
        
        # Discard pile: top_card_id + pile_size_normalized = 2
        size += 2
        
        # Game state: turn_number + deck_size + hand_sizes + dutch_called = 5
        size += 5
        
        # Action context: one-hot encoding of current context = 4
        size += 4  # draw_source, main_action, jack_ability, queen_ability
        
        # Recent action history: last 3 actions encoded = 3 × 4 = 12
        size += 3 * 4  # action_type + target + result + value
        
        print(f"Total state size: {size}")
        return size
    
    def _setup_encoding_maps(self):
        """Setup card encoding mappings"""
        # Map card values to encoding
        self.value_to_encoding = {
            0: CardEncoding.RED_KING,
            1: CardEncoding.ACE,
            2: CardEncoding.TWO,
            3: CardEncoding.THREE,
            4: CardEncoding.FOUR,
            5: CardEncoding.FIVE,
            6: CardEncoding.SIX,
            7: CardEncoding.SEVEN,
            8: CardEncoding.EIGHT,
            9: CardEncoding.NINE,
            10: CardEncoding.BLACK_KING,  # Will distinguish Jack/Queen by has_ability flag
        }
        
        # Special cases for Jack/Queen
        self.special_cards = {
            "Jack": CardEncoding.JACK,
            "Queen": CardEncoding.QUEEN
        }
    
    def encode_card(self, card: Optional[Dict], known: bool = True) -> Tuple[float, float]:
        """
        Encode a single card for neural network input.
        
        Args:
            card: Card dictionary or None
            known: Whether this card's value is known to the agent
            
        Returns:
            (card_encoding, confidence)
        """
        if card is None:
            return 0.0, 0.0  # No card
        
        if not known:
            return float(CardEncoding.UNKNOWN.value), 0.5  # Unknown card, medium confidence
        
        # Handle special cards
        if card.get("rank") == "Jack":
            return float(CardEncoding.JACK.value), 1.0
        elif card.get("rank") == "Queen":
            return float(CardEncoding.QUEEN.value), 1.0
        
        # Handle normal cards by score value
        score_value = card.get("score_value", 5)
        if score_value in self.value_to_encoding:
            encoding = self.value_to_encoding[score_value]
            return float(encoding.value), 1.0
        
        # Fallback for unknown card values
        return float(CardEncoding.UNKNOWN.value), 0.3
    
    def encode_own_hand(self, hand: List[Optional[Dict]], known_cards: List[bool]) -> torch.Tensor:
        """
        Encode own hand state.
        
        Args:
            hand: List of 4 cards (or None)
            known_cards: List of 4 booleans indicating if card is known
            
        Returns:
            Tensor of shape (12,) - 4 positions × 3 features each
        """
        features = []
        
        for i in range(4):
            if i < len(hand):
                card = hand[i]
                known = i < len(known_cards) and known_cards[i]
                card_encoding, confidence = self.encode_card(card, known)
                
                features.extend([
                    card_encoding / self.card_vocab_size,  # Normalized card encoding
                    1.0 if known else 0.0,               # Known flag
                    confidence                            # Confidence in this information
                ])
            else:
                features.extend([0.0, 0.0, 0.0])  # Empty position
        
        return torch.tensor(features, dtype=torch.float32)
    
    def encode_opponent_hand(self, hand: List[Optional[Dict]], 
                           estimated_values: List[float],
                           confidences: List[float]) -> torch.Tensor:
        """
        Encode opponent hand state with estimates.
        
        Args:
            hand: List of 4 cards (mostly None, some visible from abilities)
            estimated_values: Estimated score values for each position
            confidences: Confidence in each estimate
            
        Returns:
            Tensor of shape (12,) - 4 positions × 3 features each
        """
        features = []
        
        for i in range(4):
            if i < len(hand) and hand[i] is not None:
                # Visible card (from Queen peek etc.)
                card_encoding, _ = self.encode_card(hand[i], True)
                visible_flag = 1.0
                confidence = 1.0
            else:
                # Hidden card - use estimates
                estimated_value = estimated_values[i] if i < len(estimated_values) else 5.0
                card_encoding = estimated_value / 10.0  # Normalize to [0,1]
                visible_flag = 0.0
                confidence = confidences[i] if i < len(confidences) else 0.3
            
            features.extend([
                card_encoding,
                visible_flag,  # 1 if card is visible, 0 if estimated
                confidence
            ])
        
        return torch.tensor(features, dtype=torch.float32)
    
    def encode_drawn_card(self, drawn_card: Optional[Dict]) -> torch.Tensor:
        """
        Encode currently drawn card.
        
        Returns:
            Tensor of shape (2,) - card_encoding, has_ability
        """
        if drawn_card is None:
            return torch.tensor([0.0, 0.0], dtype=torch.float32)
        
        card_encoding, _ = self.encode_card(drawn_card, True)
        has_ability = 1.0 if drawn_card.get("has_special_ability", False) else 0.0
        
        return torch.tensor([
            card_encoding / self.card_vocab_size,  # Normalized
            has_ability
        ], dtype=torch.float32)
    
    def encode_discard_pile(self, top_card: Optional[Dict], pile_size: int) -> torch.Tensor:
        """
        Encode discard pile state.
        
        Returns:
            Tensor of shape (2,) - top_card_encoding, pile_size_normalized
        """
        if top_card is None:
            card_encoding = 0.0
        else:
            card_encoding, _ = self.encode_card(top_card, True)
            card_encoding = card_encoding / self.card_vocab_size  # Normalize
        
        pile_size_normalized = min(pile_size / 52.0, 1.0)  # Normalize to [0,1]
        
        return torch.tensor([card_encoding, pile_size_normalized], dtype=torch.float32)
    
    def encode_game_state(self, turn_number: int, deck_size: int, 
                         own_hand_size: int, opponent_hand_size: int,
                         dutch_called: bool) -> torch.Tensor:
        """
        Encode general game state information.
        
        Returns:
            Tensor of shape (5,)
        """
        return torch.tensor([
            min(turn_number / 50.0, 1.0),           # Normalized turn number
            min(deck_size / 52.0, 1.0),            # Normalized deck size  
            own_hand_size / 4.0,                   # Normalized hand size
            opponent_hand_size / 4.0,              # Normalized opponent hand size
            1.0 if dutch_called else 0.0           # Dutch called flag
        ], dtype=torch.float32)
    
    def encode_action_context(self, context: str) -> torch.Tensor:
        """
        Encode current action context as one-hot.
        
        Returns:
            Tensor of shape (4,) - one-hot encoding
        """
        context_map = {
            "draw_source": 0,
            "main_action": 1, 
            "jack_ability": 2,
            "queen_ability": 3
        }
        
        one_hot = torch.zeros(4, dtype=torch.float32)
        if context in context_map:
            one_hot[context_map[context]] = 1.0
        
        return one_hot
    
    def encode_action_history(self, recent_actions: List[Dict]) -> torch.Tensor:
        """
        Encode recent action history for LSTM memory.
        
        Args:
            recent_actions: List of recent action dictionaries
            
        Returns:
            Tensor of shape (12,) - 3 actions × 4 features each
        """
        features = []
        
        # Take last 3 actions (pad if fewer)
        actions_to_encode = recent_actions[-3:] if len(recent_actions) >= 3 else recent_actions
        while len(actions_to_encode) < 3:
            actions_to_encode.insert(0, {})  # Pad with empty actions
        
        action_type_map = {
            "draw": 0.2, "discard": 0.4, "swap": 0.6, "ability": 0.8, "dutch": 1.0
        }
        
        for action in actions_to_encode:
            action_type = action_type_map.get(action.get("action", ""), 0.0)
            target = action.get("position", 0) / 4.0  # Normalize position
            result = action.get("success", 0.5)  # Success/failure of action
            value = action.get("value_change", 0.0) / 10.0  # Normalized value change
            
            features.extend([action_type, target, result, value])
        
        return torch.tensor(features, dtype=torch.float32)
    
    def create_state_vector(self, game_state: Dict) -> torch.Tensor:
        """
        Create complete state vector from game state dictionary.
        
        Args:
            game_state: Complete game state information
            
        Returns:
            Tensor of shape (state_size,) ready for DQRN input
        """
        # Extract components from game state
        own_hand = game_state.get("own_hand", [None] * 4)
        known_cards = game_state.get("known_cards", [False] * 4)
        opponent_hand = game_state.get("opponent_hand", [None] * 4)
        estimated_values = game_state.get("opponent_estimates", [5.0] * 4)
        estimate_confidences = game_state.get("estimate_confidences", [0.3] * 4)
        drawn_card = game_state.get("drawn_card")
        top_discard = game_state.get("top_discard")
        pile_size = game_state.get("discard_pile_size", 0)
        turn_number = game_state.get("turn_number", 0)
        deck_size = game_state.get("deck_size", 52)
        own_hand_size = game_state.get("own_hand_size", 4)
        opponent_hand_size = game_state.get("opponent_hand_size", 4)
        dutch_called = game_state.get("dutch_called", False)
        context = game_state.get("action_context", "main_action")
        recent_actions = game_state.get("recent_actions", [])
        
        # Encode each component
        own_hand_features = self.encode_own_hand(own_hand, known_cards)
        opponent_features = self.encode_opponent_hand(opponent_hand, estimated_values, estimate_confidences)
        drawn_card_features = self.encode_drawn_card(drawn_card)
        discard_features = self.encode_discard_pile(top_discard, pile_size)
        game_features = self.encode_game_state(turn_number, deck_size, own_hand_size, 
                                              opponent_hand_size, dutch_called)
        context_features = self.encode_action_context(context)
        history_features = self.encode_action_history(recent_actions)
        
        # Concatenate all features
        state_vector = torch.cat([
            own_hand_features,      # 12
            opponent_features,      # 12  
            drawn_card_features,    # 2
            discard_features,       # 2
            game_features,          # 5
            context_features,       # 4
            history_features        # 12
        ], dim=0)
        
        assert state_vector.shape[0] == self.state_size, f"State size mismatch: {state_vector.shape[0]} != {self.state_size}"
        
        return state_vector
    
    def get_state_size(self) -> int:
        """Get total state vector size"""
        return self.state_size


# Singleton instance
state_space = StateSpace() 