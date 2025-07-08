"""
Test script for DQRN Multi-Head system

Tests action space, state space, and network integration.
"""

import torch
import numpy as np
from typing import Dict

from .action_space import ActionContext, action_space
from .state_space import state_space
from .dqrn_network import create_dqrn_network


def test_action_space():
    """Test action space functionality"""
    print("=== Testing Action Space ===")
    
    # Test action sizes
    for context in ActionContext:
        size = action_space.get_action_size(context)
        print(f"{context.value}: {size} actions")
    
    # Test action decoding
    print("\nTesting action decoding:")
    
    # Test draw source actions
    for action_id in range(2):
        decoded = action_space.decode_action(ActionContext.DRAW_SOURCE, action_id)
        print(f"Draw {action_id}: {decoded}")
    
    # Test main actions
    for action_id in range(7):
        decoded = action_space.decode_action(ActionContext.MAIN_ACTION, action_id)
        print(f"Main {action_id}: {decoded}")
    
    # Test Jack ability (first few)
    for action_id in range(4):
        decoded = action_space.decode_action(ActionContext.JACK_ABILITY, action_id)
        print(f"Jack {action_id}: {decoded}")
    
    print("Action space tests passed!\n")


def test_state_space():
    """Test state space functionality"""
    print("=== Testing State Space ===")
    
    print(f"State size: {state_space.get_state_size()}")
    
    # Create dummy game state
    dummy_game_state = {
        "own_hand": [
            {"rank": "King", "suit": "Hearts", "score_value": 0},  # Red King
            {"rank": "Ace", "suit": "Spades", "score_value": 1},   # Ace
            None,  # Empty position
            {"rank": "Jack", "suit": "Clubs", "score_value": 10, "has_special_ability": True}
        ],
        "known_cards": [True, True, False, False],
        "opponent_hand": [None, None, None, None],
        "opponent_estimates": [5.0, 3.0, 7.0, 6.0],
        "estimate_confidences": [0.3, 0.6, 0.2, 0.4],
        "drawn_card": {"rank": "Queen", "suit": "Diamonds", "score_value": 10, "has_special_ability": True},
        "top_discard": {"rank": "5", "suit": "Spades", "score_value": 5},
        "discard_pile_size": 8,
        "turn_number": 12,
        "deck_size": 35,
        "own_hand_size": 3,
        "opponent_hand_size": 4,
        "dutch_called": False,
        "action_context": "main_action",
        "recent_actions": [
            {"action": "draw", "success": 1.0, "value_change": -2.0},
            {"action": "swap", "position": 1, "success": 1.0, "value_change": -1.0}
        ]
    }
    
    # Create state vector
    state_vector = state_space.create_state_vector(dummy_game_state)
    print(f"State vector shape: {state_vector.shape}")
    print(f"State vector sample: {state_vector[:10].tolist()}")
    
    print("State space tests passed!\n")


def test_network():
    """Test DQRN network functionality"""
    print("=== Testing DQRN Network ===")
    
    # Create network
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    network = create_dqrn_network(device=device)
    
    # Test forward pass with dummy state
    batch_size = 2
    state_size = state_space.get_state_size()
    dummy_state = torch.randn(batch_size, state_size, device=device)
    
    print(f"\nTesting forward pass with state shape: {dummy_state.shape}")
    
    # Test single context forward pass
    for context in ActionContext:
        output = network.forward(dummy_state, context=context)
        q_values = output["q_values"]
        value = output["value"]
        hidden_state = output["hidden_state"]
        
        expected_action_size = action_space.get_action_size(context)
        print(f"{context.value}:")
        print(f"  Q-values shape: {q_values.shape} (expected: [{batch_size}, {expected_action_size}])")
        print(f"  Value shape: {value.shape}")
        print(f"  Hidden state shapes: {hidden_state[0].shape}, {hidden_state[1].shape}")
        
        assert q_values.shape == (batch_size, expected_action_size), f"Wrong Q-values shape for {context}"
    
    # Test action selection
    print(f"\nTesting action selection:")
    single_state = dummy_state[:1]  # Single sample
    
    for context in ActionContext:
        action, new_hidden, debug_info = network.get_action(
            single_state, 
            context, 
            epsilon=0.1
        )
        
        action_size = action_space.get_action_size(context)
        print(f"{context.value}: selected action {action} (range: 0-{action_size-1})")
        print(f"  Q-value: {debug_info['selected_q_value']:.3f}")
        print(f"  State value: {debug_info['value']:.3f}")
        
        assert 0 <= action < action_size, f"Invalid action {action} for {context}"
    
    print("Network tests passed!\n")


def test_integration():
    """Test full integration"""
    print("=== Testing Integration ===")
    
    # Create network
    device = "cuda" if torch.cuda.is_available() else "cpu"
    network = create_dqrn_network(device=device)
    
    # Create realistic game state
    game_state = {
        "own_hand": [
            {"rank": "2", "suit": "Hearts", "score_value": 2},
            None,
            {"rank": "King", "suit": "Spades", "score_value": 10}, 
            None
        ],
        "known_cards": [True, False, True, False],
        "opponent_hand": [None, None, None, None],
        "opponent_estimates": [4.0, 6.0, 8.0, 5.0],
        "estimate_confidences": [0.4, 0.3, 0.2, 0.5],
        "drawn_card": {"rank": "7", "suit": "Clubs", "score_value": 7},
        "top_discard": {"rank": "9", "suit": "Hearts", "score_value": 9},
        "discard_pile_size": 5,
        "turn_number": 8,
        "deck_size": 40,
        "own_hand_size": 2,
        "opponent_hand_size": 4,
        "dutch_called": False,
        "action_context": "main_action",
        "recent_actions": []
    }
    
    # Convert to state vector
    state_vector = state_space.create_state_vector(game_state)
    state_tensor = state_vector.unsqueeze(0).to(device)  # Add batch dimension
    
    print(f"Game state converted to tensor: {state_tensor.shape}")
    
    # Test decision making for main action context
    context = ActionContext.MAIN_ACTION
    
    # Get valid actions (normally would come from game engine)
    valid_actions_list = action_space.get_valid_actions(context, game_state)
    valid_mask = action_space.create_action_mask(context, valid_actions_list, device)
    
    print(f"Valid actions for {context.value}: {valid_actions_list}")
    print(f"Valid mask: {valid_mask.tolist()}")
    
    # Get action from network
    action, hidden_state, debug_info = network.get_action(
        state_tensor,
        context,
        valid_actions=valid_mask,
        epsilon=0.0  # Greedy
    )
    
    print(f"Selected action: {action}")
    print(f"Action meaning: {action_space.decode_action(context, action)}")
    print(f"Q-values: {debug_info['q_values']}")
    
    # Verify action is valid
    assert action in valid_actions_list, f"Invalid action selected: {action}"
    
    print("Integration tests passed!\n")


def run_all_tests():
    """Run all tests"""
    print("Starting DQRN Multi-Head System Tests...\n")
    
    try:
        test_action_space()
        test_state_space() 
        test_network()
        test_integration()
        
        print("🎉 All tests passed successfully!")
        print("\nDQRN Multi-Head system is ready for training!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests() 