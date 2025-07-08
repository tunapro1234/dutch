#!/usr/bin/env python3
"""
DQRN Checkpoint Comparison System

Compare different DQRN training runs against each other to find the best model.
"""

import os
import sys
import torch
import argparse
from typing import Dict, List, Tuple
import time
from collections import defaultdict

# Add parent directory to path
sys.path.append('..')

from players.dqrn_multi_head.dqrn_network import create_dqrn_network
from players.dqrn_multi_head.training import DQRNAgent
from src.game import Game
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer


def load_checkpoint_info(checkpoint_path: str) -> Dict:
    """Load checkpoint metadata"""
    try:
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        return {
            'path': checkpoint_path,
            'episode': checkpoint.get('episode', 'Unknown'),
            'steps': checkpoint.get('step_count', 'Unknown'),
            'name': os.path.basename(os.path.dirname(checkpoint_path))
        }
    except Exception as e:
        return {
            'path': checkpoint_path,
            'episode': 'Error',
            'steps': 'Error',
            'name': os.path.basename(os.path.dirname(checkpoint_path))
        }


def load_dqrn_agent(checkpoint_path: str, name: str, device: str = "cuda") -> DQRNAgent:
    """Load DQRN agent from checkpoint"""
    network = create_dqrn_network(device)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    network.load_state_dict(checkpoint["policy_net"])
    network.eval()
    
    agent = DQRNAgent(network, device)
    agent.name = name
    agent.epsilon = 0.0  # No exploration
    return agent


def play_match(agent1, agent2, num_games: int = 100) -> Dict:
    """Play a match between two agents (DQRN or classic AI)"""
    results = {
        'agent1_wins': 0,
        'agent2_wins': 0,
        'ties': 0,
        'total_games': num_games,
        'agent1_total_score': 0,
        'agent2_total_score': 0
    }
    
    print(f"🥊 {agent1.name} vs {agent2.name} ({num_games} games)")
    
    start_time = time.time()
    
    for game_num in range(num_games):
        if (game_num + 1) % 100 == 0:
            print(f"   Progress: {game_num + 1}/{num_games}")
        
        # Create fresh agents for each game to reset state
        if hasattr(agent1, 'network'):  # DQRN agent
            fresh_agent1 = DQRNAgent(agent1.network, agent1.device)
            fresh_agent1.name = agent1.name
            fresh_agent1.epsilon = 0.0
        else:  # Classic AI
            fresh_agent1 = type(agent1)(agent1.name)
        
        if hasattr(agent2, 'network'):  # DQRN agent
            fresh_agent2 = DQRNAgent(agent2.network, agent2.device)
            fresh_agent2.name = agent2.name  
            fresh_agent2.epsilon = 0.0
        else:  # Classic AI
            fresh_agent2 = type(agent2)(agent2.name)
        
        # Create and play game
        game = Game([fresh_agent1, fresh_agent2])
        
        # Let games run normally to see actual errors
        game.play_game()
        
        # Record results
        if game.winner == fresh_agent1:
            results['agent1_wins'] += 1
        elif game.winner == fresh_agent2:
            results['agent2_wins'] += 1
        else:
            results['ties'] += 1
        
        # Record scores
        results['agent1_total_score'] += fresh_agent1.get_score()
        results['agent2_total_score'] += fresh_agent2.get_score()
    
    match_time = time.time() - start_time
    
    # Calculate statistics
    results['match_time'] = match_time
    results['agent1_win_rate'] = results['agent1_wins'] / num_games
    results['agent2_win_rate'] = results['agent2_wins'] / num_games
    results['agent1_avg_score'] = results['agent1_total_score'] / num_games
    results['agent2_avg_score'] = results['agent2_total_score'] / num_games
    
    print(f"   Results: {results['agent1_wins']}-{results['agent2_wins']}-{results['ties']} (W-L-T)")
    print(f"   Win rates: {results['agent1_win_rate']:.1%} vs {results['agent2_win_rate']:.1%}")
    print(f"   Avg scores: {results['agent1_avg_score']:.1f} vs {results['agent2_avg_score']:.1f}")
    print(f"   Time: {match_time:.1f}s")
    
    return results


def find_training_runs() -> Dict[str, str]:
    """Find all training runs and their latest checkpoints"""
    training_runs = {}
    
    # First check normal training runs
    base_dir = "../players/dqrn_multi_head/checkpoints"
    if os.path.exists(base_dir):
        for folder in os.listdir(base_dir):
            folder_path = os.path.join(base_dir, folder)
            if os.path.isdir(folder_path) and folder != "legacy":
                # Find latest checkpoint in this run
                checkpoints = []
                for file in os.listdir(folder_path):
                    if file.endswith('.pt'):
                        checkpoint_path = os.path.join(folder_path, file)
                        checkpoints.append((checkpoint_path, os.path.getmtime(checkpoint_path)))
                
                if checkpoints:
                    # Sort by modification time, get latest
                    checkpoints.sort(key=lambda x: x[1], reverse=True)
                    training_runs[folder] = checkpoints[0][0]
    
    # Then add legacy checkpoints as individual runs
    legacy_dir = "../players/dqrn_multi_head/checkpoints/legacy"
    if os.path.exists(legacy_dir):
        for file in os.listdir(legacy_dir):
            if file.endswith('.pt'):
                checkpoint_path = os.path.join(legacy_dir, file)
                # Extract meaningful name from filename
                if "final" in file:
                    name = "Legacy_Final"
                elif "iter_" in file:
                    # Extract iteration number
                    iter_num = file.split("iter_")[1].split("_")[0]
                    name = f"Legacy_{iter_num}"
                else:
                    name = file.replace(".pt", "")
                training_runs[name] = checkpoint_path
    
    return training_runs


