#!/usr/bin/env python3
"""
Dutch Cabo - Main Entry Point

Usage:
    python dutch.py --quick-play              # Quick human vs AI game
    python dutch.py --agent-vs-agent          # Watch two AIs play (interactive)
    python dutch.py --auto-battle [agent1] [agent2] [num_games]  # Automated AI battles
    python dutch.py --full-setup              # Full game setup
"""

import argparse
import sys
import time
import multiprocessing as mp
import os
from typing import List, Optional

# Game imports - Updated for new architecture
from game.engine import GameEngine, PlayerBase
from game.play import HumanPlayer, GameRunner
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer
from players.bayes.smart_bayes import SmartBayesPlayer


def quick_play():
    """Quick human vs AI game"""
    print("🎮 Dutch Cabo - Quick Play")
    print("=" * 50)
    
    # AI type selection
    print("\nSelect AI opponent:")
    print("1. SimpleAI - Rule-based AI")
    print("2. BayesPlayer - Advanced Bayesian AI")
    print("3. SmartBayesPlayer - New Enhanced AI")
    
    while True:
        choice = input("\nSelect AI opponent (1-3): ").strip()
        if choice in ["1", "2", "3"]:
            break
        print("Please enter 1, 2, or 3")
    
    # Create players
    human = HumanPlayer("You")
    
    if choice == "1":
        ai = SimpleAI("SimpleAI")
    elif choice == "2":
        ai = BayesPlayer("BayesAI")
    else:
        ai = SmartBayesPlayer("SmartBayesAI")
    
    print(f"\n🥊 {human.name} vs {ai.name}")
    print("=" * 50)
    
    # Create and run game
    game_runner = GameRunner([human, ai])
    game_runner.play_game()


def auto_battle(agent1_choice=None, agent2_choice=None, num_games=100):
    """Automated AI vs AI battles with optional player selection"""
    print("🤖 Dutch Cabo - Auto Battle Mode")
    print("=" * 50)
    
    # Use defaults if not provided: SmartBayes vs Bayes (newer vs older)
    if agent1_choice is None:
        agent1_choice = "3"  # SmartBayesPlayer (newer)
    if agent2_choice is None:
        agent2_choice = "2"  # BayesPlayer (older)
    
    # Convert to string if passed as int
    agent1_choice = str(agent1_choice)
    agent2_choice = str(agent2_choice)
    
    # Validate choices
    if agent1_choice not in ["1", "2", "3"] or agent2_choice not in ["1", "2", "3"]:
        print("❌ Invalid agent selection! Use 1 (SimpleAI), 2 (BayesPlayer), or 3 (SmartBayesPlayer)")
        return
    
    verbose = False  # Silent mode for speed
    
    # Create agents
    agent1 = create_agent(agent1_choice, "Player1")
    agent2 = create_agent(agent2_choice, "Player2")
    
    if not agent1 or not agent2:
        raise ValueError("Failed to create agents!")
    
    # Show agent names for clarity
    agent_names = {
        "1": "SimpleAI",
        "2": "BayesPlayer", 
        "3": "SmartBayesPlayer"
    }
    
    print(f"🥊 {agent_names[agent1_choice]} vs {agent_names[agent2_choice]}")
    print(f"🎮 Running {num_games} games automatically...")
    
    # Start timing
    start_time = time.time()
    
    results = {agent1.name: 0, agent2.name: 0}
    dutch_calls = {agent1.name: 0, agent2.name: 0}  # Track Dutch calls
    
    # Run games in silent mode
    for game_num in range(num_games):
        # Create fresh agents for each game
        agent1_fresh = create_agent(agent1_choice, "Player1")
        agent2_fresh = create_agent(agent2_choice, "Player2")
        
        if not agent1_fresh or not agent2_fresh:
            raise ValueError(f"Failed to create agents for game {game_num + 1}")
        
        # Create engine for silent mode
        engine = GameEngine([agent1_fresh, agent2_fresh])
        
        # Setup and play game
        engine.setup_new_game()
        
        while not engine.game_over:
            turn_result = engine.play_turn()
            if turn_result.get("game_ended"):
                break
        
        # Get results
        final_results = engine.get_final_results()
        winner_name = final_results.get("winner")
        if winner_name:
            if winner_name in results:
                results[winner_name] += 1
        
        # Track Dutch calls
        if engine.dutch_called and engine.dutch_caller:
            caller_name = engine.dutch_caller.name
            if caller_name in dutch_calls:
                dutch_calls[caller_name] += 1
    
    # End timing
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Show final results
    print(f"\n📊 Auto Battle Results ({num_games} games):")
    print("=" * 40)
    for agent_name, wins in results.items():
        win_rate = (wins / num_games) * 100 if num_games > 0 else 0
        dutch_count = dutch_calls.get(agent_name, 0)
        dutch_rate = (dutch_count / num_games) * 100 if num_games > 0 else 0
        print(f"{agent_name}: {wins} wins ({win_rate:.1f}%) | {dutch_count} dutch calls ({dutch_rate:.1f}%)")
    
    # Show Dutch call statistics
    total_dutch_calls = sum(dutch_calls.values())
    print(f"\n🔔 Dutch Call Statistics:")
    print("=" * 40)
    print(f"Total Dutch calls: {total_dutch_calls}")
    for agent_name, dutch_count in dutch_calls.items():
        dutch_rate = (dutch_count / total_dutch_calls) * 100 if total_dutch_calls > 0 else 0
        print(f"{agent_name}: {dutch_count} calls ({dutch_rate:.1f}% of all Dutch calls)")
    
    # Determine overall winner
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_results) >= 2 and sorted_results[0][1] > sorted_results[1][1]:
        print(f"\n🏆 Overall Winner: {sorted_results[0][0]} ({sorted_results[0][1]} wins)")
    else:
        print(f"\n🤝 It's a tie!")
    
    # Show timing information
    if num_games > 0:
        avg_game_time = total_duration / num_games
        print(f"\n⏱️ Performance:")
        print(f"Total time: {total_duration:.2f} seconds")
        print(f"Average per game: {avg_game_time:.3f} seconds")
        print(f"Games per second: {1 / avg_game_time:.1f}")


