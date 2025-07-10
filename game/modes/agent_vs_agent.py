"""
Agent vs Agent Mode - AI players compete against each other
"""

import sys
import os
from typing import List

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game.play.game_runner import GameRunner
from game.engine.player_base import PlayerBase
from players.bayes.smart_bayes import SmartBayesPlayer
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer


def agent_vs_agent():
    """AI agents compete against each other"""
    print("=== Agent vs Agent ===")
    print("Choose AI players:")
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
    
    print(f"Starting game with {len(players)} AI players...")
    runner = GameRunner(players)
    runner.play_game()
    print("Game completed!") 