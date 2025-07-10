"""
Tests for GameEngine basic functionality
"""

import unittest
from typing import cast, List
from game.engine.game_engine import GameEngine
from game.engine.card import Card, Suit
from game.engine.player_base import PlayerBase
from test.test_utils import MockPlayer, create_simple_test_deck


class TestGameEngine(unittest.TestCase):
    """Test GameEngine basic functionality"""
    
    def test_engine_initialization(self):
        """Test GameEngine initialization"""
        player1 = MockPlayer("Player1")
        player2 = MockPlayer("Player2")
        
        # Normal initialization
        engine = GameEngine([player1, player2])
        assert len(engine.players) == 2
        assert engine.current_player_index == 0
        assert not engine.game_over
        assert engine.turn_count == 0
        assert not engine.dutch_called
        
    def test_fixed_deck_initialization(self):
        """Test GameEngine with fixed deck"""
        player1 = MockPlayer("Player1")
        player2 = MockPlayer("Player2")
        test_deck = create_simple_test_deck()
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        assert engine.fixed_deck == test_deck
        
    def test_invalid_player_count(self):
        """Test GameEngine rejects invalid player counts"""
        player1 = MockPlayer("Player1")
        
        # Too few players
        with self.assertRaises(ValueError):
            GameEngine([player1])
            
        # Too many players
        players = cast(List[PlayerBase], [MockPlayer(f"Player{i}") for i in range(5)])
        with self.assertRaises(ValueError):
            GameEngine(players)
    
    def test_game_setup_with_fixed_deck(self):
        """Test game setup uses fixed deck correctly"""
        player1 = MockPlayer("Player1", initial_peek_pos=0)
        player2 = MockPlayer("Player2", initial_peek_pos=1)
        test_deck = create_simple_test_deck()
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        setup_result = engine.setup_new_game()
        
        # Check deck is used correctly
        assert len(engine.deck) == len(test_deck) - 9  # 8 dealt + 1 discard
        
        # Check players got correct cards
        assert player1.hand[0] == Card(Suit.HEARTS, 2)   # First card
        assert player1.hand[1] == Card(Suit.SPADES, 7)   # Second card
        assert player1.hand[2] == Card(Suit.CLUBS, 12)   # Third card (Queen)
        assert player1.hand[3] == Card(Suit.DIAMONDS, 5) # Fourth card
        
        assert player2.hand[0] == Card(Suit.HEARTS, 11)  # Fifth card (Jack)
        assert player2.hand[1] == Card(Suit.SPADES, 3)   # Sixth card
        assert player2.hand[2] == Card(Suit.CLUBS, 9)    # Seventh card
        assert player2.hand[3] == Card(Suit.DIAMONDS, 1) # Eighth card (Ace)
        
        # Check discard pile
        assert engine.discard_pile[-1] == Card(Suit.HEARTS, 8)  # Ninth card
        
        # Check initial peeks
        assert "Player1" in setup_result["initial_peeks"]
        assert "Player2" in setup_result["initial_peeks"]
        
    def test_player_turns(self):
        """Test player turn progression"""
        player1 = MockPlayer("Player1")
        player2 = MockPlayer("Player2")
        
        engine = GameEngine([player1, player2])
        assert engine.get_current_player() == player1
        
        engine.next_turn()
        assert engine.get_current_player() == player2
        assert engine.turn_count == 1
        
        engine.next_turn()
        assert engine.get_current_player() == player1
        assert engine.turn_count == 2
        
    def test_get_other_players(self):
        """Test getting other players"""
        player1 = MockPlayer("Player1")
        player2 = MockPlayer("Player2")
        player3 = MockPlayer("Player3")
        
        engine = GameEngine([player1, player2, player3])
        
        others = engine.get_other_players(player1)
        assert len(others) == 2
        assert player2 in others
        assert player3 in others
        assert player1 not in others
        
    def test_game_state(self):
        """Test game state information"""
        player1 = MockPlayer("Player1")
        player2 = MockPlayer("Player2")
        test_deck = create_simple_test_deck()
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        game_state = engine.get_game_state()
        
        assert game_state["turn_count"] == 0
        assert game_state["current_player"] == "Player1"
        assert "Player1" in game_state["player_hand_sizes"]
        assert "Player2" in game_state["player_hand_sizes"]
        assert game_state["player_hand_sizes"]["Player1"] == 4
        assert game_state["player_hand_sizes"]["Player2"] == 4
        assert not game_state["dutch_called"]
        assert game_state["dutch_caller"] is None
        
    def test_card_drawing(self):
        """Test card drawing mechanism"""
        player1 = MockPlayer("Player1")
        player2 = MockPlayer("Player2")
        test_deck = create_simple_test_deck()
        
        engine = GameEngine([player1, player2], fixed_deck=test_deck)
        engine.setup_new_game()
        
        initial_deck_size = len(engine.deck)
        drawn_card = engine.draw_card()
        
        assert len(engine.deck) == initial_deck_size - 1
        assert drawn_card == Card(Suit.SPADES, 12)  # First card to be drawn
        
    def test_discard_card(self):
        """Test card discarding"""
        player1 = MockPlayer("Player1")
        player2 = MockPlayer("Player2")
        
        engine = GameEngine([player1, player2])
        engine.setup_new_game()
        
        initial_discard_size = len(engine.discard_pile)
        test_card = Card(Suit.HEARTS, 5)
        
        engine.discard_card(test_card)
        
        assert len(engine.discard_pile) == initial_discard_size + 1
        assert engine.discard_pile[-1] == test_card 