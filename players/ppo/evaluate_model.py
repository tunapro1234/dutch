#!/usr/bin/env python3
"""
PPO Model Evaluation Script

This script evaluates trained PPO models by running games against various opponents
and collecting detailed performance statistics.
"""

import os
import sys
import argparse
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
import statistics

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from game.play.game_runner import GameRunner
from players.ppo.ppo_player import PPOPlayer
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer

try:
    from players.bayes.smart_bayes import SmartBayesPlayer
except ImportError:
    SmartBayesPlayer = None


class ModelEvaluator:
    """
    Evaluates PPO models against different opponent types
    """
    
    def __init__(self, model_path: str):
        """
        Initialize evaluator with a trained model
        
        Args:
            model_path: Path to the trained PPO model
        """
        self.model_path = model_path
        self.ppo_player = PPOPlayer("PPO_Agent", model_path)
        self.results = {}
        
        # Opponent configurations
        self.opponent_configs = {
            "weak": lambda: [SimpleAI("Simple1"), SimpleAI("Simple2"), SimpleAI("Simple3")],
            "mixed": lambda: [SimpleAI("Simple1"), BayesPlayer("Bayes1"), SimpleAI("Simple2")],
            "strong": lambda: [BayesPlayer("Bayes1"), BayesPlayer("Bayes2"), BayesPlayer("Bayes3")],
        }
        
        # Add smart bayes if available
        if SmartBayesPlayer:
            self.opponent_configs["expert"] = lambda: [
                SmartBayesPlayer("SmartBayes1"), 
                BayesPlayer("Bayes1"), 
                SmartBayesPlayer("SmartBayes2")
            ]
    
    def run_evaluation(self, num_games: int = 100, verbose: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive evaluation against all opponent types
        
        Args:
            num_games: Number of games to play against each opponent type
            verbose: Whether to print progress information
            
        Returns:
            Evaluation results dictionary
        """
        if verbose:
            print(f"🔬 Evaluating PPO model: {os.path.basename(self.model_path)}")
            print(f"🎮 Games per opponent type: {num_games}")
            print("=" * 50)
        
        total_results = {}
        
        for config_name, opponent_factory in self.opponent_configs.items():
            if verbose:
                print(f"\n🤖 Testing against {config_name} opponents...")
            
            # Run games against this opponent configuration
            config_results = self._evaluate_against_opponents(
                opponent_factory(), 
                num_games, 
                config_name,
                verbose
            )
            
            total_results[config_name] = config_results
            
            if verbose:
                win_rate = config_results["win_rate"] * 100
                avg_score = config_results["avg_score"]
                print(f"   ✅ Win Rate: {win_rate:.1f}% | Avg Score: {avg_score:.1f}")
        
        # Calculate overall statistics
        overall_stats = self._calculate_overall_stats(total_results)
        total_results["overall"] = overall_stats
        
        if verbose:
            print("\n" + "=" * 50)
            print("📊 Overall Performance:")
            print(f"   🏆 Overall Win Rate: {overall_stats['win_rate']:.1%}")
            print(f"   📈 Average Score: {overall_stats['avg_score']:.1f}")
            print(f"   🎯 Best vs: {overall_stats['best_matchup']}")
            print(f"   ⚠️ Worst vs: {overall_stats['worst_matchup']}")
        
        return total_results
    
    def _evaluate_against_opponents(self, opponents: List, num_games: int, 
                                  config_name: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Evaluate against a specific set of opponents
        
        Args:
            opponents: List of opponent players
            num_games: Number of games to play
            config_name: Name of the opponent configuration
            verbose: Whether to print progress
            
        Returns:
            Results for this configuration
        """
        wins = 0
        scores = []
        game_lengths = []
        position_stats = {"1st": 0, "2nd": 0, "3rd": 0, "4th": 0}
        
        runner = GameRunner()
        
        for game_num in range(num_games):
            # Reset all players for new game
            all_players = [self.ppo_player] + opponents
            for player in all_players:
                player.reset_for_new_game()
            
            # Run the game
            try:
                results = runner.run_single_game(all_players, verbose=False)
                
                # Collect statistics
                ppo_score = self.ppo_player.get_score()
                scores.append(ppo_score)
                game_lengths.append(results.get("turn_count", 0))
                
                # Check if PPO won
                winner = results.get("winner")
                if winner and winner.name == self.ppo_player.name:
                    wins += 1
                
                # Calculate position (1st = lowest score)
                all_scores = [(player.get_score(), player.name) for player in all_players]
                all_scores.sort()
                
                for pos, (score, name) in enumerate(all_scores):
                    if name == self.ppo_player.name:
                        if pos == 0:
                            position_stats["1st"] += 1
                        elif pos == 1:
                            position_stats["2nd"] += 1
                        elif pos == 2:
                            position_stats["3rd"] += 1
                        else:
                            position_stats["4th"] += 1
                        break
                
                # Progress indicator
                if verbose and (game_num + 1) % (num_games // 10) == 0:
                    current_win_rate = wins / (game_num + 1)
                    print(f"      Game {game_num + 1}/{num_games} - Win Rate: {current_win_rate:.1%}")
                    
            except Exception as e:
                print(f"⚠️ Error in game {game_num + 1}: {e}")
                continue
        
        # Calculate statistics
        win_rate = wins / num_games if num_games > 0 else 0
        avg_score = statistics.mean(scores) if scores else 0
        median_score = statistics.median(scores) if scores else 0
        min_score = min(scores) if scores else 0
        max_score = max(scores) if scores else 0
        avg_game_length = statistics.mean(game_lengths) if game_lengths else 0
        
        return {
            "games_played": num_games,
            "wins": wins,
            "win_rate": win_rate,
            "avg_score": avg_score,
            "median_score": median_score,
            "min_score": min_score,
            "max_score": max_score,
            "score_std": statistics.stdev(scores) if len(scores) > 1 else 0,
            "avg_game_length": avg_game_length,
            "position_distribution": {
                pos: count / num_games for pos, count in position_stats.items()
            },
            "opponent_config": config_name
        }
    
    def _calculate_overall_stats(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Calculate overall statistics across all opponent types"""
        total_games = sum(r["games_played"] for r in results.values())
        total_wins = sum(r["wins"] for r in results.values())
        
        # Weighted averages
        avg_score = sum(r["avg_score"] * r["games_played"] for r in results.values()) / total_games
        avg_game_length = sum(r["avg_game_length"] * r["games_played"] for r in results.values()) / total_games
        
        # Best and worst matchups
        best_matchup = max(results.items(), key=lambda x: x[1]["win_rate"])
        worst_matchup = min(results.items(), key=lambda x: x[1]["win_rate"])
        
        return {
            "total_games": total_games,
            "total_wins": total_wins,
            "win_rate": total_wins / total_games,
            "avg_score": avg_score,
            "avg_game_length": avg_game_length,
            "best_matchup": f"{best_matchup[0]} ({best_matchup[1]['win_rate']:.1%})",
            "worst_matchup": f"{worst_matchup[0]} ({worst_matchup[1]['win_rate']:.1%})"
        }
    
    def save_results(self, results: Dict[str, Any], output_file: str = None) -> str:
        """
        Save evaluation results to JSON file
        
        Args:
            results: Evaluation results
            output_file: Optional output file path
            
        Returns:
            Path to saved file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = os.path.splitext(os.path.basename(self.model_path))[0]
            output_file = f"players/ppo/evaluations/eval_{model_name}_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Add metadata
        results["metadata"] = {
            "model_path": self.model_path,
            "evaluation_time": datetime.now().isoformat(),
            "evaluator_version": "1.0"
        }
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
        return output_file
    
    def print_detailed_report(self, results: Dict[str, Any]):
        """Print a detailed evaluation report"""
        print("\n" + "=" * 60)
        print("🔬 DETAILED PPO MODEL EVALUATION REPORT")
        print("=" * 60)
        
        model_name = os.path.basename(self.model_path)
        print(f"Model: {model_name}")
        print(f"Evaluation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📊 Performance by Opponent Type:")
        print("-" * 40)
        
        for config_name, config_results in results.items():
            if config_name == "overall":
                continue
                
            print(f"\n{config_name.upper()} Opponents:")
            print(f"  Games Played: {config_results['games_played']}")
            print(f"  Win Rate: {config_results['win_rate']:.1%}")
            print(f"  Average Score: {config_results['avg_score']:.1f}")
            print(f"  Score Range: {config_results['min_score']:.1f} - {config_results['max_score']:.1f}")
            print(f"  Avg Game Length: {config_results['avg_game_length']:.1f} turns")
            
            # Position distribution
            pos_dist = config_results['position_distribution']
            print(f"  Position Distribution:")
            print(f"    1st: {pos_dist['1st']:.1%}, 2nd: {pos_dist['2nd']:.1%}, "
                  f"3rd: {pos_dist['3rd']:.1%}, 4th: {pos_dist['4th']:.1%}")
        
        # Overall summary
        overall = results["overall"]
        print(f"\n🏆 OVERALL PERFORMANCE:")
        print("-" * 40)
        print(f"Total Games: {overall['total_games']}")
        print(f"Overall Win Rate: {overall['win_rate']:.1%}")
        print(f"Average Score: {overall['avg_score']:.1f}")
        print(f"Best Matchup: {overall['best_matchup']}")
        print(f"Worst Matchup: {overall['worst_matchup']}")
        
        # Performance analysis
        print(f"\n🎯 PERFORMANCE ANALYSIS:")
        print("-" * 40)
        win_rate = overall['win_rate']
        if win_rate > 0.4:
            print("✅ EXCELLENT: Model performs very well!")
        elif win_rate > 0.3:
            print("✅ GOOD: Model is competitive")
        elif win_rate > 0.2:
            print("⚠️ FAIR: Model shows learning but needs improvement")
        else:
            print("❌ POOR: Model needs significant training")
        
        avg_score = overall['avg_score']
        if avg_score < 8:
            print("✅ Low average score - good strategy")
        elif avg_score < 12:
            print("⚠️ Moderate average score")
        else:
            print("❌ High average score - strategy needs work")


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained PPO model")
    parser.add_argument("model_path", help="Path to the trained PPO model (.zip file)")
    parser.add_argument("--games", type=int, default=100, 
                       help="Number of games per opponent type")
    parser.add_argument("--output", type=str, 
                       help="Output file for results (JSON)")
    parser.add_argument("--detailed", action="store_true",
                       help="Print detailed report")
    parser.add_argument("--quiet", action="store_true",
                       help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    # Validate model path
    if not os.path.exists(args.model_path):
        print(f"❌ Model file not found: {args.model_path}")
        return
    
    # Create evaluator
    evaluator = ModelEvaluator(args.model_path)
    
    # Run evaluation
    results = evaluator.run_evaluation(
        num_games=args.games,
        verbose=not args.quiet
    )
    
    # Save results
    output_file = evaluator.save_results(results, args.output)
    
    # Print detailed report if requested
    if args.detailed:
        evaluator.print_detailed_report(results)
    
    print(f"\n🎉 Evaluation completed!")
    print(f"📄 Results: {output_file}")


if __name__ == "__main__":
    main() 