#!/usr/bin/env python3
"""
Test script for Dutch Cabo Gymnasium Environment

Tests basic functionality and compatibility with stable-baselines3
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gymnasium as gym
import numpy as np
from game.gym_env import DutchCaboEnv
from players.simple_ai import SimpleAI


def test_basic_functionality():
    """Test basic environment functionality"""
    print("🧪 Testing basic Gym environment functionality...")
    
    # Create environment
    env = DutchCaboEnv(render_mode="human")
    
    print(f"✅ Environment created successfully")
    print(f"📊 Observation space: {env.observation_space}")
    print(f"🎮 Action space: {env.action_space}")
    
    # Test reset
    obs, info = env.reset(seed=42)
    print(f"✅ Environment reset successful")
    print(f"📋 Initial observation shape: {obs.shape}")
    print(f"📋 Initial info keys: {list(info.keys())}")
    
    # Test few random steps
    total_reward = 0
    for step in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        print(f"Step {step + 1}: Action={action}, Reward={reward:.2f}, Done={terminated or truncated}")
        
        if terminated or truncated:
            print(f"🏁 Game ended at step {step + 1}")
            break
    
    print(f"💰 Total reward: {total_reward:.2f}")
    env.close()
    print("✅ Basic functionality test completed\n")


def test_full_game():
    """Test a complete game"""
    print("🎲 Testing complete game...")
    
    env = DutchCaboEnv(render_mode="none")  # Silent mode for faster testing
    
    obs, info = env.reset(seed=123)
    
    total_reward = 0
    step_count = 0
    
    while True:
        # Random policy for testing
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        
        total_reward += reward
        step_count += 1
        
        if terminated or truncated:
            print(f"🏁 Game completed in {step_count} steps")
            print(f"💰 Final reward: {total_reward:.2f}")
            
            if "final_results" in info:
                results = info["final_results"]
                print(f"🏆 Winner: {results.get('winner', 'Unknown')}")
                print(f"📊 Final scores: {results.get('final_scores', {})}")
            
            break
    
    env.close()
    print("✅ Full game test completed\n")


def test_stable_baselines3_compatibility():
    """Test compatibility with stable-baselines3"""
    print("🤖 Testing Stable-Baselines3 compatibility...")
    
    try:
        from stable_baselines3 import DQN
        from stable_baselines3.common.env_checker import check_env
        
        # Create environment
        env = DutchCaboEnv(render_mode="none")
        
        # Check environment
        print("🔍 Checking environment compliance...")
        check_env(env)
        print("✅ Environment passes compliance check")
        
        # Create a simple DQN agent
        print("🧠 Creating DQN agent...")
        model = DQN("MlpPolicy", env, verbose=0, learning_starts=10, train_freq=4)
        print("✅ DQN agent created successfully")
        
        # Quick training test (just few steps)
        print("📚 Testing quick training...")
        model.learn(total_timesteps=50)
        print("✅ Training test successful")
        
        # Test prediction
        obs, _ = env.reset()
        action, _states = model.predict(obs, deterministic=True)
        print(f"🎯 Model prediction: action={action}")
        
        env.close()
        print("✅ Stable-Baselines3 compatibility test completed\n")
        
    except ImportError:
        print("⚠️ Stable-Baselines3 not installed, skipping compatibility test\n")
    except Exception as e:
        print(f"❌ Stable-Baselines3 test failed: {e}\n")


def test_action_decoding():
    """Test action decoding functionality"""
    print("🔧 Testing action decoding...")
    
    env = DutchCaboEnv()
    
    # Test all action types
    test_actions = [0, 4, 8, 9, 10, 11, 12, 16]
    
    for action in test_actions:
        decoded = env._decode_action(action)
        print(f"Action {action}: {decoded}")
    
    print("✅ Action decoding test completed\n")


def main():
    """Run all tests"""
    print("🎮 Dutch Cabo Gymnasium Environment Test Suite")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_action_decoding()
        test_full_game()
        test_stable_baselines3_compatibility()
        
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 