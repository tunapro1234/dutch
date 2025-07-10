"""
Quick Play GUI Mode - Fast AI vs AI game with visual display
"""

import sys
import os
import threading
import time
from typing import List

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game.play.game_runner import GameRunner
from game.engine.player_base import PlayerBase
from game.gui.simple_gui import SimpleGameGUI
from players.bayes.smart_bayes import SmartBayesPlayer
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer


class VisualGameRunner(GameRunner):
    """Game runner with GUI integration"""
    
    def __init__(self, players: List[PlayerBase], gui: SimpleGameGUI):
        super().__init__(players)
        self.gui = gui
        self.step_delay = 1.0  # Seconds between steps
        self.auto_mode = True
        
    def play_game_visual(self):
        """Play game with visual updates"""
        print("Starting visual game...")
        
        # Setup game
        setup_results = self.engine.setup_new_game()
        print(f"Game setup: {setup_results}")
        
        # Initial GUI update
        self.update_gui()
        self.gui.set_status("Game started!")
        
        # Main game loop with visual updates
        while not self.engine.game_over:
            current_player = self.engine.get_current_player()
            self.gui.set_status(f"{current_player.name}'s turn")
            
            # Update GUI before turn
            self.update_gui()
            
            # Play one turn
            turn_result = self.engine.play_turn()
            
            # Update GUI after turn
            self.update_gui()
            
            # Show turn results in status
            if turn_result.get("turn_completed"):
                action_result = turn_result.get("action_result", {})
                action = action_result.get("action", "unknown")
                self.gui.set_status(f"{current_player.name} performed: {action}")
            
            # Check if game ended
            if turn_result.get("game_ended"):
                break
            
            # Delay for visualization
            if self.auto_mode:
                time.sleep(self.step_delay)
            else:
                input("Press Enter for next turn...")
        
        # Display final results
        final_results = self.engine.get_final_results()
        winner = final_results.get("winner", "Unknown")
        self.gui.set_status(f"Game Over! Winner: {winner}")
        
        print(f"Game finished! Winner: {winner}")
        return final_results
    
    def update_gui(self):
        """Update GUI with current game state"""
        try:
            # Get game state
            current_player = self.engine.get_current_player()
            
            # Update game state
            gui_state = {
                "turn_count": self.engine.turn_count,
                "current_player": current_player.name if current_player else "",
                "dutch_called": self.engine.dutch_called,
                "deck_size": len(self.engine.deck),
                "top_discard": str(self.engine.discard_pile[-1]) if self.engine.discard_pile else None
            }
            self.gui.update_game_state(gui_state)
            
            # Update all players
            for player in self.engine.players:
                player_data = {
                    "hand": [str(card) if card else None for card in player.hand],
                    "known_cards": player.known_cards,
                    "score": player.get_score(),
                    "hand_size": player.get_hand_size()
                }
                self.gui.update_player(player.name, player_data)
                
        except Exception as e:
            print(f"GUI update error: {e}")


def quick_play_gui():
    """Quick AI vs AI game with GUI visualization"""
    print("=== Quick Play GUI Mode ===")
    print("Fast AI vs AI game with visual display")
    print()
    
    # Player selection
    print("Select AI players:")
    print("1. SmartBayes vs SimpleAI")
    print("2. SmartBayes vs BayesPlayer")
    print("3. SimpleAI vs BayesPlayer")
    print("4. All three AI types")
    
    choice = input("Choice (1-4, default 1): ").strip() or "1"
    
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
            SimpleAI("SimpleAI"),
            BayesPlayer("BayesPlayer")
        ]
    elif choice == "4":
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
    
    # Speed selection
    print(f"\nGame will show {len(players)} AI players:")
    for i, player in enumerate(players):
        print(f"  {i+1}. {player.name}")
    
    print("\nSelect game speed:")
    print("1. Fast (0.5s per turn)")
    print("2. Normal (1s per turn)")
    print("3. Slow (2s per turn)")
    print("4. Manual (press Enter for each turn)")
    
    speed_choice = input("Speed (1-4, default 2): ").strip() or "2"
    
    # Create GUI
    gui = SimpleGameGUI("Dutch Cabo - Quick Play")
    
    # Add players to GUI
    for i, player in enumerate(players):
        is_first = (i == 0)  # First player shows cards
        gui.add_player(player.name, is_gym_player=is_first)
    
    # Start GUI in background
    gui_thread = threading.Thread(target=gui.start_gui, daemon=True)
    gui_thread.start()
    
    # Create visual game runner
    visual_runner = VisualGameRunner(players, gui)
    
    # Set speed
    if speed_choice == "1":
        visual_runner.step_delay = 0.5
    elif speed_choice == "2":
        visual_runner.step_delay = 1.0
    elif speed_choice == "3":
        visual_runner.step_delay = 2.0
    elif speed_choice == "4":
        visual_runner.auto_mode = False
    
    print(f"\nStarting game with {len(players)} AI players...")
    print("Check the GUI window for visual updates!")
    
    # Initial delay to let GUI load
    time.sleep(1)
    
    # Run the visual game
    final_results = visual_runner.play_game_visual()
    
    # Show final results
    print("\n" + "=" * 50)
    print("GAME RESULTS")
    print("=" * 50)
    
    winner = final_results.get("winner", "Unknown")
    final_scores = final_results.get("final_scores", {})
    
    print(f"🏆 Winner: {winner}")
    print("\nFinal Scores:")
    
    # Sort players by score
    sorted_scores = sorted(final_scores.items(), key=lambda x: x[1])
    
    for i, (player_name, score) in enumerate(sorted_scores):
        if i == 0:
            print(f"  🥇 {player_name}: {score} points")
        elif i == 1:
            print(f"  🥈 {player_name}: {score} points")
        elif i == 2:
            print(f"  🥉 {player_name}: {score} points")
        else:
            print(f"     {player_name}: {score} points")
    
    print("\nGame completed! You can close the GUI window.")
    input("Press Enter to exit...")
    gui.close()


# Quick test function
def test_quick_gui():
    """Test the quick play GUI"""
    print("Testing Quick Play GUI...")
    
    # Simple 2-player test
    players = [
        SmartBayesPlayer("AI1"),
        SimpleAI("AI2")
    ]
    
    gui = SimpleGameGUI("Test Game")
    
    for player in players:
        gui.add_player(player.name, is_gym_player=True)
    
    # Start GUI
    gui_thread = threading.Thread(target=gui.start_gui, daemon=True)
    gui_thread.start()
    
    # Create and run game
    visual_runner = VisualGameRunner(players, gui)
    visual_runner.step_delay = 1.0
    
    print("Running test game...")
    final_results = visual_runner.play_game_visual()
    
    print(f"Test completed. Winner: {final_results.get('winner', 'Unknown')}")
    time.sleep(3)
    gui.close()


if __name__ == "__main__":
    test_quick_gui() 