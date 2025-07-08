#!/usr/bin/env python3
"""
Dutch Cabo - Main Entry Point

Usage:
    python dutch.py --quick-play              # Quick human vs AI game
    python dutch.py --agent-vs-agent          # Watch two AIs play
    python dutch.py --full-setup              # Full game setup
    python dutch.py --test-system             # Test DQRN system
    python dutch.py --test-gpu                # Test GPU setup
"""

import argparse
import sys
import time
import multiprocessing as mp
import os
from typing import List, Dict, Optional

# Game imports
from src.game import Game
from src.player import Player, HumanPlayer
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer


def quick_play():
    """Quick human vs AI game"""
    print("🎮 Dutch Cabo - Quick Play")
    print("=" * 50)
    
    # Create players
    human = HumanPlayer("You")
    ai = BayesPlayer("BayesAI")
    
    # Create and run game
    game = Game([human, ai])
    game.play_game()
    winner = game.winner
    
    if winner:
        print(f"\n🏆 Winner: {winner.name}")
        if winner == human:
            print("🎉 Congratulations! You won!")
        else:
            print("🤖 AI wins this time!")
    else:
        print("🤔 Game ended without a clear winner")


def agent_vs_agent():
    """Watch two agents play against each other"""
    print("🤖 Dutch Cabo - Agent vs Agent")
    print("=" * 50)
    
    # Get agent selection
    print("\nAvailable agents:")
    print("1. SimpleAI - Rule-based AI")
    print("2. BayesPlayer - Advanced Bayesian AI")
    
    agent1_choice = input("\nSelect Agent 1 (1-2): ").strip()
    agent2_choice = input("Select Agent 2 (1-2): ").strip()
    
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
    
    # Calculate parallelization strategy
    cpu_cores = os.cpu_count() or 4
    num_workers, batch_size = calculate_parallel_strategy(num_games, cpu_cores)
    
    print(f"\n🚀 Parallel Strategy: {num_workers} workers, ~{batch_size} games per batch")
    print(f"💻 CPU cores: {cpu_cores}, Using: {num_workers}")
    
    results = {"Agent1": 0, "Agent2": 0}
    
    if verbose or num_workers == 1:
        # Single-threaded execution (verbose mode or small batch)
        for game_num in range(num_games):
            if num_games > 1:
                print(f"\n🎲 Game {game_num + 1}/{num_games}")
                print("-" * 30)
            
            # Create fresh agents for each game
            agent1_fresh = create_agent(agent1_choice, "Agent1")
            agent2_fresh = create_agent(agent2_choice, "Agent2")
            
            game = Game([agent1_fresh, agent2_fresh])
            
            if not verbose:
                # Suppress output for multi-game runs
                import io
                import contextlib
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    game.play_game()
                winner = game.winner
            else:
                game.play_game()
                winner = game.winner
            
            # Track results
            if winner:
                results[winner.name] += 1
            
            if verbose:
                print(f"🏆 Winner: {winner.name}")
    
    else:
        # Multi-threaded execution
        print(f"⚡ Running {num_games} games in parallel...")
        
        # Prepare batches for parallel execution
        batches = []
        games_assigned = 0
        
        for worker_id in range(num_workers):
            if games_assigned >= num_games:
                break
                
            # Calculate actual batch size for this worker
            remaining_games = num_games - games_assigned
            actual_batch_size = min(batch_size, remaining_games)
            
            if actual_batch_size > 0:
                batches.append((agent1_choice, agent2_choice, actual_batch_size, games_assigned + 1))
                games_assigned += actual_batch_size
        
        # Run batches in parallel
        with mp.Pool(processes=num_workers) as pool:
            batch_results = pool.map(run_game_batch, batches)
        
        # Merge results from all batches
        for batch_result in batch_results:
            batch_wins = batch_result["results"]
            results["Agent1"] += batch_wins["Agent1"]
            results["Agent2"] += batch_wins["Agent2"]
        
        print(f"✅ Completed {sum(results.values())} games across {len(batches)} batches")
    
    # End timing
    end_time = time.time()
    total_duration = end_time - start_time
    avg_game_time = total_duration / num_games
    
    # Show final results
    print(f"\n📊 Final Results ({num_games} games):")
    print("=" * 40)
    for agent_name, wins in results.items():
        win_rate = (wins / num_games) * 100
        print(f"{agent_name}: {wins} wins ({win_rate:.1f}%)")
    
    # Determine overall winner
    if results["Agent1"] > results["Agent2"]:
        print(f"\n🏆 Overall Winner: Agent1 ({agent1.name})")
    elif results["Agent2"] > results["Agent1"]:
        print(f"\n🏆 Overall Winner: Agent2 ({agent2.name})")
    else:
        print(f"\n🤝 It's a tie!")
    
    # Show timing information
    print(f"\n⏱️ Performance:")
    print(f"Total time: {total_duration:.2f} seconds")
    print(f"Average per game: {avg_game_time:.4f} seconds")
    print(f"Games per minute: {60 / avg_game_time:.1f}")
    print(f"Games per second: {1 / avg_game_time:.1f}")
    
    if num_workers > 1:
        theoretical_speedup = num_workers
        print(f"🚀 Parallel execution with {num_workers} workers")
        print(f"Theoretical max speedup: {theoretical_speedup:.1f}x")
        # Estimate single-threaded performance for comparison
        estimated_single_thread_time = total_duration * num_workers
        actual_speedup = estimated_single_thread_time / total_duration if total_duration > 0 else 1
        print(f"Estimated speedup achieved: {actual_speedup:.1f}x")
        efficiency = (actual_speedup / theoretical_speedup) * 100 if theoretical_speedup > 0 else 0
        print(f"Parallel efficiency: {efficiency:.1f}%")


