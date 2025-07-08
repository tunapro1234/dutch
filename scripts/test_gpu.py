#!/usr/bin/env python3
"""
PyTorch GPU test and benchmark script.
"""

import torch
import time
import numpy as np


def test_cuda_availability():
    """Test basic CUDA availability"""
    print("🔧 PyTorch GPU Test")
    print("=" * 50)
    
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Device count: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            print(f"Device {i}: {torch.cuda.get_device_name(i)}")
            print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.1f} GB")
            print(f"  Capability: {torch.cuda.get_device_properties(i).major}.{torch.cuda.get_device_properties(i).minor}")
        
        return True
    else:
        print("❌ CUDA not available!")
        return False


def benchmark_operations():
    """Benchmark basic operations on CPU vs GPU"""
    if not torch.cuda.is_available():
        print("Skipping GPU benchmark - CUDA not available")
        return
    
    print("\n🚀 Performance Benchmark")
    print("=" * 50)
    
    # Test sizes
    sizes = [1000, 5000, 10000]
    
    for size in sizes:
        print(f"\nMatrix size: {size}x{size}")
        
        # Create test data
        a_cpu = torch.randn(size, size)
        b_cpu = torch.randn(size, size)
        
        a_gpu = a_cpu.cuda()
        b_gpu = b_cpu.cuda()
        
        # CPU benchmark
        torch.cuda.synchronize()  # Ensure GPU operations are finished
        start_time = time.time()
        c_cpu = torch.mm(a_cpu, b_cpu)
        cpu_time = time.time() - start_time
        
        # GPU benchmark
        torch.cuda.synchronize()
        start_time = time.time()
        c_gpu = torch.mm(a_gpu, b_gpu)
        torch.cuda.synchronize()
        gpu_time = time.time() - start_time
        
        # Results
        speedup = cpu_time / gpu_time
        print(f"  CPU time: {cpu_time:.4f}s")
        print(f"  GPU time: {gpu_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x")
        
        # Verify results match
        diff = torch.max(torch.abs(c_cpu - c_gpu.cpu())).item()
        print(f"  Max difference: {diff:.2e}")


def test_memory_usage():
    """Test GPU memory usage"""
    if not torch.cuda.is_available():
        return
    
    print("\n💾 GPU Memory Test")
    print("=" * 50)
    
    # Clear cache
    torch.cuda.empty_cache()
    
    # Initial memory
    memory_allocated = torch.cuda.memory_allocated() / 1e6
    memory_reserved = torch.cuda.memory_reserved() / 1e6
    print(f"Initial - Allocated: {memory_allocated:.1f} MB, Reserved: {memory_reserved:.1f} MB")
    
    # Allocate some tensors
    tensors = []
    for i in range(10):
        tensor = torch.randn(1000, 1000).cuda()
        tensors.append(tensor)
        
        memory_allocated = torch.cuda.memory_allocated() / 1e6
        memory_reserved = torch.cuda.memory_reserved() / 1e6
        print(f"After tensor {i+1} - Allocated: {memory_allocated:.1f} MB, Reserved: {memory_reserved:.1f} MB")
    
    # Clear tensors
    del tensors
    torch.cuda.empty_cache()
    
    memory_allocated = torch.cuda.memory_allocated() / 1e6
    memory_reserved = torch.cuda.memory_reserved() / 1e6
    print(f"After cleanup - Allocated: {memory_allocated:.1f} MB, Reserved: {memory_reserved:.1f} MB")


def test_neural_network():
    """Test a simple neural network on GPU"""
    if not torch.cuda.is_available():
        return
    
    print("\n🧠 Neural Network Test")
    print("=" * 50)
    
    # Simple neural network
    class SimpleNet(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = torch.nn.Sequential(
                torch.nn.Linear(784, 256),
                torch.nn.ReLU(),
                torch.nn.Linear(256, 128),
                torch.nn.ReLU(),
                torch.nn.Linear(128, 10)
            )
        
        def forward(self, x):
            return self.layers(x)
    
    # Create model and move to GPU
    model = SimpleNet().cuda()
    print(f"Model created with {sum(p.numel() for p in model.parameters())} parameters")
    
    # Test data
    batch_size = 64
    x = torch.randn(batch_size, 784).cuda()
    
    # Forward pass
    start_time = time.time()
    with torch.no_grad():
        output = model(x)
    forward_time = time.time() - start_time
    
    print(f"Forward pass: {forward_time:.4f}s")
    print(f"Output shape: {output.shape}")
    print(f"Output device: {output.device}")
    
    # Test training step
    optimizer = torch.optim.Adam(model.parameters())
    criterion = torch.nn.CrossEntropyLoss()
    target = torch.randint(0, 10, (batch_size,)).cuda()
    
    start_time = time.time()
    optimizer.zero_grad()
    output = model(x)
    loss = criterion(output, target)
    loss.backward()
    optimizer.step()
    training_time = time.time() - start_time
    
    print(f"Training step: {training_time:.4f}s")
    print(f"Loss: {loss.item():.4f}")


def main():
    """Run all GPU tests"""
    try:
        # Basic CUDA test
        cuda_available = test_cuda_availability()
        
        if cuda_available:
            # Performance benchmarks
            benchmark_operations()
            
            # Memory usage test
            test_memory_usage()
            
            # Neural network test
            test_neural_network()
            
            print("\n✅ All GPU tests completed successfully!")
            print("\n🎮 Your RTX 3070 Laptop GPU is ready for RL training!")
        else:
            print("\n❌ GPU tests skipped - CUDA not available")
    
    except Exception as e:
        print(f"\n❌ Error during GPU testing: {e}")


if __name__ == "__main__":
    main() 