def run_tournament(training_runs: Dict[str, str], games_per_match: int = 1000) -> Dict:
    """Run a round-robin tournament between all training runs"""
    if len(training_runs) < 2:
        print("❌ Need at least 2 training runs for comparison")
        return {}
    
    print(f"🏆 Running DQRN Championship Tournament")
    print(f"   Participants: {len(training_runs)}")
    print(f"   Games per match: {games_per_match}")
    print(f"   Total matches: {len(training_runs) * (len(training_runs) - 1) // 2}")
    print("=" * 60)
    
    # Load all agents
    agents = {}
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    for run_name, checkpoint_path in training_runs.items():
        try:
            agent = load_dqrn_agent(checkpoint_path, run_name, device)
            agents[run_name] = agent
            
            # Show checkpoint info
            info = load_checkpoint_info(checkpoint_path)
            print(f"✅ Loaded {run_name}: Episode {info['episode']}, Steps {info['steps']}")
        except Exception as e:
            print(f"❌ Failed to load {run_name}: {e}")
    
    if len(agents) < 2:
        print("❌ Failed to load enough agents for comparison")
        return {}
    
    print("\n🥊 Starting Tournament Matches...")
    print("=" * 60)
    
    # Tournament results
    tournament_results = {}
    leaderboard = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0, 'total_score': 0, 'games': 0})
    
    run_names = list(agents.keys())
    total_matches = 0
    completed_matches = 0
    
    # Calculate total matches
    for i in range(len(run_names)):
        for j in range(i + 1, len(run_names)):
            total_matches += 1
    
    # Run round-robin tournament
    for i in range(len(run_names)):
        for j in range(i + 1, len(run_names)):
            agent1_name = run_names[i]
            agent2_name = run_names[j]
            
            print(f"\nMatch {completed_matches + 1}/{total_matches}")
            
            # Play match
            results = play_match(agents[agent1_name], agents[agent2_name], games_per_match)
            tournament_results[f"{agent1_name}_vs_{agent2_name}"] = results
            
            # Update leaderboard
            leaderboard[agent1_name]['wins'] += results['agent1_wins']
            leaderboard[agent1_name]['losses'] += results['agent2_wins']
            leaderboard[agent1_name]['ties'] += results['ties']
            leaderboard[agent1_name]['total_score'] += results['agent1_total_score']
            leaderboard[agent1_name]['games'] += games_per_match
            
            leaderboard[agent2_name]['wins'] += results['agent2_wins']
            leaderboard[agent2_name]['losses'] += results['agent1_wins']
            leaderboard[agent2_name]['ties'] += results['ties']
            leaderboard[agent2_name]['total_score'] += results['agent2_total_score']
            leaderboard[agent2_name]['games'] += games_per_match
            
            completed_matches += 1
    
    # Calculate final statistics
    final_standings = []
    for agent_name, stats in leaderboard.items():
        win_rate = stats['wins'] / stats['games'] if stats['games'] > 0 else 0
        avg_score = stats['total_score'] / stats['games'] if stats['games'] > 0 else 0
        
        final_standings.append({
            'name': agent_name,
            'wins': stats['wins'],
            'losses': stats['losses'],
            'ties': stats['ties'],
            'win_rate': win_rate,
            'avg_score': avg_score,
            'total_games': stats['games']
        })
    
    # Sort by win rate (descending)
    final_standings.sort(key=lambda x: x['win_rate'], reverse=True)
    
    return {
        'standings': final_standings,
        'match_results': tournament_results,
        'total_matches': total_matches,
        'games_per_match': games_per_match,
        'agents': agents
    }


