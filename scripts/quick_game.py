#!/usr/bin/env python3
"""
Quick 2-player game launcher for Dutch Cabo.
Simple interface to quickly start games with different AI opponents.
"""

from src.game import Game
from src.player import HumanPlayer
from players import SimpleAI, BayesPlayer


def main():
    """Quick 2-player game setup"""
    print("🎮 Dutch Cabo - Quick 2-Player Game")
    print("=" * 40)
    
    # Get player name
    player_name = input("Enter your name: ").strip()
    if not player_name:
        player_name = "Player"
    
    # Choose AI opponent
    print("\nChoose your opponent:")
    print("1. Simple AI (information-focused strategy)")
    print("2. Bayes AI (advanced Bayesian probability)")
    
    while True:
        try:
            choice = int(input("Choose opponent (1-2): "))
            if choice in [1, 2]:
                break
            else:
                print("Please choose 1 or 2.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Create players
    human = HumanPlayer(player_name)
    
    if choice == 1:
        ai = SimpleAI("Simple AI")
    else:
        ai = BayesPlayer("Bayes AI")
    
    print(f"\n🥊 {human.name} vs {ai.name}")
    print("=" * 40)
    
    # Create and play game
    game = Game([human, ai])
    game.play_game()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing! 👋")
    except Exception as e:
        print(f"\nError: {e}")
        print("Please check your setup and try again.") 