def create_agent(choice: str, name: str) -> Optional[Player]:
    """Create an agent based on user choice"""
    if choice == "1":
        return SimpleAI(name)
    elif choice == "2":
        return BayesPlayer(name)
    else:
        return None


def calculate_parallel_strategy(num_games: int, cpu_cores: int) -> tuple[int, int]:
    """
    Calculate optimal parallelization strategy.
    
    Args:
        num_games: Total number of games to play
        cpu_cores: Number of CPU cores available
        
    Returns:
        (num_workers, batch_size)
    """
    # Leave 2 cores for system processes
    max_workers = max(1, cpu_cores - 2)
    
    # No parallelization for small game counts (overhead > benefit)
    if num_games < 50:
        return 1, num_games
    
    # For medium counts, use fewer workers to avoid overhead
    if num_games < 200:
        num_workers = min(4, max_workers, num_games // 25)
    else:
        # For large counts, use more workers but cap at reasonable batch sizes
        num_workers = min(max_workers, num_games // 100)
    
    # Ensure we have at least some reasonable work per worker
    num_workers = max(1, min(num_workers, num_games // 20))
    
    # Calculate batch size - distribute games evenly
    batch_size = max(20, num_games // num_workers)
    
    return num_workers, batch_size


def run_game_batch(args) -> Dict:
    """
    Worker function to run a batch of games in parallel.
    
    Args:
        args: Tuple of (agent1_choice, agent2_choice, batch_size, start_game_num)
        
    Returns:
        Dictionary with batch results
    """
    agent1_choice, agent2_choice, batch_size, start_game_num = args
    
    # Suppress output during parallel execution
    import io
    import contextlib
    
    results = {"Agent1": 0, "Agent2": 0}
    
    for game_num in range(batch_size):
        # Create fresh agents for each game
        agent1_fresh = create_agent(agent1_choice, "Agent1")
        agent2_fresh = create_agent(agent2_choice, "Agent2")
        
        if not agent1_fresh or not agent2_fresh:
            continue
            
        game = Game([agent1_fresh, agent2_fresh])
        
        # Suppress all output for parallel execution
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            game.play_game()
        
        winner = game.winner
        if winner:
            results[winner.name] += 1
    
    return {
        "results": results,
        "batch_size": batch_size,
        "start_game": start_game_num
    }


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
        
        while True:
            choice = input(f"Select type for Player {i + 1} (1-3): ").strip()
            if choice in ["1", "2", "3"]:
                break
            print("Please enter 1, 2, or 3.")
        
        if choice == "1":
            name = input(f"Enter name for Player {i + 1}: ").strip() or f"Player{i + 1}"
            players.append(HumanPlayer(name))
        elif choice == "2":
            name = f"SimpleAI{i + 1}"
            players.append(SimpleAI(name))
        elif choice == "3":
            name = f"BayesAI{i + 1}"
            players.append(BayesPlayer(name))
    
    print(f"\n🎲 Starting game with {len(players)} players")
    print("Players:", [p.name for p in players])
    print("=" * 50)
    
    # Create and run game
    game = Game(players)
    game.play_game()
    winner = game.winner
    
    if winner:
        print(f"\n🏆 Winner: {winner.name}")
    else:
        print("🤔 Game ended without a clear winner")


def test_dqrn_system():
    """Test DQRN multi-head system"""
    print("🧪 Testing DQRN Multi-Head System")
    print("=" * 50)
    
    try:
        from players.dqrn_multi_head.test_system import run_all_tests
        run_all_tests()
    except ImportError:
        print("❌ DQRN system not available. Make sure you have PyTorch installed.")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_gpu():
    """Test GPU setup"""
    print("🔧 Testing GPU Setup")
    print("=" * 50)
    
    try:
        import sys
        sys.path.append('scripts')
        from test_gpu import main as test_gpu_main
        test_gpu_main()
    except ImportError as e:
        print(f"❌ Could not import test modules: {e}")
    except Exception as e:
        print(f"❌ GPU test failed: {e}")


def show_help():
    """Show help information"""
    print("🎮 Dutch Cabo - Available Commands")
    print("=" * 50)
    print()
    print("Game Modes:")
    print("  --quick-play        Quick human vs AI game")
    print("  --agent-vs-agent    Watch two AIs compete")
    print("  --full-setup        Full game setup (2-4 players)")
    print()
    print("Testing:")
    print("  --test-system       Test DQRN neural network system")
    print("  --test-gpu          Test GPU/CUDA setup")
    print()
    print("Other:")
    print("  --info              Show detailed information")
    print("  -h, --help          Show basic help")
    print()
    print("Examples:")
    print("  python dutch.py --quick-play")
    print("  python dutch.py --agent-vs-agent")
    print("  python dutch.py --full-setup")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Dutch Cabo Card Game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dutch.py --quick-play        # Quick human vs AI
  python dutch.py --agent-vs-agent    # AI vs AI battles
  python dutch.py --full-setup        # Full game setup
  python dutch.py --test-system       # Test DQRN system
        """
    )
    
    # Add mutually exclusive group for game modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--quick-play', action='store_true', 
                      help='Quick human vs AI game')
    group.add_argument('--agent-vs-agent', action='store_true',
                      help='Watch two agents play against each other')
    group.add_argument('--full-setup', action='store_true',
                      help='Full game setup with multiple players')
    group.add_argument('--test-system', action='store_true',
                      help='Test DQRN multi-head system')
    group.add_argument('--test-gpu', action='store_true',
                      help='Test GPU/CUDA setup')
    group.add_argument('--info', action='store_true',
                      help='Show detailed information')
    
    args = parser.parse_args()
    
    try:
        if args.quick_play:
            quick_play()
        elif args.agent_vs_agent:
            agent_vs_agent()
        elif args.full_setup:
            full_setup()
        elif args.test_system:
            test_dqrn_system()
        elif args.test_gpu:
            test_gpu()
        elif args.info:
            show_help()
    
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for playing Dutch Cabo!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 