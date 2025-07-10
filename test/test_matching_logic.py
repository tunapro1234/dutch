"""
Tests for discard pile matching logic - verifying only known cards are offered for matching
"""

import unittest
from game.engine.game_engine import GameEngine
from game.engine.card import Card, Suit
from test.test_utils import MockPlayer, create_simple_test_deck


class TestMatchingLogic(unittest.TestCase):
    """Test discard pile matching logic extensively"""
    
    def test_only_known_cards_offered_for_matching(self):
        """Test that only known cards can match discard pile"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Verify initial state - Player1 knows position 0 has 2♥
        assert player1.hand[0] == Card(Suit.HEARTS, 2)  # Known via initial peek
        assert player1.known_cards[0] == True
        assert player1.known_cards[1] == False  # Position 1 should be unknown
        assert player1.known_cards[2] == False  # Position 2 should be unknown
        assert player1.known_cards[3] == False  # Position 3 should be unknown
        
        # Test matching against 2♣ (different suit, same value)
        discard_2_clubs = Card(Suit.CLUBS, 2)
        matches = player1.get_discard_pile_matches(discard_2_clubs)
        
        # Should only find the known 2♥ at position 0
        assert len(matches) == 1
        assert matches[0][0] == 0  # Position 0
        assert matches[0][1] == Card(Suit.HEARTS, 2)  # Hearts 2
        
        # Test that unknown cards don't match even if they have same value
        # Player1 doesn't know what's at other positions, so no other matches
        positions = [match[0] for match in matches]
        assert len(positions) == 1  # Only position 0 should match
        
    def test_learning_cards_enables_matching(self):
        """Test that learning about cards enables them for matching"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = [
            Card(Suit.HEARTS, 5),    # P1[0] - known via initial peek
            Card(Suit.SPADES, 5),    # P1[1] - unknown initially
            Card(Suit.CLUBS, 9),     # P1[2] - unknown
            Card(Suit.DIAMONDS, 2),  # P1[3] - unknown
            
            Card(Suit.HEARTS, 12),   # P2[0] - Queen
            Card(Suit.SPADES, 3),    # P2[1] - known via initial peek
            Card(Suit.CLUBS, 8),     # P2[2]
            Card(Suit.DIAMONDS, 1),  # P2[3]
            
            Card(Suit.HEARTS, 4),    # Initial discard
            
            # Rest of deck
            *[Card(Suit.HEARTS, i) for i in [1, 6, 7, 8, 10, 11, 13]],
            *[Card(Suit.SPADES, i) for i in [1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13]],
            *[Card(Suit.CLUBS, i) for i in [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13]],
            *[Card(Suit.DIAMONDS, i) for i in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]]
        ]
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Initially, only position 0 is known
        discard_5_diamonds = Card(Suit.DIAMONDS, 5)
        matches = player1.get_discard_pile_matches(discard_5_diamonds)
        assert len(matches) == 1  # Only position 0 (Hearts 5)
        assert matches[0][0] == 0
        
        # Now learn about position 1 by peeking
        peeked_card = player1.peek_at_own_card(1)
        assert peeked_card == Card(Suit.SPADES, 5)
        assert player1.known_cards[1] == True
        
        # Now check matches again - should find both 5s
        matches = player1.get_discard_pile_matches(discard_5_diamonds)
        assert len(matches) == 2  # Both positions 0 and 1
        
        positions = [match[0] for match in matches]
        assert 0 in positions  # Hearts 5
        assert 1 in positions  # Spades 5
        
    def test_no_matches_when_no_known_cards(self):
        """Test no matches are offered when no matching known cards"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = [
            Card(Suit.HEARTS, 2),    # P1[0] - known via initial peek
            Card(Suit.SPADES, 7),    # P1[1] - unknown, different value
            Card(Suit.CLUBS, 9),     # P1[2] - unknown, different value
            Card(Suit.DIAMONDS, 10), # P1[3] - unknown, different value
            
            Card(Suit.HEARTS, 12),   # P2[0] - Queen
            Card(Suit.SPADES, 3),    # P2[1] - known via initial peek
            Card(Suit.CLUBS, 8),     # P2[2]
            Card(Suit.DIAMONDS, 1),  # P2[3]
            
            Card(Suit.HEARTS, 4),    # Initial discard
            
            # Rest of deck
            *[Card(Suit.HEARTS, i) for i in [1, 5, 6, 8, 11, 13]],
            *[Card(Suit.SPADES, i) for i in [1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13]],
            *[Card(Suit.CLUBS, i) for i in [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13]],
            *[Card(Suit.DIAMONDS, i) for i in [2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13]]
        ]
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Player1 knows position 0 has Hearts 2
        assert player1.known_cards[0] == True
        assert player1.hand[0] == Card(Suit.HEARTS, 2)
        
        # Test against 7♣ - no matching known cards
        discard_7_clubs = Card(Suit.CLUBS, 7)
        matches = player1.get_discard_pile_matches(discard_7_clubs)
        
        assert len(matches) == 0  # No matches because known card (2♥) doesn't match 7♣
        
    def test_matching_after_card_swap(self):
        """Test matching works correctly after card swaps"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Player1 initially knows position 0 has Hearts 2
        assert player1.known_cards[0] == True
        assert player1.hand[0] == Card(Suit.HEARTS, 2)
        
        # Swap a new card into position 0
        new_card = Card(Suit.SPADES, 8)
        old_card = player1.swap_card(0, new_card)
        
        # After swap, player should know the new card
        assert player1.known_cards[0] == True
        assert player1.hand[0] == new_card
        
        # Test matching with the new card
        discard_8_hearts = Card(Suit.HEARTS, 8)
        matches = player1.get_discard_pile_matches(discard_8_hearts)
        
        assert len(matches) == 1
        assert matches[0][0] == 0  # Position 0
        assert matches[0][1] == new_card  # Spades 8
        
        # Test no matching with the old card value
        discard_2_clubs = Card(Suit.CLUBS, 2)
        matches = player1.get_discard_pile_matches(discard_2_clubs)
        
        assert len(matches) == 0  # No matches because position 0 no longer has a 2
        
    def test_full_matching_integration(self):
        """Test complete matching flow with game engine"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        # Create deck where matching opportunities will occur
        test_deck = [
            Card(Suit.HEARTS, 6),    # P1[0] - known via initial peek
            Card(Suit.SPADES, 7),    # P1[1] - unknown
            Card(Suit.CLUBS, 6),     # P1[2] - unknown, but matches value at pos 0
            Card(Suit.DIAMONDS, 5),  # P1[3] - unknown
            
            Card(Suit.HEARTS, 10),   # P2[0] 
            Card(Suit.SPADES, 3),    # P2[1] - known via initial peek
            Card(Suit.CLUBS, 8),     # P2[2]
            Card(Suit.DIAMONDS, 1),  # P2[3]
            
            Card(Suit.HEARTS, 4),    # Initial discard
            
            # Cards to be drawn
            Card(Suit.DIAMONDS, 6),  # Will be discarded to create matching opportunity
            
            # Rest of deck
            *[Card(Suit.HEARTS, i) for i in [1, 2, 5, 8, 9, 11, 12, 13]],
            *[Card(Suit.SPADES, i) for i in [1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13]],
            *[Card(Suit.CLUBS, i) for i in [1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13]],
            *[Card(Suit.DIAMONDS, i) for i in [2, 3, 4, 7, 8, 9, 10, 11, 12, 13]]
        ]
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Verify initial state
        assert player1.known_cards[0] == True
        assert player1.hand[0] == Card(Suit.HEARTS, 6)
        
        # Simulate discarding Diamonds 6 to create matching opportunity
        engine.discard_card(Card(Suit.DIAMONDS, 6))
        
        # Test matching opportunity
        top_discard = engine.discard_pile[-1]
        assert top_discard == Card(Suit.DIAMONDS, 6)
        
        matches = player1.get_discard_pile_matches(top_discard)
        
        # Should only match the known Hearts 6 at position 0
        assert len(matches) == 1
        assert matches[0][0] == 0  # Position 0
        assert matches[0][1] == Card(Suit.HEARTS, 6)  # Hearts 6
        
        # Position 2 has Clubs 6 but it's unknown, so it shouldn't be offered
        positions = [match[0] for match in matches]
        assert 2 not in positions  # Clubs 6 at position 2 is unknown
        
    def test_edge_case_empty_discard_pile(self):
        """Test matching behavior with empty or None discard pile"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        
        # Test with None
        matches = player1.get_discard_pile_matches(None)  # type: ignore
        assert len(matches) == 0
        
        # Manually set up player hand for testing
        player1.hand = [Card(Suit.HEARTS, 5), None, None, None]
        player1.known_cards = [True, False, False, False]
        
        # Test with None again
        matches = player1.get_discard_pile_matches(None)  # type: ignore
        assert len(matches) == 0 