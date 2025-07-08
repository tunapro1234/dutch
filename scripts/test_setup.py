#!/usr/bin/env python3
"""
Test script to verify environment setup and basic game functionality.
"""

import sys
import random


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from src.card import Card, Suit, create_deck
        from src.player import Player, HumanPlayer
        from src.game import Game
        from players import SimpleAI, BayesPlayer
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_card_creation():
    """Test card creation and special rules"""
    print("\nTesting card creation and special rules...")
    
    try:
        from src.card import Card, Suit, create_deck
        
        # Test regular cards
        ace_hearts = Card(Suit.HEARTS, 1)
        print(f"Ace of Hearts: {ace_hearts} (score: {ace_hearts.get_score_value()})")
        
        # Test red king (should be 0 points)
        red_king = Card(Suit.DIAMONDS, 13)
        print(f"Red King: {red_king} (score: {red_king.get_score_value()})")
        assert red_king.get_score_value() == 0, "Red King should be worth 0 points"
        
        # Test black king (should be 10 points)
        black_king = Card(Suit.SPADES, 13)
        print(f"Black King: {black_king} (score: {black_king.get_score_value()})")
        assert black_king.get_score_value() == 10, "Black King should be worth 10 points"
        
        # Test Jack (special ability)
        jack = Card(Suit.CLUBS, 11)
        print(f"Jack: {jack} (score: {jack.get_score_value()}, has_ability: {jack.has_special_ability()})")
        assert jack.is_jack(), "Jack should be identified as Jack"
        assert jack.has_special_ability(), "Jack should have special ability"
        
        # Test Queen (special ability)
        queen = Card(Suit.HEARTS, 12)
        print(f"Queen: {queen} (score: {queen.get_score_value()}, has_ability: {queen.has_special_ability()})")
        assert queen.is_queen(), "Queen should be identified as Queen"
        assert queen.has_special_ability(), "Queen should have special ability"
        
        # Test deck creation
        deck = create_deck()
        print(f"Deck created with {len(deck)} cards")
        assert len(deck) == 52, "Deck should have 52 cards"
        
        print("✅ Card tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Card test failed: {e}")
        return False


def test_player_creation():
    """Test player creation"""
    print("\nTesting player creation...")
    
    try:
        from src.player import HumanPlayer
        from players import SimpleAI
        from src.card import Card, Suit
        
        # Create players
        human = HumanPlayer("TestHuman")
        ai = SimpleAI("TestAI")
        
        print(f"Created human player: {human.name}")
        print(f"Created AI player: {ai.name}")
        
        # Test card handling
        test_card = Card(Suit.HEARTS, 5)
        human.receive_card(test_card, 0)
        print(f"Human hand after receiving card: {human.display_hand()}")
        
        print("✅ Player tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Player test failed: {e}")
        return False


def test_game_creation():
    """Test basic game creation"""
    print("\nTesting game creation...")
    
    try:
        from src.game import Game
        from players import SimpleAI
        
        # Create a simple 2-player AI game
        players = [SimpleAI("AI1"), SimpleAI("AI2")]
        game = Game(players)
        
        print(f"Created game with {len(game.players)} players")
        print("✅ Game creation test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Game creation test failed: {e}")
        return False


def test_dependencies():
    """Test that required dependencies are available"""
    print("\nTesting dependencies...")
    
    dependencies = ["torch", "numpy", "random"]
    all_good = True
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} available")
        except ImportError:
            print(f"❌ {dep} not available")
            all_good = False
    
    return all_good


def main():
    """Run all tests"""
    print("Dutch Cabo - Environment Setup Test")
    print("=" * 40)
    
    tests = [
        test_dependencies,
        test_imports,
        test_card_creation,
        test_player_creation,
        test_game_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Environment is ready.")
        print("\nYou can now run the game with:")
        print("  python main.py")
    else:
        print("❌ Some tests failed. Please check the setup.")
        sys.exit(1)


if __name__ == "__main__":
    main() 