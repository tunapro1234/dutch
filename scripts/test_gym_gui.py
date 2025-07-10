#!/usr/bin/env python3
"""
Quick test for Gym environment with GUI
"""

import sys
import os
import time

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_gym_gui():
    """Test gym environment with GUI"""
    try:
        from game.gym_env.dutch_env import DutchCaboEnv
        
        print("Creating environment with GUI...")
        env = DutchCaboEnv(render_mode="gui")
        
        print("Resetting environment...")
        obs, info = env.reset()
        
        print("Rendering initial state...")
        env.render()
        
        print("Running a few steps...")
        for step in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            env.render()
            
            if terminated or truncated:
                print(f"Game ended at step {step}")
                break
                
            time.sleep(1)  # Slow it down to see updates
        
        print("Test completed! Close the GUI window.")
        time.sleep(5)  # Keep it open for a bit
        
        env.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gym_gui() 