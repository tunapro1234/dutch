"""
Full Setup Mode - Custom player configuration and game setup
"""

import sys
import os
from typing import List

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game.play.game_runner import GameRunner
from game.engine.player_base import PlayerBase
from game.play.human_player import HumanPlayer
from players.bayes.smart_bayes import SmartBayesPlayer
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer


def full_setup():
    """Full game setup with custom player configuration"""
    print("=== Full Game Setup ===")
    print("Configure your game with custom players")
    print()
    
    players: List[PlayerBase] = []
    
    while len(players) < 4:  # Max 4 players
        print(f"\nPlayer {len(players) + 1} configuration:")
        print("Available player types:")
        print("1. Human Player")
        print("2. SmartBayes AI")
        print("3. SimpleAI")
        print("4. BayesPlayer AI")
        
        if len(players) >= 2:
            print("5. Start game (minimum 2 players)")
        
        choice = input("Choose player type (1-5): ").strip()
        
        if choice == "1":
            name = input("Enter human player name: ").strip() or f"Human{len(players)+1}"
            players.append(HumanPlayer(name))
            print(f"Added human player: {name}")
            
        elif choice == "2":
            name = input("Enter SmartBayes AI name: ").strip() or f"SmartBayes{len(players)+1}"
            players.append(SmartBayesPlayer(name))
            print(f"Added SmartBayes AI: {name}")
            
        elif choice == "3":
            name = input("Enter SimpleAI name: ").strip() or f"SimpleAI{len(players)+1}"
            players.append(SimpleAI(name))
            print(f"Added SimpleAI: {name}")
            
        elif choice == "4":
            name = input("Enter BayesPlayer AI name: ").strip() or f"BayesPlayer{len(players)+1}"
            players.append(BayesPlayer(name))
            print(f"Added BayesPlayer AI: {name}")
            
        elif choice == "5" and len(players) >= 2:
            break
            
        else:
            print("Invalid choice or not enough players!")
    
    print(f"\nGame configured with {len(players)} players:")
    for i, player in enumerate(players):
        player_type = "Human" if isinstance(player, HumanPlayer) else "AI"
        print(f"  {i+1}. {player.name} ({player_type})")
    
    input("\nPress Enter to start the game...")
    
    runner = GameRunner(players)
    runner.play_game()
    print("Game completed!") 