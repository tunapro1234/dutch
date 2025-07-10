#!/usr/bin/env python3
"""
Dutch Cabo Card Game

Core game with essential modes:
1. Single-player: Human vs AI
2. Agent Battle: AI vs AI (supports flag-based execution)
3. Real Life: AI assistant for physical cards (supports flag-based execution)
"""

import sys
import argparse
from game.play.game_runner import GameRunner


def show_game_menu():
    """Show simplified game mode menu"""
    print("\n" + "="*50)
    print("🃏 DUTCH CABO CARD GAME 🃏")
    print("="*50)
    print("Choose your game mode:")
    print()
    print("1. 🎯 Single-Player (Human vs AI)")
    print("2. 🤖 Agent Battle (AI vs AI)")  
    print("3. 🎮 Real Life Mode (AI Assistant)")
    print("4. ❌ Exit")
    print()
    print("="*50)


def get_user_choice():
    """Get valid user choice"""
    while True:
        try:
            choice = input("Enter your choice (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ Invalid choice. Please enter 1-4.")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='🃏 Dutch Cabo Card Game - Enhanced implementation with AI opponents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python dutch.py                           # Interactive mode selection menu
  python dutch.py -s                        # Single-player: Human vs AI
  python dutch.py -a simple bayes 5         # Agent battle: SimpleAI vs BayesPlayer, 5 games
  python dutch.py --agent-battle smart simple 10  # Agent battle: SmartBayes vs SimpleAI, 10 games
  python dutch.py -r                        # Real life assistant mode
  python dutch.py --mode single-player      # Alternative syntax

Available AI types for agent battle:
  simple     - SimpleAI (🟢 Basic strategy)
  bayes      - BayesPlayer (🟡 Probabilistic reasoning)
  smart      - SmartBayesPlayer (🔴 Advanced analytics)

Game Modes:
  🎯 Single-Player: Play against AI with difficulty selection
  🤖 Agent Battle: Watch AI agents compete (specify AIs and game count via flags)
  🎮 Real Life: AI assistant for physical card games
        '''
    )
    
    # Mode selection flags
    parser.add_argument('--mode', choices=[
        'single-player', 
        'agent-battle', 
        'real-life'
    ], help='Game mode to run directly')
    
    # Individual mode flags
    parser.add_argument('-s', '--single-player', action='store_true',
                        help='🎯 Single-Player mode: Human vs AI')
    parser.add_argument('-a', '--agent-battle', nargs=3, metavar=('PLAYER1_AI', 'PLAYER2_AI', 'NUM_GAMES'),
                        help='🤖 Agent Battle mode: AI vs AI (player1_ai player2_ai num_games)')
    parser.add_argument('-r', '--real-life', action='store_true',
                        help='🎮 Real Life mode: AI assistant for physical cards')
    
    # Debug options
    parser.add_argument('--debug', action='store_true',
                        help='🔍 Enable debug mode: Show AI reasoning, visible cards, and decision process')
    
    args = parser.parse_args()
    
    # Check for individual flags first
    runner = GameRunner()
    
    if args.single_player or args.mode == 'single-player':
        print("🎯 Starting Single-Player Mode...")
        if args.debug:
            print("🔍 Debug mode enabled - AI reasoning will be shown")
        runner.run_single_player(debug_mode=args.debug)
        return
    elif args.agent_battle or args.mode == 'agent-battle':
        print("🤖 Starting Agent Battle Mode...")
        if args.agent_battle:
            # Extract parameters from flag
            player1_ai, player2_ai, num_games_str = args.agent_battle
            try:
                num_games = int(num_games_str)
                if num_games <= 0:
                    raise ValueError("Number of games must be positive")
            except ValueError as e:
                print(f"❌ Error: Invalid number of games '{num_games_str}'. Must be a positive integer.")
                sys.exit(1)
            
            # Validate AI types
            valid_ais = ['simple', 'bayes', 'smart']
            if player1_ai not in valid_ais:
                print(f"❌ Error: Invalid AI type '{player1_ai}'. Valid options: {', '.join(valid_ais)}")
                sys.exit(1)
            if player2_ai not in valid_ais:
                print(f"❌ Error: Invalid AI type '{player2_ai}'. Valid options: {', '.join(valid_ais)}")
                sys.exit(1)
            
            # Run non-interactive agent battle
            runner.run_agent_battle(player1_ai=player1_ai, player2_ai=player2_ai, num_games=num_games, interactive=False)
        else:
            # Interactive mode
            runner.run_agent_battle(interactive=True)
        return
    elif args.real_life or args.mode == 'real-life':
        print("🎮 Starting Real Life Mode...")
        if args.real_life:
            # Non-interactive mode
            runner.run_real_life_mode(interactive=False)
        else:
            # Interactive mode
            runner.run_real_life_mode(interactive=True)
        return
    
    # Interactive menu
    while True:
        show_game_menu()
        choice = get_user_choice()
        
        runner = GameRunner()
        
        if choice == 1:
            print("\n🎯 Starting Single-Player Mode...")
            runner.run_single_player(debug_mode=args.debug)
            
        elif choice == 2:
            print("\n🤖 Starting Agent Battle...")
            runner.run_agent_battle(interactive=True)
            
        elif choice == 3:
            print("\n🎮 Starting Real Life Mode...")
            runner.run_real_life_mode(interactive=True)
            
        elif choice == 4:
            print("\n👋 Thanks for playing Dutch Cabo!")
            break
        
        # Ask if user wants to continue
        print("\n" + "-"*30)
        continue_choice = input("Play another game? (y/n): ").strip().lower()
        if continue_choice not in ['y', 'yes', '']:
            print("\n👋 Thanks for playing Dutch Cabo!")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Game interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1) 