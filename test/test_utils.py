"""
Test utilities for Dutch Cabo game tests
"""

from typing import List, Optional, Tuple
from game.engine.card import Card, Suit
from game.engine.player_base import PlayerBase


class MockPlayer(PlayerBase):
    """Mock player for testing purposes"""
    
    def __init__(self, name: str, initial_peek_pos: int = 0):
        super().__init__(name)
        self.initial_peek_pos = initial_peek_pos
        self.action_responses = []  # Queue of actions to take
        self.peek_responses = []    # Queue of peek choices
        self.swap_responses = []    # Queue of swap choices
        self.draw_responses = []    # Queue of draw choices
        
    def choose_initial_peek(self) -> int:
        return self.initial_peek_pos
        
    def choose_action(self, drawn_card: Card, game_state: dict) -> dict:
        if self.action_responses:
            return self.action_responses.pop(0)
        return {"action": "discard"}  # Default
        
    def choose_swap_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[PlayerBase, int]:
        if self.swap_responses:
            target_name, position = self.swap_responses.pop(0)
            target_player = next(p for p in opponents if p.name == target_name)
            return target_player, position
        return opponents[0], 0  # Default
        
    def choose_own_swap_position(self, game_state: dict) -> int:
        valid_positions = self.get_valid_positions()
        return valid_positions[0] if valid_positions else 0
        
    def calculate_score(self) -> int:
        """Calculate score for testing - same as get_score"""
        return self.get_score()
        
    def choose_peek_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[Optional[PlayerBase], int]:
        if self.peek_responses:
            target_name, position = self.peek_responses.pop(0)
            if target_name is None:
                return None, position
            target_player = next(p for p in opponents if p.name == target_name)
            return target_player, position
        return None, 0  # Default: peek at own card
        
    def choose_draw_source(self, top_discard_card: Card, game_state: dict) -> str:
        if self.draw_responses:
            return self.draw_responses.pop(0)
        return "deck"  # Default
        
    def want_to_discard_pile_matches(self, matches_available: List[Tuple[int, Card]], 
                                   top_discard_card: Card, timing: str, game_state: dict) -> Optional[List[int]]:
        # For testing: always discard first match if available
        if matches_available:
            return [matches_available[0][0]]
        return None


def create_test_deck() -> List[Card]:
    """Create a specific deck for testing"""
    return [
        # First 8 cards (will be dealt to 2 players)
        Card(Suit.HEARTS, 7),    # Player 1, pos 0
        Card(Suit.SPADES, 10),   # Player 1, pos 1
        Card(Suit.CLUBS, 1),     # Player 1, pos 2  (Ace)
        Card(Suit.DIAMONDS, 13), # Player 1, pos 3  (Red King = 0)
        
        Card(Suit.HEARTS, 11),   # Player 2, pos 0  (Jack)
        Card(Suit.SPADES, 5),    # Player 2, pos 1
        Card(Suit.CLUBS, 8),     # Player 2, pos 2
        Card(Suit.DIAMONDS, 2),  # Player 2, pos 3
        
        # Top discard card
        Card(Suit.HEARTS, 9),    # Initial discard
        
        # Next cards to be drawn
        Card(Suit.SPADES, 12),   # Queen
        Card(Suit.CLUBS, 11),    # Jack
        Card(Suit.DIAMONDS, 7),
        Card(Suit.HEARTS, 3),
        Card(Suit.SPADES, 6),
        Card(Suit.CLUBS, 4),
        
        # Fill rest with random cards
        *[Card(suit, value) for suit in Suit for value in range(1, 14) 
          if Card(suit, value) not in [
              Card(Suit.HEARTS, 7), Card(Suit.SPADES, 10), Card(Suit.CLUBS, 1), Card(Suit.DIAMONDS, 13),
              Card(Suit.HEARTS, 11), Card(Suit.SPADES, 5), Card(Suit.CLUBS, 8), Card(Suit.DIAMONDS, 2),
              Card(Suit.HEARTS, 9), Card(Suit.SPADES, 12), Card(Suit.CLUBS, 11), Card(Suit.DIAMONDS, 7),
              Card(Suit.HEARTS, 3), Card(Suit.SPADES, 6), Card(Suit.CLUBS, 4)
          ]]
    ]


def create_simple_test_deck() -> List[Card]:
    """Create a simple test deck with known cards
    
    Cards are dealt from the END of the deck (using pop()), so:
    - Last 9 cards: 8 player cards + 1 discard
    - Earlier cards: draw pile (will be drawn later)
    """
    # Rest of deck first (these will be drawn later)
    deck = [
        *[Card(Suit.HEARTS, i) for i in [1, 6, 10, 13]],
        *[Card(Suit.SPADES, i) for i in [1, 4, 8, 9, 11, 13]],
        *[Card(Suit.CLUBS, i) for i in [1, 2, 3, 4, 5, 6, 8, 10, 11, 13]],
        *[Card(Suit.DIAMONDS, i) for i in [2, 3, 4, 6, 7, 8, 9, 11, 12, 13]]
    ]
    
    # Cards to be drawn (these come before dealing)
    deck.extend([
        Card(Suit.HEARTS, 4),
        Card(Suit.DIAMONDS, 10),
        Card(Suit.CLUBS, 7),     # Matching card
        Card(Suit.SPADES, 12),   # Queen to be drawn
    ])
    
    # Discard pile start (dealt last, so it's at end of deck)
    deck.append(Card(Suit.HEARTS, 8))
    
    # Player hands (8 cards) - dealt in reverse order since we use pop()
    # P2[3] is dealt first (last in deck), P1[0] is dealt last (at end of deck)
    deck.extend([
        Card(Suit.DIAMONDS, 1),  # P2[3] Ace
        Card(Suit.CLUBS, 9),     # P2[2]
        Card(Suit.SPADES, 3),    # P2[1]
        Card(Suit.HEARTS, 11),   # P2[0] Jack
        
        Card(Suit.DIAMONDS, 5),  # P1[3]
        Card(Suit.CLUBS, 12),    # P1[2] Queen
        Card(Suit.SPADES, 7),    # P1[1] 
        Card(Suit.HEARTS, 2),    # P1[0]
    ])
    
    return deck 