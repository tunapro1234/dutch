"""
Quick Play Mode - Immediate game start with default settings
"""

import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import List
from game.play.game_runner import GameRunner
from game.engine.player_base import PlayerBase
from players.bayes.smart_bayes import SmartBayesPlayer


def quick_play():
    """Start a quick game with default settings"""
    print("Starting quick game...")
    
    players: List[PlayerBase] = [
        SmartBayesPlayer("SmartBayes"),
        SmartBayesPlayer("SmartBayes2")
    ]
    
    runner = GameRunner(players)
    runner.play_game()
    
    print("Game completed!") 