#!/usr/bin/env python3
"""
DQRN Performance Analysis & Optimization Test

Detailed timing analysis to identify bottlenecks in training pipeline.
"""

import torch
import time
import cProfile
import pstats
import io
from players.dqrn_multi_head.training import DQRNTrainer, DQRNAgent, DutchCaboEnvironment
from src.game import Game
from players.simple_ai import SimpleAI


def time_function(func, *args, **kwargs):
    """Time a function execution"""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time


def profile_function(func, *args, **kwargs):
    """Profile a function with cProfile"""
    pr = cProfile.Profile()
    pr.enable()
    result = func(*args, **kwargs)
    pr.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    return result, s.getvalue()


def test_game_creation_speed():
    """Test how fast we can create games"""
    print("🎮 Testing Game Creation Speed...")
    
    # Test without neural networks
    times = []
    for i in range(100):
        start = time.time()
        player1 = SimpleAI("Player1")
        player2 = SimpleAI("Player2")
        game = Game([player1, player2], silent_mode=True)
        game.setup_new_game()
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    print(f"   Average game creation: {avg_time*1000:.2f}ms")
    print(f"   Games per second: {1/avg_time:.1f}")
    
    return avg_time


def test_neural_network_speed():
    """Test neural network inference speed"""
    print("🧠 Testing Neural Network Speed...")
    
    config = {"batch_size_override": 32}
    trainer = DQRNTrainer(config)
    
    # Test network creation
    start = time.time()
    agent = DQRNAgent(trainer.policy_net, trainer.hardware.device)
    creation_time = time.time() - start
    print(f"   Agent creation: {creation_time*1000:.2f}ms")
    
    # Test state building
    dummy_state = torch.randn(49).to(trainer.hardware.device)
    times = []
    for i in range(1000):
        start = time.time()
        with torch.no_grad():
            output = trainer.policy_net(dummy_state.unsqueeze(0))
        times.append(time.time() - start)
    
    avg_inference = sum(times) / len(times)
    print(f"   Average inference: {avg_inference*1000:.3f}ms")
    print(f"   Inferences per second: {1/avg_inference:.0f}")
    
    return creation_time, avg_inference


def test_experience_collection_speed():
    """Test experience collection bottlenecks"""
    print("💾 Testing Experience Collection...")
    
    config = {"batch_size_override": 32}
    trainer = DQRNTrainer(config)
    
    # Test 1: Single game timing
    print("   Testing single game...")
    start = time.time()
    stats = trainer.collect_experience(num_episodes=1)
    single_game_time = time.time() - start
    print(f"   Single game: {single_game_time:.3f}s")
    
    # Test 2: Multiple games
    print("   Testing batch games...")
    start = time.time()
    stats = trainer.collect_experience(num_episodes=10)
    batch_time = time.time() - start
    print(f"   10 games: {batch_time:.3f}s ({batch_time/10:.3f}s per game)")
    
    # Test 3: Profile the collection
    print("   Profiling experience collection...")
    _, profile_output = profile_function(trainer.collect_experience, num_episodes=5)
    
    # Extract key timing info
    lines = profile_output.split('\n')
    print("   Top time consumers:")
    for line in lines[5:15]:  # Skip header, show top 10
        if 'cumulative' not in line and line.strip():
            print(f"      {line}")
    
    return single_game_time, batch_time


def test_training_batch_speed():
    """Test training batch performance"""
    print("🎯 Testing Training Batch Speed...")
    
    config = {"batch_size_override": 32}
    trainer = DQRNTrainer(config)
    
    # Fill buffer with some dummy experiences first
    print("   Filling replay buffer...")
    trainer.collect_experience(num_episodes=20)
    
    if len(trainer.replay_buffer) < trainer.batch_size:
        print("   Not enough experiences for batch training")
        return 0
    
    # Test training speed
    print("   Testing training batches...")
    times = []
    for i in range(10):
        start = time.time()
        train_stats = trainer.train_batch()
        times.append(time.time() - start)
        
    avg_training_time = sum(times) / len(times)
    print(f"   Average training batch: {avg_training_time:.3f}s")
    print(f"   Batches per second: {1/avg_training_time:.1f}")
    
    # Profile one training batch
    print("   Profiling training batch...")
    _, profile_output = profile_function(trainer.train_batch)
    
    lines = profile_output.split('\n')
    print("   Training bottlenecks:")
    for line in lines[5:12]:  # Top training bottlenecks
        if 'cumulative' not in line and line.strip():
            print(f"      {line}")
    
    return avg_training_time


