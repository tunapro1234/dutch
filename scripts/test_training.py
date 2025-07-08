#!/usr/bin/env python3
"""
Test DQRN Training Pipeline

Quick verification that all components work correctly before full training.
"""

import torch
import time
from players.dqrn_multi_head.training import DQRNTrainer, HardwareConfig


def test_hardware_detection():
    """Test hardware detection and configuration"""
    print("🖥️  Testing Hardware Detection...")
    
    config = HardwareConfig()
    
    assert config.device in [torch.device("cuda"), torch.device("cpu")]
    assert config.cpu_cores > 0
    assert config.batch_size > 0
    assert config.experience_batch_size > 0
    assert config.num_game_workers > 0
    
    print(f"✅ Hardware detection working correctly")
    return True


def test_network_creation():
    """Test DQRN network creation and forward pass"""
    print("🧠 Testing Network Creation...")
    
    trainer = DQRNTrainer({})
    
    # Test network parameters
    param_count = sum(p.numel() for p in trainer.policy_net.parameters())
    print(f"   Network parameters: {param_count:,}")
    assert param_count > 300000  # Should be around 320K
    
    # Test forward pass
    from players.dqrn_multi_head.action_space import ActionContext
    dummy_state = torch.randn(2, trainer.policy_net.state_size).to(trainer.hardware.device)
    
    output = trainer.policy_net(dummy_state, context=ActionContext.MAIN_ACTION)
    assert "q_values" in output
    assert "hidden_state" in output
    assert output["q_values"].shape[0] == 2  # Batch size
    
    print("✅ Network creation and forward pass working")
    return True


def test_experience_collection():
    """Test experience collection from environment"""
    print("🎮 Testing Experience Collection...")
    
    trainer = DQRNTrainer({})
    
    # Collect small batch of experiences
    start_time = time.time()
    stats = trainer.collect_experience(num_episodes=5)
    collection_time = time.time() - start_time
    
    print(f"   Collected {stats['experiences_collected']} experiences in {collection_time:.2f}s")
    print(f"   Buffer size: {len(trainer.replay_buffer)}")
    print(f"   Average reward: {stats['avg_reward']:.2f}")
    
    assert len(trainer.replay_buffer) > 0
    assert stats['experiences_collected'] > 0
    
    print("✅ Experience collection working")
    return True


def test_training_batch():
    """Test training on a batch of experiences"""
    print("🏋️  Testing Training Batch...")
    
    trainer = DQRNTrainer({})
    
    # First collect enough experiences for training
    trainer.collect_experience(num_episodes=20)  # 20 episodes * 10 experiences = 200 total
    
    if len(trainer.replay_buffer) >= trainer.batch_size:
        # Test training batch
        train_stats = trainer.train_batch()
        
        print(f"   Training loss: {train_stats.get('total_loss', 'N/A')}")
        print(f"   Contexts trained: {train_stats.get('contexts_trained', 0)}")
        
        assert "total_loss" in train_stats
        assert train_stats["total_loss"] > 0
        
        print("✅ Training batch working")
        return True
    else:
        print("⚠️  Not enough experiences for training batch test")
        return False


def test_evaluation():
    """Test evaluation system"""
    print("📊 Testing Evaluation...")
    
    trainer = DQRNTrainer({})
    
    # Test evaluation
    eval_stats = trainer.evaluate(num_games=3)
    
    print(f"   Win rate: {eval_stats['win_rate']:.1%}")
    print(f"   Average reward: {eval_stats['avg_reward']:.2f}")
    
    assert "win_rate" in eval_stats
    assert "avg_reward" in eval_stats
    assert 0 <= eval_stats["win_rate"] <= 1
    
    print("✅ Evaluation working")
    return True


def test_checkpoint_system():
    """Test checkpoint saving and loading"""
    print("💾 Testing Checkpoint System...")
    
    trainer = DQRNTrainer({})
    
    # Save checkpoint
    checkpoint_path = "test_checkpoint.pt"
    trainer.save_checkpoint(checkpoint_path)
    
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=trainer.hardware.device)
    
    assert "policy_net" in checkpoint
    assert "target_net" in checkpoint
    assert "optimizer" in checkpoint
    
    # Clean up
    import os
    os.remove(checkpoint_path)
    
    print("✅ Checkpoint system working")
    return True


def run_full_test():
    """Run all tests"""
    print("🧪 Running DQRN Training Pipeline Tests")
    print("=" * 60)
    
    tests = [
        test_hardware_detection,
        test_network_creation,
        test_experience_collection,
        test_training_batch,
        test_evaluation,
        test_checkpoint_system
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print()
    
    print("=" * 60)
    print(f"🏆 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Ready for training.")
        print("\nTo start training, run:")
        print("python train_dqrn.py --iterations 2000")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    run_full_test() 