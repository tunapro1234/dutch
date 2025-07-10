#!/usr/bin/env python3
"""
DQRN Training Runner for Dutch Cabo

Simple interface to start DQRN training with automatic hardware optimization.
"""

import torch
import os
import argparse
from datetime import datetime
from players.dqrn_multi_head.training import DQRNTrainer


def find_latest_checkpoint(training_dir: str) -> str:
    """Find the latest checkpoint in training directory"""
    if not os.path.exists(training_dir):
        return None
    
    checkpoints = []
    for file in os.listdir(training_dir):
        if file.endswith('.pt'):
            filepath = os.path.join(training_dir, file)
            mtime = os.path.getmtime(filepath)
            checkpoints.append((filepath, mtime))
    
    if not checkpoints:
        return None
    
    # Sort by modification time, return latest
    checkpoints.sort(key=lambda x: x[1], reverse=True)
    return checkpoints[0][0]


def migrate_old_checkpoints():
    """Migrate old checkpoints to new structure"""
    old_dir = "players/dqrn_multi_head/checkpoints"
    new_base = "players/dqrn_multi_head/checkpoints/legacy"
    
    if not os.path.exists(old_dir):
        return
    
    # Find .pt files directly in checkpoints dir (old format)
    old_checkpoints = []
    for file in os.listdir(old_dir):
        if file.endswith('.pt') and os.path.isfile(os.path.join(old_dir, file)):
            old_checkpoints.append(file)
    
    if old_checkpoints:
        os.makedirs(new_base, exist_ok=True)
        print(f"📦 Migrating {len(old_checkpoints)} old checkpoints to 'legacy' folder...")
        
        for checkpoint in old_checkpoints:
            old_path = os.path.join(old_dir, checkpoint)
            new_path = os.path.join(new_base, checkpoint)
            os.rename(old_path, new_path)
        
        print("✅ Migration completed")