def print_tournament_results(results: Dict) -> Tuple[str, Dict]:
    """Print tournament results in a nice format"""
    if not results:
        return None, {}
    
    print("\n" + "=" * 80)
    print("🏆 TOURNAMENT RESULTS")
    print("=" * 80)
    
    standings = results['standings']
    
    print(f"\n📊 Final Leaderboard:")
    print("-" * 80)
    print(f"{'Rank':<4} {'Training Run':<20} {'Win Rate':<10} {'W-L-T':<15} {'Avg Score':<10}")
    print("-" * 80)
    
    for i, agent in enumerate(standings):
        rank = i + 1
        name = agent['name']
        win_rate = f"{agent['win_rate']:.1%}"
        record = f"{agent['wins']}-{agent['losses']}-{agent['ties']}"
        avg_score = f"{agent['avg_score']:.1f}"
        
        # Add medal for top 3
        if rank == 1:
            rank_str = "🥇"
        elif rank == 2:
            rank_str = "🥈"
        elif rank == 3:
            rank_str = "🥉"
        else:
            rank_str = f"{rank}."
        
        print(f"{rank_str:<4} {name:<20} {win_rate:<10} {record:<15} {avg_score:<10}")
    
    print("-" * 80)
    print(f"Total matches: {results['total_matches']}")
    print(f"Games per match: {results['games_per_match']}")
    print(f"Total games played: {results['total_matches'] * results['games_per_match']}")
    
    # Show champion
    if standings:
        champion = standings[0]
        print(f"\n🏆 CHAMPION: {champion['name']}")
        print(f"   Win Rate: {champion['win_rate']:.1%}")
        print(f"   Record: {champion['wins']}-{champion['losses']}-{champion['ties']}")
        print(f"   Average Score: {champion['avg_score']:.1f}")
        return champion['name'], results.get('agents', {})
    
    return None, {}


def test_against_classic_ais(champion_name: str, champion_agent, games_per_match: int = 1000):
    """Test the champion against classic AI players"""
    print("\n" + "=" * 80)
    print("🤖 CHAMPION vs CLASSIC AIs")
    print("=" * 80)
    
    # Create classic AI opponents
    classic_ais = {
        'SimpleAI': SimpleAI("SimpleAI"),
        'BayesPlayer': BayesPlayer("BayesPlayer")
    }
    
    results = {}
    
    for ai_name, ai_agent in classic_ais.items():
        print(f"\n🎮 {champion_name} vs {ai_name}")
        match_results = play_match(champion_agent, ai_agent, games_per_match)
        results[ai_name] = match_results
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 CLASSIC AI CHALLENGE RESULTS")
    print("=" * 80)
    
    total_wins = 0
    total_losses = 0
    total_ties = 0
    
    for ai_name, match_results in results.items():
        wins = match_results['agent1_wins']
        losses = match_results['agent2_wins']
        ties = match_results['ties']
        win_rate = match_results['agent1_win_rate']
        
        total_wins += wins
        total_losses += losses
        total_ties += ties
        
        print(f"\nvs {ai_name}:")
        print(f"   Record: {wins}-{losses}-{ties} (W-L-T)")
        print(f"   Win Rate: {win_rate:.1%}")
        print(f"   Avg Scores: {match_results['agent1_avg_score']:.1f} vs {match_results['agent2_avg_score']:.1f}")
    
    # Overall performance
    total_games = total_wins + total_losses + total_ties
    overall_win_rate = total_wins / total_games if total_games > 0 else 0
    
    print("\n" + "-" * 40)
    print(f"🏆 {champion_name} Overall vs Classic AIs:")
    print(f"   Total Record: {total_wins}-{total_losses}-{total_ties} (W-L-T)")
    print(f"   Overall Win Rate: {overall_win_rate:.1%}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Compare DQRN checkpoints")
    parser.add_argument("--games", type=int, default=1000,
                       help="Number of games per match (default: 1000)")
    parser.add_argument("--runs", type=str, nargs='+', default=None,
                       help="Specific training runs to compare (default: all)")
    parser.add_argument("--vs-classic", action="store_true",
                       help="Test champion against classic AIs")
    
    args = parser.parse_args()
    
    print("🔍 DQRN Checkpoint Comparison System")
    print("=" * 60)
    
    # Find training runs
    all_runs = find_training_runs()
    
    if not all_runs:
        print("❌ No training runs found!")
        print("Create training runs using: python train_dqrn.py --name <run_name>")
        return
    
    # Filter runs if specified
    if args.runs:
        filtered_runs = {}
        for run_name in args.runs:
            if run_name in all_runs:
                filtered_runs[run_name] = all_runs[run_name]
            else:
                print(f"⚠️  Training run '{run_name}' not found")
        
        if not filtered_runs:
            print("❌ No valid training runs specified")
            return
        
        selected_runs = filtered_runs
    else:
        selected_runs = all_runs
    
    print(f"📋 Found {len(all_runs)} training run(s):")
    for run_name, checkpoint_path in all_runs.items():
        info = load_checkpoint_info(checkpoint_path)
        status = "✅" if run_name in selected_runs else "⏭️ "
        print(f"   {status} {run_name}: Episode {info['episode']}, Steps {info['steps']}")
    
    if len(selected_runs) < 2:
        print("❌ Need at least 2 training runs for comparison")
        return
    
    # Run tournament
    print(f"\n🎯 Comparing {len(selected_runs)} training run(s)")
    results = run_tournament(selected_runs, args.games)
    
    # Print results
    champion_name, agents = print_tournament_results(results)
    
    # Test against classic AIs if requested or always run by default
    if champion_name and champion_name in agents:
        champion_agent = agents[champion_name]
        test_against_classic_ais(champion_name, champion_agent, args.games)


if __name__ == "__main__":
    main() 