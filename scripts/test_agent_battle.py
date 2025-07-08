#!/usr/bin/env python3
"""
Test script to demonstrate agent vs agent functionality
"""

import subprocess
import sys

def test_agent_battle():
    """Test the agent vs agent mode with automated input"""
    print("🧪 Testing Agent vs Agent Mode")
    print("=" * 50)
    
    # Simulate inputs for: agent1=2 (BayesPlayer), agent2=1 (SimpleAI), games=3, details=n
    inputs = "2\n1\n3\nn\n"
    
    try:
        # Run the agent vs agent mode with simulated input
        result = subprocess.run([
            sys.executable, "dutch.py", "--agent-vs-agent"
        ], input=inputs, text=True, capture_output=True, timeout=30)
        
        print("Exit code:", result.returncode)
        print("\nSTDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Agent vs Agent test completed successfully!")
        else:
            print("❌ Agent vs Agent test failed!")
            
    except subprocess.TimeoutExpired:
        print("⏱️ Test timed out (may be normal for interactive mode)")
    except Exception as e:
        print(f"❌ Error running test: {e}")

if __name__ == "__main__":
    test_agent_battle() 