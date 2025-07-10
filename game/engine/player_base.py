from typing import List, Optional, Tuple
from abc import ABC, abstractmethod

from .card import Card


class PlayerBase(ABC):
    """Abstract base class for all players - pure game logic without UI"""
    
    def __init__(self, name: str):
        """
        Initialize a player.
        
        Args:
            name: The player's name/identifier
        """
        self.name = name
        self.hand: List[Optional[Card]] = [None] * 4  # 4 face-down cards
        self.known_cards: List[bool] = [False] * 4     # Track which cards the player knows
        self.initial_peek_used = False
        
    def reset_for_new_game(self):
        """Reset player state for a new game"""
        self.hand = [None] * 4
        self.known_cards = [False] * 4
        self.initial_peek_used = False
    
    def receive_card(self, card: Card, position: int):
        """
        Place a card in the player's hand at the specified position.
        
        Args:
            card: The card to place
            position: Position in hand (0-3)
        """
        if not 0 <= position <= 3:
            raise ValueError("Position must be between 0 and 3")
        self.hand[position] = card
    
    def peek_at_own_card(self, position: int) -> Card:
        """
        Peek at one of the player's own cards.
        
        Args:
            position: Position to peek at (0-3)
            
        Returns:
            The card at that position
        """
        if not 0 <= position <= 3:
            raise ValueError("Position must be between 0 and 3")
        card = self.hand[position]
        if card is None:
            raise ValueError("No card at that position")
        
        self.known_cards[position] = True
        return card
    
    def swap_card(self, position: int, new_card: Card) -> Card:
        """
        Swap a card in the player's hand with a new card.
        
        Args:
            position: Position to swap (0-3)
            new_card: The new card to place
            
        Returns:
            The old card that was replaced
        """
        if not 0 <= position <= 3:
            raise ValueError("Position must be between 0 and 3")
        old_card = self.hand[position]
        if old_card is None:
            raise ValueError("No card at that position")
            
        self.hand[position] = new_card
        self.known_cards[position] = True  # Player now knows this card
        return old_card
    
    def get_score(self) -> int:
        """Calculate the player's current score (sum of card values)"""
        score = 0
        for card in self.hand:
            if card is not None:
                score += card.get_score_value()
        return score
    
    def get_hand_size(self) -> int:
        """Get the current number of cards in hand"""
        return sum(1 for card in self.hand if card is not None)
    
    def is_hand_empty(self) -> bool:
        """Check if the player has no cards left"""
        return self.get_hand_size() == 0
    
    def get_valid_positions(self) -> List[int]:
        """Get list of positions that have cards"""
        return [i for i in range(4) if self.hand[i] is not None]
    
    def get_discard_pile_matches(self, top_discard_card: Card) -> List[Tuple[int, Card]]:
        """
        Get known cards that match the top discard card.
        
        Args:
            top_discard_card: The card on top of discard pile
            
        Returns:
            List of (position, card) tuples for matching cards
        """
        matches = []
        if top_discard_card is None:
            return matches
            
        for i in range(4):
            card = self.hand[i]
            if (card is not None and 
                self.known_cards[i] and 
                card.value == top_discard_card.value):
                matches.append((i, card))
        return matches
    
    def display_hand(self, reveal_all: bool = False) -> str:
        """
        Display the player's hand.
        
        Args:
            reveal_all: If True, show all cards. If False, only show known cards.
            
        Returns:
            String representation of the hand
        """
        hand_str = []
        for i, card in enumerate(self.hand):
            if card is None:
                hand_str.append("[ ]")
            elif reveal_all or self.known_cards[i]:
                hand_str.append(f"[{card}]")
            else:
                hand_str.append("[?]")
        return " ".join(hand_str)
    
    # Abstract methods that subclasses must implement
    @abstractmethod
    def choose_initial_peek(self) -> int:
        """Choose which card to peek at initially (0-3)"""
        pass
    
    @abstractmethod
    def choose_action(self, drawn_card: Card, game_state: dict) -> dict:
        """
        Choose what action to take with a drawn card.
        
        Args:
            drawn_card: The card that was drawn
            game_state: Current game state information
            
        Returns:
            Dictionary describing the chosen action
        """
        pass
    
    @abstractmethod
    def choose_swap_target(self, opponents: List['PlayerBase'], game_state: dict) -> Tuple['PlayerBase', int]:
        """
        Choose which opponent and position to swap with (when using Jack).
        
        Args:
            opponents: List of other players
            game_state: Current game state information
            
        Returns:
            Tuple of (target_player, target_position)
        """
        pass
    
    @abstractmethod
    def choose_peek_target(self, opponents: List['PlayerBase'], game_state: dict) -> Tuple[Optional['PlayerBase'], int]:
        """
        Choose which card to peek at (when using Queen).
        
        Args:
            opponents: List of other players
            game_state: Current game state information
            
        Returns:
            Tuple of (target_player, target_position). If target_player is None, peek at own card.
        """
        pass
    
    def choose_draw_source(self, top_discard_card: Card, game_state: dict) -> str:
        """
        Choose whether to draw from deck or discard pile.
        
        Args:
            top_discard_card: The card on top of discard pile
            game_state: Current game state information
            
        Returns:
            "deck" or "discard"
        """
        # Default implementation: always draw from deck
        return "deck"
    
    def want_to_discard_pile_matches(self, matches_available: List[Tuple[int, Card]], 
                                   top_discard_card: Card, timing: str, game_state: dict) -> Optional[List[int]]:
        """
        Choose whether to discard cards that match the top discard card.
        
        Args:
            matches_available: List of (position, card) tuples for matching cards
            top_discard_card: The card on top of discard pile
            timing: "before_draw" or "after_turn"
            game_state: Current game state
            
        Returns:
            List of positions to discard, None otherwise
        """
        # Default implementation: never discard matches
        return None 