def main():
    parser = argparse.ArgumentParser(description="Train DQRN for Dutch Cabo")
    parser.add_argument("--name", type=str, required=True,
                       help="Training run name (creates folder with this name)")
    parser.add_argument("--iterations", type=int, default=5000, 
                       help="Number of training iterations (default: 5000)")
    parser.add_argument("--eval-freq", type=int, default=300,
                       help="Evaluation frequency (default: 300)")
    parser.add_argument("--learning-rate", type=float, default=1e-4,
                       help="Learning rate (default: 1e-4)")
    parser.add_argument("--buffer-size", type=int, default=100000,
                       help="Replay buffer size (default: 100000)")
    parser.add_argument("--batch-size", type=int, default=None,
                       help="Override automatic batch size calculation")
    parser.add_argument("--save-freq", type=int, default=2000,
                       help="Save checkpoint every N iterations (default: 2000)")
    
    args = parser.parse_args()
    
    print("🚀 ULTRA-OPTIMIZED DQRN Training for Dutch Cabo")
    print("=" * 70)
    print("🔥 OPTIMIZATIONS ENABLED:")
    print("   ⚡ Resource-Conscious Parallel Games")
    print("   🎯 Mixed Precision Training") 
    print("   💪 Gradient Accumulation")
    print("   📈 Enlarged Replay Buffer")
    print("   🎲 Dutch Call & Feature Rewards")
    print("=" * 70)
    
    # Migrate old checkpoints first
    migrate_old_checkpoints()
    
    # Setup training directory structure
    base_checkpoint_dir = "players/dqrn_multi_head/checkpoints"
    training_dir = os.path.join(base_checkpoint_dir, args.name)
    os.makedirs(training_dir, exist_ok=True)
    
    print(f"📁 Training: {args.name}")
    print(f"📂 Directory: {training_dir}")
    
    # ULTRA-OPTIMIZED Training configuration
    config = {
        "learning_rate": args.learning_rate,
        "gamma": 0.99,
        "epsilon_start": 1.0,
        "epsilon_end": 0.1,   # Standard final epsilon
        "epsilon_decay": 0.999,   # Standard RL decay rate
        "buffer_size": max(args.buffer_size, 200000),  # Minimum 200K buffer
        "target_update_freq": 500,  # More frequent target updates
        "opponent_update_freq": 1000,  # More frequent opponent updates
        "batch_size_override": args.batch_size,
        "training_name": args.name,
        "self_play_ratio": 0.995,  # Even more self-play
        "ultra_optimized": True  # Enable all performance optimizations
    }
    
    # Create trainer
    trainer = DQRNTrainer(config)
    
    # Auto-resume from latest checkpoint in training directory
    latest_checkpoint = find_latest_checkpoint(training_dir)
    if latest_checkpoint:
        print(f"🔄 Found existing training, resuming from: {os.path.basename(latest_checkpoint)}")
        trainer.load_checkpoint(latest_checkpoint)
    else:
        print("🆕 Starting new training run")
    
    # Initial evaluation
    print("\n🧪 Initial evaluation...")
    eval_stats = trainer.evaluate(num_games=20)
    print(f"   Initial win rate: {eval_stats['win_rate']:.1%}")
    print(f"   Initial avg reward: {eval_stats['avg_reward']:.2f}")
    
    # Display optimized system info
    print(f"\n💻 SYSTEM UTILIZATION:")
    print(f"   GPU: {trainer.hardware.device} ({trainer.hardware.gpu_memory_gb:.1f} GB)")
    print(f"   CPU Cores: {trainer.hardware.cpu_cores} (Using: {trainer.hardware.num_game_workers})")
    print(f"   Training Batch: {trainer.batch_size}")
    print(f"   Game Batch: {trainer.hardware.experience_batch_size}")
    print(f"   Mixed Precision: {'✅' if getattr(trainer, 'use_amp', False) else '❌'}")
    print(f"   Buffer Capacity: {trainer.replay_buffer.capacity:,}")

    # ULTRA-OPTIMIZED Training loop with automatic checkpointing
    try:
        training_results = trainer.train(
            num_iterations=args.iterations, 
            eval_freq=args.eval_freq,
            save_freq=args.save_freq,
            checkpoint_dir=training_dir
        )
        
        # Final evaluation
        print("\n🏆 Final evaluation...")
        final_stats = trainer.evaluate(num_games=100)
        print(f"   Final win rate: {final_stats['win_rate']:.1%}")
        print(f"   Final avg reward: {final_stats['avg_reward']:.2f}")
        
        # Save final checkpoint with complete progress
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = os.path.join(training_dir, f"dqrn_final_{timestamp}.pt")
        
        # Combine training results with final evaluation
        final_progress = training_results.copy()
        final_progress["final_stats"]["final_evaluation_100_games"] = final_stats
        
        trainer.save_checkpoint(checkpoint_path, final_progress)
        
        print(f"\n✅ ULTRA-OPTIMIZED TRAINING COMPLETED!")
        print(f"   🏆 Final model saved: {checkpoint_path}")
        print(f"   ⚡ Performance gains achieved through:")
        print(f"      - Resource-conscious parallel execution")
        print(f"      - Mixed precision training")
        print(f"      - Gradient accumulation")
        print(f"      - Dutch call & feature rewards")
        
    except KeyboardInterrupt:
        print("\n⏸️  Training interrupted by user")
        
        # Save emergency checkpoint
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = os.path.join(training_dir, f"dqrn_interrupted_{timestamp}.pt")
        trainer.save_checkpoint(checkpoint_path)
        print(f"   Emergency checkpoint saved: {checkpoint_path}")
    
    except Exception as e:
        print(f"\n❌ Training failed with error: {e}")
        
        # Save debug checkpoint
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = os.path.join(training_dir, f"dqrn_error_{timestamp}.pt")
        trainer.save_checkpoint(checkpoint_path)
        print(f"   Debug checkpoint saved: {checkpoint_path}")
        raise


if __name__ == "__main__":
    main() 