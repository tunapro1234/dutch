"""
Tests for Jack and Queen special abilities
"""

import unittest
from typing import cast, List
from game.engine.game_engine import GameEngine
from game.engine.card import Card, Suit
from game.engine.player_base import PlayerBase
from test.test_utils import MockPlayer, create_simple_test_deck


class TestSpecialAbilities(unittest.TestCase):
    """Test Jack and Queen special abilities"""
    
    def test_jack_swap_ability(self):
        """Test Jack swap ability - choosing different positions"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        # Create deck where player1 gets Jack at position 2
        test_deck = [
            Card(Suit.HEARTS, 2),    # P1[0] - known
            Card(Suit.SPADES, 7),    # P1[1] 
            Card(Suit.CLUBS, 11),    # P1[2] - Jack
            Card(Suit.DIAMONDS, 5),  # P1[3]
            
            Card(Suit.HEARTS, 10),   # P2[0] - known (high value)
            Card(Suit.SPADES, 3),    # P2[1] - known
            Card(Suit.CLUBS, 9),     # P2[2]
            Card(Suit.DIAMONDS, 1),  # P2[3] - Ace
            
            Card(Suit.HEARTS, 8),    # Discard pile start
            
            # Rest of deck
            *[Card(Suit.HEARTS, i) for i in [4, 6, 12, 13]],
            *[Card(Suit.SPADES, i) for i in [1, 4, 5, 8, 9, 11, 12, 13]],
            *[Card(Suit.CLUBS, i) for i in [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13]],
            *[Card(Suit.DIAMONDS, i) for i in [2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13]]
        ]
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Player1 should know position 0 (Hearts 2)
        # Player2 should know position 1 (Spades 3)
        assert player1.known_cards[0] == True
        assert player1.hand[0] == Card(Suit.HEARTS, 2)
        assert player2.known_cards[1] == True
        assert player2.hand[1] == Card(Suit.SPADES, 3)
        
        # Set up responses for Jack swap
        player1.swap_responses = [("Player2", 0)]  # Target player2's position 0 (10♥)
        # Player1 should give position 2 (where Jack is)
        
        # Draw Jack and use ability
        drawn_jack = Card(Suit.CLUBS, 11)
        action = {"action": "use_ability", "ability": "jack_swap"}
        
        result = engine.handle_drawn_card_action(player1, drawn_jack, action, False)
        
        # Check that ability was used successfully
        assert result["success"] == True
        assert result["action"] == "use_ability"
        assert "jack_result" in result
        jack_result = result["jack_result"]
        assert jack_result["swap_performed"] == True
        
        # After swap, player1 should have J♥ at position 0, player2 should have 2♥ at position 0
        assert player1.hand[0] == Card(Suit.HEARTS, 11)  # Got Jack from player2
        assert player2.hand[0] == Card(Suit.HEARTS, 2)   # Got 2♥ from player1
        
        # Check knowledge updates
        assert player1.known_cards[0] == True  # Player who used Jack knows what they received
        
    def test_queen_peek_ability(self):
        """Test Queen peek ability"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Set up Queen peek responses
        player1.peek_responses = [("Player2", 2)]  # Peek at player2's position 2
        
        # Draw Queen and use ability
        drawn_queen = Card(Suit.SPADES, 12)
        action = {"action": "use_ability", "ability": "queen_peek"}
        
        result = engine.handle_drawn_card_action(player1, drawn_queen, action, False)
        
        # Check that ability was used
        assert result["success"] == True
        assert result["action"] == "use_ability"
        assert "queen_result" in result
        queen_result = result["queen_result"]
        assert queen_result["peek_performed"] == True
        assert queen_result["target"] == "Player2"
        assert queen_result["position"] == 2
        assert queen_result["peeked_card"] == str(player2.hand[2])
        
    def test_queen_peek_own_card(self):
        """Test Queen peek on own card"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        test_deck = create_simple_test_deck()
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Set up Queen peek responses - peek at own position 3
        player1.peek_responses = [(None, 3)]
        
        # Initially position 3 should be unknown
        assert not player1.known_cards[3]
        
        # Draw Queen and use ability
        drawn_queen = Card(Suit.SPADES, 12)
        action = {"action": "use_ability", "ability": "queen_peek"}
        
        result = engine.handle_drawn_card_action(player1, drawn_queen, action, False)
        
        # Check that ability was used
        assert result["success"] == True
        assert result["action"] == "use_ability"
        assert "queen_result" in result
        queen_result = result["queen_result"]
        assert queen_result["peek_performed"] == True
        assert queen_result["target"] == "self"  # Self
        assert queen_result["position"] == 3
        
        # Now player1 should know their position 3
        assert player1.known_cards[3] == True
        
    def test_discard_pile_matching_after_ability(self):
        """Test discard pile matching after using special abilities"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        # Create deck where matching opportunity exists
        test_deck = [
            Card(Suit.HEARTS, 7),    # P1[0] - will be known
            Card(Suit.SPADES, 7),    # P1[1] - matching card
            Card(Suit.CLUBS, 11),    # P1[2] - Jack
            Card(Suit.DIAMONDS, 5),  # P1[3]
            
            Card(Suit.HEARTS, 10),   # P2[0] 
            Card(Suit.SPADES, 3),    # P2[1] - will be known
            Card(Suit.CLUBS, 9),     # P2[2]
            Card(Suit.DIAMONDS, 1),  # P2[3]
            
            Card(Suit.HEARTS, 8),    # Discard pile start
            
            # Next to be drawn/discarded
            Card(Suit.SPADES, 12),   # Queen
            Card(Suit.CLUBS, 7),     # Will create matching opportunity
            
            # Rest of deck
            *[Card(Suit.HEARTS, i) for i in [1, 2, 3, 4, 6, 9, 11, 12, 13]],
            *[Card(Suit.SPADES, i) for i in [1, 4, 5, 8, 9, 10, 11, 13]],
            *[Card(Suit.CLUBS, i) for i in [1, 2, 3, 4, 5, 6, 8, 10, 12, 13]],
            *[Card(Suit.DIAMONDS, i) for i in [2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13]]
        ]
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Player1 should know position 0 (Hearts 7)
        assert player1.known_cards[0] == True
        assert player1.hand[0] == Card(Suit.HEARTS, 7)
        
        # Use Jack to learn about another card
        player1.swap_responses = [("Player2", 1)]
        drawn_jack = Card(Suit.CLUBS, 11) 
        action = {"action": "use_ability", "ability": "jack_swap"}
        
        result = engine.handle_drawn_card_action(player1, drawn_jack, action, False)
        
        # Now simulate someone discarding 7♣ to trigger matching
        engine.discard_card(Card(Suit.CLUBS, 7))
        
        # Check for matches - player1 should have 7♥ at known position 0
        matches = player1.get_discard_pile_matches(Card(Suit.CLUBS, 7))
        assert len(matches) > 0
        assert matches[0][0] == 0  # Position 0
        assert matches[0][1] == Card(Suit.HEARTS, 7)  # Hearts 7
        
    def test_red_king_scoring(self):
        """Test Red King (13♥ or 13♦) scores as 0"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        
        # Create deck with Red Kings
        test_deck = [
            Card(Suit.HEARTS, 13),   # P1[0] - Red King = 0 points
            Card(Suit.DIAMONDS, 13), # P1[1] - Red King = 0 points
            Card(Suit.SPADES, 13),   # P1[2] - Black King = 13 points
            Card(Suit.CLUBS, 13),    # P1[3] - Black King = 13 points
            
            Card(Suit.HEARTS, 10),   # P2[0] 
            Card(Suit.SPADES, 3),    # P2[1]
            Card(Suit.CLUBS, 9),     # P2[2]
            Card(Suit.DIAMONDS, 1),  # P2[3]
            
            Card(Suit.HEARTS, 8),    # Discard pile start
            
            # Rest of deck
            *[Card(Suit.HEARTS, i) for i in [1, 2, 3, 4, 5, 6, 7, 9, 11, 12]],
            *[Card(Suit.SPADES, i) for i in [1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12]],
            *[Card(Suit.CLUBS, i) for i in [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]],
            *[Card(Suit.DIAMONDS, i) for i in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]
        ]
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        # Calculate scores
        p1_score = player1.calculate_score()
        
        # Red Kings should score 0, Black Kings should score 13
        # Expected: 0 + 0 + 13 + 13 = 26
        assert p1_score == 26 