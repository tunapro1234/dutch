#!/usr/bin/env python3
"""
Dutch Cabo Card Game
Entry point for the game with different modes
"""

import argparse
import sys
import os

# Add game directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'game'))

from game.modes import (
    quick_play,
    agent_vs_agent,
    auto_battle,
    ai_vs_human_mode,
    full_setup,
    show_help
)


def main():
    """Main entry point - parse arguments and route to appropriate mode"""
    parser = argparse.ArgumentParser(description="Dutch Cabo Card Game")
    parser.add_argument("--mode", "-m", 
                       choices=["quick", "agent", "battle", "ai-human", "setup", "help"],
                       help="Game mode to run")
    
    args = parser.parse_args()
    
    if args.mode == "quick":
        quick_play()
    elif args.mode == "agent":
        agent_vs_agent()
    elif args.mode == "battle":
        auto_battle()
    elif args.mode == "ai-human":
        ai_vs_human_mode()
    elif args.mode == "setup":
        full_setup()
    elif args.mode == "help":
        show_help()
    else:
        # Show interactive menu
        show_menu()


def show_menu():
    """Show interactive menu for game mode selection"""
    while True:
        print("\n" + "=" * 50)
        print("DUTCH CABO CARD GAME")
        print("=" * 50)
        print("Choose a game mode:")
        print()
        print("1. Quick Play - Instant AI vs AI game")
        print("2. Agent vs Agent - Choose AI matchups")
        print("3. Auto Battle - Multiple games with statistics")
        print("4. AI vs Human - AI plays, you execute moves")
        print("5. Full Setup - Custom player configuration")
        print("6. Help - Rules and instructions")
        print("7. Exit")
        print()
        
        choice = input("Enter your choice (1-7): ").strip()
        
        try:
            if choice == "1":
                quick_play()
            elif choice == "2":
                agent_vs_agent()
            elif choice == "3":
                auto_battle()
            elif choice == "4":
                ai_vs_human_mode()
            elif choice == "5":
                full_setup()
            elif choice == "6":
                show_help()
            elif choice == "7":
                print("Thanks for playing!")
                break
            else:
                print("Invalid choice! Please enter 1-7.")
                
        except KeyboardInterrupt:
            print("\nGame interrupted. Returning to menu...")
        except Exception as e:
            print(f"Error occurred: {e}")
            print("Returning to menu...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0) 