def test_memory_usage():
    """Test memory usage patterns"""
    print("🧠 Testing Memory Usage...")
    
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        initial_memory = torch.cuda.memory_allocated() / 1024**2
        
        config = {"batch_size_override": 32}
        trainer = DQRNTrainer(config)
        
        after_init = torch.cuda.memory_allocated() / 1024**2
        
        # Collect some experience
        trainer.collect_experience(num_episodes=10)
        after_collection = torch.cuda.memory_allocated() / 1024**2
        
        # Do some training
        if len(trainer.replay_buffer) >= trainer.batch_size:
            for _ in range(5):
                trainer.train_batch()
        
        after_training = torch.cuda.memory_allocated() / 1024**2
        peak_memory = torch.cuda.max_memory_allocated() / 1024**2
        
        print(f"   Initial: {initial_memory:.1f} MB")
        print(f"   After init: {after_init:.1f} MB (+{after_init-initial_memory:.1f})")
        print(f"   After collection: {after_collection:.1f} MB (+{after_collection-after_init:.1f})")
        print(f"   After training: {after_training:.1f} MB (+{after_training-after_collection:.1f})")
        print(f"   Peak memory: {peak_memory:.1f} MB")
        
    else:
        print("   CUDA not available - skipping GPU memory test")


def identify_bottlenecks():
    """Identify main performance bottlenecks"""
    print("\n🔍 PERFORMANCE ANALYSIS SUMMARY")
    print("=" * 50)
    
    # Test each component
    game_time = test_game_creation_speed()
    creation_time, inference_time = test_neural_network_speed()
    single_game, batch_game = test_experience_collection_speed()
    training_time = test_training_batch_speed()
    test_memory_usage()
    
    # Analysis
    print("\n📊 BOTTLENECK ANALYSIS:")
    
    # Calculate throughput estimates
    games_per_second = 1 / single_game if single_game > 0 else 0
    training_per_second = 1 / training_time if training_time > 0 else 0
    
    print(f"   Game throughput: {games_per_second:.1f} games/sec")
    print(f"   Training throughput: {training_per_second:.1f} batches/sec")
    
    # Identify bottlenecks
    bottlenecks = []
    
    if single_game > 1.0:  # Slow games
        bottlenecks.append(("Experience Collection", "Games taking >1s each"))
    
    if training_time > 0.1:  # Slow training
        bottlenecks.append(("Training Batches", "Batches taking >100ms"))
    
    if inference_time > 0.01:  # Slow inference
        bottlenecks.append(("Neural Network", "Inference taking >10ms"))
    
    if bottlenecks:
        print("\n⚠️  IDENTIFIED BOTTLENECKS:")
        for component, issue in bottlenecks:
            print(f"   - {component}: {issue}")
    else:
        print("\n✅ No major bottlenecks identified")
    
    return {
        "game_time": game_time,
        "inference_time": inference_time,
        "single_game": single_game,
        "training_time": training_time,
        "bottlenecks": bottlenecks
    }


def suggest_optimizations(analysis_results):
    """Suggest specific optimizations based on results"""
    print("\n💡 OPTIMIZATION SUGGESTIONS:")
    
    suggestions = []
    
    # Game speed optimizations
    if analysis_results["single_game"] > 0.5:
        suggestions.extend([
            "🎮 Reduce game complexity - limit turn count",
            "🔇 Ensure all prints are suppressed",
            "⚡ Use simpler opponent for training",
            "🚀 Implement game vectorization"
        ])
    
    # Neural network optimizations  
    if analysis_results["inference_time"] > 0.005:
        suggestions.extend([
            "🧠 Reduce network size for training",
            "⚡ Use mixed precision (FP16)",
            "🔀 Batch multiple inferences together"
        ])
    
    # Training optimizations
    if analysis_results["training_time"] > 0.05:
        suggestions.extend([
            "🎯 Increase batch size if memory allows",
            "📊 Reduce training frequency",
            "🔄 Use gradient accumulation"
        ])
    
    # General optimizations
    suggestions.extend([
        "🔁 Collect experience less frequently",
        "⚡ Use multiple workers for games",
        "💾 Optimize replay buffer operations",
        "📈 Adjust eval frequency to 200-500"
    ])
    
    for suggestion in suggestions:
        print(f"   {suggestion}")


def main():
    """Run complete performance analysis"""
    print("🚀 DQRN Performance Analysis Starting...")
    print("=" * 60)
    
    try:
        # Run analysis
        results = identify_bottlenecks()
        
        # Provide optimization suggestions
        suggest_optimizations(results)
        
        print(f"\n✅ Performance analysis completed!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main() 