def agent_vs_agent():
    """Watch two agents play against each other"""
    print("🤖 Dutch Cabo - Agent vs Agent")
    print("=" * 50)
    
    # Get agent selection
    print("\nAvailable agents:")
    print("1. SimpleAI - Rule-based AI")
    print("2. BayesPlayer - Advanced Bayesian AI")
    print("3. SmartBayesPlayer - New Enhanced AI")
    
    while True:
        agent1_choice = input("\nSelect Agent 1 (1-3): ").strip()
        if agent1_choice in ["1", "2", "3"]:
            break
        print("Please enter 1, 2, or 3")
    
    while True:
        agent2_choice = input("Select Agent 2 (1-3): ").strip()
        if agent2_choice in ["1", "2", "3"]:
            break
        print("Please enter 1, 2, or 3")
    
    # Create agents
    agent1 = create_agent(agent1_choice, "Agent1")
    agent2 = create_agent(agent2_choice, "Agent2")
    
    if not agent1 or not agent2:
        print("❌ Invalid agent selection!")
        return
    
    print(f"\n🥊 {agent1.name} vs {agent2.name}")
    print("=" * 50)
    
    # Game options
    num_games = input("\nNumber of games to play (default: 1): ").strip()
    try:
        num_games = int(num_games) if num_games else 1
    except ValueError:
        num_games = 1
    
    show_details = input("Show detailed game output? (y/n, default: y): ").strip().lower()
    verbose = show_details != 'n'
    
    # Start timing
    start_time = time.time()
    
    results = {"Agent1": 0, "Agent2": 0}
    
    if verbose and num_games == 1:
        # Single game with full output
        game_runner = GameRunner([agent1, agent2])
        game_runner.play_game()
        
        # Determine winner based on final scores
        final_results = game_runner.engine.get_final_results()
        winner_name = final_results.get("winner")
        if winner_name:
            if winner_name == agent1.name:
                results["Agent1"] = 1
            else:
                results["Agent2"] = 1
    else:
        # Multiple games or silent mode
        for game_num in range(num_games):
            if verbose:
                print(f"\n🎲 Game {game_num + 1}/{num_games}")
                print("-" * 30)
            
            # Create fresh agents for each game
            agent1_fresh = create_agent(agent1_choice, "Agent1")
            agent2_fresh = create_agent(agent2_choice, "Agent2")
            
            if not agent1_fresh or not agent2_fresh:
                print(f"Error creating agents for game {game_num + 1}")
                continue
            
            # Create engine for silent mode
            engine = GameEngine([agent1_fresh, agent2_fresh])
            
            # Setup and play game
            engine.setup_new_game()
            
            while not engine.game_over:
                turn_result = engine.play_turn()
                if turn_result.get("game_ended"):
                    break
                
            # Get results
            final_results = engine.get_final_results()
            winner_name = final_results.get("winner")
            if winner_name:
                if winner_name == "Agent1":
                    results["Agent1"] += 1
                else:
                    results["Agent2"] += 1
            
            if verbose:
                print(f"🏆 Winner: {winner_name}")
    
    # End timing
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Show final results
    print(f"\n📊 Final Results ({num_games} games):")
    print("=" * 40)
    for agent_name, wins in results.items():
        win_rate = (wins / num_games) * 100 if num_games > 0 else 0
        print(f"{agent_name}: {wins} wins ({win_rate:.1f}%)")
    
    # Determine overall winner
    if results["Agent1"] > results["Agent2"]:
        print(f"\n🏆 Overall Winner: Agent1 ({agent1.name})")
    elif results["Agent2"] > results["Agent1"]:
        print(f"\n🏆 Overall Winner: Agent2 ({agent2.name})")
    else:
        print(f"\n🤝 It's a tie!")
    
    # Show timing information
    if num_games > 0:
        avg_game_time = total_duration / num_games
        print(f"\n⏱️ Performance:")
        print(f"Total time: {total_duration:.2f} seconds")
        print(f"Average per game: {avg_game_time:.3f} seconds")


