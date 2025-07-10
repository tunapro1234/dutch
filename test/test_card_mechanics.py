"""
Tests for card swapping and basic game mechanics
"""

import unittest
from game.engine.game_engine import GameEngine
from game.engine.card import Card, Suit
from test.test_utils import MockPlayer, create_simple_test_deck


class TestCardMechanics(unittest.TestCase):
    """Test card swapping and basic mechanics"""
    
    def test_card_swap_basic(self):
        """Test basic card swapping functionality"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Player1 should have Card(Suit.HEARTS, 2) at position 0 (known)
        assert player1.hand[0] == Card(Suit.HEARTS, 2)
        assert player1.known_cards[0] == True
        
        # Test swapping with a new card
        new_card = Card(Suit.SPADES, 9)
        old_card = player1.swap_card(0, new_card)
        
        # Check swap worked correctly
        assert old_card == Card(Suit.HEARTS, 2)
        assert player1.hand[0] == new_card
        assert player1.known_cards[0] == True  # Should still be known
        
    def test_card_swap_with_drawn_card(self):
        """Test swapping drawn card into hand"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Draw a card (first from test deck after setup)
        drawn_card = engine.draw_card()
        assert drawn_card == Card(Suit.SPADES, 12)  # Queen from test deck
        
        # Test swap action
        action = {"action": "swap", "position": 0}
        result = engine.handle_drawn_card_action(player1, drawn_card, action, False)
        
        assert result["success"] == True
        assert result["action"] == "swap"
        assert result["position"] == 0
        assert result["swapped_card"] == str(Card(Suit.HEARTS, 2))  # Original card at pos 0
        
        # Check hand updated correctly
        assert player1.hand[0] == drawn_card
        assert player1.known_cards[0] == True
        
    def test_discard_drawn_card(self):
        """Test discarding a drawn card"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Draw a card
        drawn_card = engine.draw_card()
        initial_discard_size = len(engine.discard_pile)
        
        # Test discard action
        action = {"action": "discard"}
        result = engine.handle_drawn_card_action(player1, drawn_card, action, False)
        
        assert result["success"] == True
        assert result["action"] == "discard"
        assert result["discarded_card"] == str(drawn_card)
        
        # Check discard pile updated
        assert len(engine.discard_pile) == initial_discard_size + 1
        assert engine.discard_pile[-1] == drawn_card
        
    def test_cannot_discard_card_from_discard_pile(self):
        """Test that you cannot discard a card drawn from discard pile"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Simulate drawing from discard pile
        discard_card = engine.discard_pile[-1]
        
        # Try to discard the card drawn from discard pile
        action = {"action": "discard"}
        result = engine.handle_drawn_card_action(player1, discard_card, action, True)  # drawn_from_discard=True
        
        assert result["success"] == False
        assert "Cannot discard card drawn from discard pile" in result["error"]
        
    def test_peek_own_card(self):
        """Test peeking at own cards"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Player should know position 0 from initial peek
        assert player1.known_cards[0] == True
        assert player1.known_cards[2] == False  # Position 2 should be unknown
        
        # Peek at position 2
        peeked_card = player1.peek_at_own_card(2)
        
        assert peeked_card == Card(Suit.CLUBS, 12)  # Queen at position 2
        assert player1.known_cards[2] == True  # Now should be known
        
    def test_hand_size_tracking(self):
        """Test hand size tracking as cards are removed"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Initially should have 4 cards
        assert player1.get_hand_size() == 4
        assert not player1.is_hand_empty()
        
        # Remove a card by setting to None (simulate discard pile matching)
        player1.hand[0] = None
        assert player1.get_hand_size() == 3
        
        # Remove all cards
        for i in range(4):
            player1.hand[i] = None
            
        assert player1.get_hand_size() == 0
        assert player1.is_hand_empty()
        
    def test_valid_positions(self):
        """Test getting valid positions (positions with cards)"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Initially all positions should be valid
        valid_positions = player1.get_valid_positions()
        assert valid_positions == [0, 1, 2, 3]
        
        # Remove some cards
        player1.hand[1] = None
        player1.hand[3] = None
        
        valid_positions = player1.get_valid_positions()
        assert valid_positions == [0, 2]
        
    def test_discard_pile_matching_logic(self):
        """Test logic for finding discard pile matches"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Player1 should know position 0 has Hearts 2
        assert player1.known_cards[0] == True
        assert player1.hand[0] == Card(Suit.HEARTS, 2)
        
        # Test matching with a 2 from different suit
        discard_card = Card(Suit.SPADES, 2)
        matches = player1.get_discard_pile_matches(discard_card)
        
        assert len(matches) == 1
        assert matches[0][0] == 0  # Position 0
        assert matches[0][1] == Card(Suit.HEARTS, 2)  # Hearts 2
        
        # Test no matching with different value
        discard_card = Card(Suit.SPADES, 7)
        matches = player1.get_discard_pile_matches(discard_card)
        
        assert len(matches) == 0
        
        # Test that unknown cards don't match
        discard_card = Card(Suit.SPADES, 7)  # Assuming position 1 has Spades 7 but unknown
        matches = player1.get_discard_pile_matches(discard_card)
        
        assert len(matches) == 0  # Should be 0 because position 1 is unknown
        
    def test_score_calculation(self):
        """Test score calculation with different card types"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        
        # Manually set hand with known scoring values
        player1.hand = [
            Card(Suit.HEARTS, 1),    # Ace = 1 point
            Card(Suit.SPADES, 5),    # 5 = 5 points  
            Card(Suit.HEARTS, 13),   # Red King = 0 points
            Card(Suit.CLUBS, 11),    # Jack = 10 points
        ]
        
        score = player1.get_score()
        assert score == 16  # 1 + 5 + 0 + 10 = 16
        
    def test_red_vs_black_king_scoring(self):
        """Test Red Kings score 0, Black Kings score 10"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        
        # Test Red Kings
        red_heart_king = Card(Suit.HEARTS, 13)
        red_diamond_king = Card(Suit.DIAMONDS, 13)
        
        assert red_heart_king.get_score_value() == 0
        assert red_diamond_king.get_score_value() == 0
        assert red_heart_king.is_red_king() == True
        assert red_diamond_king.is_red_king() == True
        
        # Test Black Kings  
        black_spade_king = Card(Suit.SPADES, 13)
        black_club_king = Card(Suit.CLUBS, 13)
        
        assert black_spade_king.get_score_value() == 10
        assert black_club_king.get_score_value() == 10
        assert black_spade_king.is_red_king() == False
        assert black_club_king.is_red_king() == False 