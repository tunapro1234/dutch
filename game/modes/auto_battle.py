"""
Auto Battle Mode - Multiple games with statistics tracking
"""

import sys
import os
from typing import List, Dict
from collections import defaultdict

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game.engine.game_engine import GameEngine
from game.engine.player_base import PlayerBase
from players.bayes.smart_bayes import SmartBayesPlayer
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer


def auto_battle():
    """Run multiple games and show statistics"""
    print("=== Auto Battle Mode ===")
    
    try:
        num_games = int(input("Number of games to play (default 100): ") or "100")
    except ValueError:
        num_games = 100
    
    print("Choose player setup:")
    print("1. SmartBayes vs SimpleAI")
    print("2. SmartBayes vs BayesPlayer") 
    print("3. All three AI types")
    
    choice = input("Choice (1-3): ").strip()
    
    players: List[PlayerBase] = []
    
    if choice == "1":
        players = [
            SmartBayesPlayer("SmartBayes"),
            SimpleAI("SimpleAI")
        ]
    elif choice == "2":
        players = [
            SmartBayesPlayer("SmartBayes"),
            BayesPlayer("BayesPlayer")
        ]
    elif choice == "3":
        players = [
            SmartBayesPlayer("SmartBayes"),
            BayesPlayer("BayesPlayer"),
            SimpleAI("SimpleAI")
        ]
    else:
        print("Invalid choice, using default")
        players = [
            SmartBayesPlayer("SmartBayes"),
            SimpleAI("SimpleAI")
        ]
    
    # Statistics tracking
    wins = defaultdict(int)
    dutch_calls = defaultdict(int)
    total_games = 0
    
    print(f"\nRunning {num_games} games...")
    
    for game_num in range(num_games):
        if (game_num + 1) % 25 == 0:
            print(f"Completed {game_num + 1}/{num_games} games...")
        
        # Create fresh engine for each game
        engine = GameEngine([type(p)(p.name) for p in players])
        
        # Run game without UI
        engine.setup_new_game()
        
        while not engine.game_over:
            turn_result = engine.play_turn()
            
            # Track Dutch calls
            if turn_result.get("action_result", {}).get("action") == "call_dutch":
                player_name = turn_result.get("player", "Unknown")
                dutch_calls[player_name] += 1
            
            if turn_result.get("game_ended"):
                break
        
        # Get final results
        final_results = engine.get_final_results()
        winner = final_results.get("winner", "Unknown")
        wins[winner] += 1
        total_games += 1
    
    # Display statistics
    print("\n" + "=" * 50)
    print("BATTLE RESULTS")
    print("=" * 50)
    
    print(f"Total games played: {total_games}")
    print()
    
    print("Win Statistics:")
    for player_name in [p.name for p in players]:
        win_count = wins[player_name]
        win_rate = (win_count / total_games) * 100 if total_games > 0 else 0
        print(f"  {player_name}: {win_count} wins ({win_rate:.1f}%)")
    
    print()
    print("Dutch Call Statistics:")
    for player_name in [p.name for p in players]:
        calls = dutch_calls[player_name]
        avg_calls = calls / total_games if total_games > 0 else 0
        print(f"  {player_name}: {calls} calls ({avg_calls:.2f} per game)")
    
    print("\n" + "=" * 50) 