def create_agent(choice: str, name: str) -> Optional[PlayerBase]:
    """Create an agent based on user choice"""
    if choice == "1":
        return SimpleAI(name)
    elif choice == "2":
        return BayesPlayer(name)
    elif choice == "3":
        return SmartBayesPlayer(name)
    else:
        return None


def full_setup():
    """Full game setup with multiple players"""
    print("🎮 Dutch Cabo - Full Setup")
    print("=" * 50)
    
    players = []
    
    # Get number of players
    while True:
        try:
            num_players = int(input("\nNumber of players (2-4): "))
            if 2 <= num_players <= 4:
                break
            else:
                print("Please enter a number between 2 and 4.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Create players
    for i in range(num_players):
        print(f"\nPlayer {i + 1}:")
        print("1. Human")
        print("2. SimpleAI")  
        print("3. BayesPlayer")
        print("4. SmartBayesPlayer")
        
        while True:
            choice = input(f"Select type for Player {i + 1} (1-4): ").strip()
            if choice in ["1", "2", "3", "4"]:
                break
            print("Please choose 1, 2, 3, or 4.")
        
        # Get player name
        if choice == "1":
            name = input(f"Enter name for Player {i + 1}: ").strip()
            if not name:
                name = f"Player {i + 1}"
            players.append(HumanPlayer(name))
        else:
            name = input(f"Enter name for AI Player {i + 1} (optional): ").strip()
            if not name:
                name = f"AI_{i + 1}"
            
            if choice == "2":
                players.append(SimpleAI(name))
            elif choice == "3":
                players.append(BayesPlayer(name))
            else:
                players.append(SmartBayesPlayer(name))
    
    print(f"\n🎮 Starting game with {len(players)} players!")
    print("=" * 50)
    
    # Create and run game
    game_runner = GameRunner(players)
    game_runner.play_game()


def show_help():
    """Show help information"""
    print("🎮 Dutch Cabo Card Game")
    print("=" * 50)
    print("""
GAME RULES:
- Goal: Have the lowest score when the game ends
- Each player starts with 4 face-down cards
- Red Kings = 0 points, Aces = 1 point, Face cards = 10 points
- Jacks allow swapping with opponents
- Queens allow peeking at cards
- Call DUTCH to end the game when you think you have the lowest score

COMMANDS:
    python dutch.py --quick-play                     # Quick human vs AI game
    python dutch.py --agent-vs-agent                 # Watch AI vs AI battles (interactive)
    python dutch.py --auto-battle [agent1] [agent2] [num_games]  # Automated AI battles
    python dutch.py --full-setup                     # Custom game with 2-4 players
    python dutch.py --help                           # Show this help

EXAMPLES:
    python dutch.py --quick-play                     # Play against AI
    python dutch.py --agent-vs-agent                 # Watch AIs play (interactive)
    python dutch.py --auto-battle                    # Default: SmartBayes vs Bayes, 100 games
    python dutch.py --auto-battle 1 3                # SimpleAI vs SmartBayes, 100 games
    python dutch.py --auto-battle 2 3 50             # Bayes vs SmartBayes, 50 games
    python dutch.py --full-setup                     # Custom multiplayer setup

AGENT TYPES:
    1. SimpleAI - Rule-based AI
    2. BayesPlayer - Advanced Bayesian AI (older)
    3. SmartBayesPlayer - Enhanced Bayesian AI (newer)
    """)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Dutch Cabo Card Game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python dutch.py --quick-play                     # Quick human vs AI game
    python dutch.py --agent-vs-agent                 # Watch AI vs AI battles
    python dutch.py --auto-battle                    # Default: SmartBayes vs Bayes
    python dutch.py --auto-battle 1 3                # SimpleAI vs SmartBayes
    python dutch.py --auto-battle 2 3 50             # Bayes vs SmartBayes, 50 games
    python dutch.py --full-setup                     # Custom game setup
        """
    )
    
    parser.add_argument(
        "--quick-play", 
        action="store_true",
        help="Quick human vs AI game"
    )
    
    parser.add_argument(
        "--agent-vs-agent",
        action="store_true", 
        help="Watch two AI agents play (interactive)"
    )
    
    parser.add_argument(
        "--auto-battle",
        nargs='*',
        help="Automated AI battle. Usage: --auto-battle [agent1] [agent2] [num_games]. Default: SmartBayes vs Bayes, 100 games"
    )
    
    parser.add_argument(
        "--full-setup",
        action="store_true",
        help="Full game setup (2-4 players)"
    )
    
    parser.add_argument(
        "--help-game",
        action="store_true",
        help="Show game rules and help"
    )
    
    # If no arguments, show help and default to quick play
    if len(sys.argv) == 1:
        print("🎮 Dutch Cabo Card Game")
        print("=" * 50)
        print("Available modes:")
        print("1. Quick Play (Human vs AI)")
        print("2. Agent vs Agent (AI vs AI, interactive)")
        print("3. Auto Battle (AI vs AI, automatic)")
        print("4. Full Setup (2-4 players)")
        print("5. Show Help")
        
        while True:
            choice = input("\nSelect mode (1-5): ").strip()
            if choice == "1":
                quick_play()
                break
            elif choice == "2":
                agent_vs_agent()
                break
            elif choice == "3":
                auto_battle()
                break
            elif choice == "4":
                full_setup()
                break
            elif choice == "5":
                show_help()
                break
            else:
                print("Please enter 1, 2, 3, 4, or 5")
        return
    
    args = parser.parse_args()
    
    # No error handling - let crashes happen for easier debugging
    if args.quick_play:
        quick_play()
    elif args.agent_vs_agent:
        agent_vs_agent()
    elif args.auto_battle is not None:
        # Parse auto-battle arguments
        if len(args.auto_battle) == 0:
            # Default: SmartBayes vs Bayes
            auto_battle()
        elif len(args.auto_battle) == 2:
            # Agent selection: --auto-battle 1 3
            try:
                agent1 = int(args.auto_battle[0])
                agent2 = int(args.auto_battle[1])
                auto_battle(agent1, agent2)
            except ValueError:
                print("❌ Invalid agent numbers! Use 1, 2, or 3")
        elif len(args.auto_battle) == 3:
            # Agent selection + game count: --auto-battle 1 3 50
            try:
                agent1 = int(args.auto_battle[0])
                agent2 = int(args.auto_battle[1])
                num_games = int(args.auto_battle[2])
                auto_battle(agent1, agent2, num_games)
            except ValueError:
                print("❌ Invalid arguments! Use: --auto-battle [agent1] [agent2] [num_games]")
        else:
            print("❌ Invalid auto-battle arguments! Use: --auto-battle [agent1] [agent2] [num_games]")
    elif args.full_setup:
        full_setup()
    elif args.help_game:
        show_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 