#!/usr/bin/env python3
"""
Test script for the simple GUI
"""

import sys
import os
import time

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from game.gui.simple_gui import SimpleGameGUI


def test_gui_standalone():
    """Test GUI independently"""
    print("Testing GUI standalone...")
    
    gui = SimpleGameGUI("Dutch Cabo - Test")
    
    # Add test players
    gui.add_player("GymAgent", is_gym_player=True)
    gui.add_player("SimpleAI_1")
    gui.add_player("SimpleAI_2")
    gui.add_player("SimpleAI_3")
    
    # Update with test data
    gui.update_game_state({
        "turn_count": 7,
        "current_player": "GymAgent",
        "dutch_called": False,
        "deck_size": 25,
        "top_discard": "Q♥"
    })
    
    # Update players
    gui.update_player("GymAgent", {
        "hand": ["A♠", None, "K♦", "7♣"],
        "known_cards": [True, False, True, True],
        "score": 21,
        "hand_size": 3
    })
    
    gui.update_player("SimpleAI_1", {
        "hand": ["?", "?", "?", "?"],
        "known_cards": [False, True, False, False],
        "score": 15,
        "hand_size": 4
    })
    
    gui.update_player("SimpleAI_2", {
        "hand": ["?", "?", None, None],
        "known_cards": [False, False, False, False],
        "score": 8,
        "hand_size": 2
    })
    
    gui.set_status("Test game in progress...")
    
    print("GUI started. Close the window to exit.")
    gui.start_gui()


def test_gym_with_gui():
    """Test GUI with actual gym environment"""
    print("Testing GUI with Gym environment...")
    
    try:
        from game.gym_env.dutch_env import DutchCaboEnv
        
        # Create environment with GUI
        env = DutchCaboEnv(render_mode="gui")
        
        print("Environment created. Starting episodes...")
        
        # Run a few episodes
        for episode in range(3):
            obs, info = env.reset()
            env.render()  # This will update GUI
            
            print(f"Episode {episode + 1} started")
            
            done = False
            step = 0
            while not done and step < 50:
                # Random action
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                
                # Render GUI
                env.render()
                
                done = terminated or truncated
                step += 1
                
                # Small delay to see the updates
                time.sleep(0.5)
            
            print(f"Episode {episode + 1} finished in {step} steps")
            time.sleep(2)  # Pause between episodes
        
        print("Test completed!")
        env.close()
        
    except ImportError as e:
        print(f"Cannot test gym environment: {e}")
        print("Testing standalone GUI instead...")
        test_gui_standalone()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Dutch Cabo GUI")
    parser.add_argument("--mode", choices=["standalone", "gym"], 
                       default="standalone",
                       help="Test mode")
    
    args = parser.parse_args()
    
    if args.mode == "standalone":
        test_gui_standalone()
    else:
        test_gym_with_gui() 