#!/usr/bin/env python3
"""
Main entry point for the Dutch Cabo card game.

Run this script to start a new game with CLI interface.
"""

import sys
from src.game import create_game_from_setup


def main():
    """Main function to run the game"""
    try:
        # Create game with player setup
        game = create_game_from_setup()
        
        # Play the game
        game.play_game()
        
        # Ask if they want to play again
        while True:
            play_again = input("\nWould you like to play another round? (y/n): ").lower().strip()
            if play_again in ['y', 'yes']:
                game.round_number += 1
                game.play_game()
            elif play_again in ['n', 'no']:
                break
            else:
                print("Please enter 'y' or 'n'.")
        
        print("\nThanks for playing Dutch Cabo! 🎉")
        
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing! 👋")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 