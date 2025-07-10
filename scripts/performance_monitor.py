#!/usr/bin/env python3
"""
GPU Performance Monitor for DQRN Training

Monitors GPU utilization, memory usage, and training metrics in real-time.
"""

import time
import subprocess
import json
import threading
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.monitoring = False
        self.stats = []
    
    def get_gpu_stats(self):
        """Get current GPU statistics"""
        try:
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                values = result.stdout.strip().split(', ')
                return {
                    'gpu_util': int(values[0]),
                    'memory_used': int(values[1]),
                    'memory_total': int(values[2]),
                    'temperature': int(values[3]),
                    'power_draw': float(values[4])
                }
        except Exception as e:
            print(f"Error getting GPU stats: {e}")
        return None
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            stats = self.get_gpu_stats()
            if stats:
                stats['timestamp'] = datetime.now().isoformat()
                self.stats.append(stats)
                
                # Real-time display
                memory_usage = (stats['memory_used'] / stats['memory_total']) * 100
                print(f"\r🔥 GPU: {stats['gpu_util']:2d}% | VRAM: {memory_usage:4.1f}% ({stats['memory_used']:4d}MB) | Temp: {stats['temperature']:2d}°C | Power: {stats['power_draw']:4.1f}W", end="", flush=True)
            
            time.sleep(2)  # Update every 2 seconds
    
    def start_monitoring(self):
        """Start monitoring in background thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🖥️ GPU Performance Monitor started...")
    
    def stop_monitoring(self):
        """Stop monitoring and save stats"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=1)
        
        print("\n📊 Performance Summary:")
        if self.stats:
            avg_gpu_util = sum(s['gpu_util'] for s in self.stats) / len(self.stats)
            max_gpu_util = max(s['gpu_util'] for s in self.stats)
            avg_memory = sum(s['memory_used'] for s in self.stats) / len(self.stats)
            max_memory = max(s['memory_used'] for s in self.stats)
            
            print(f"   Average GPU Utilization: {avg_gpu_util:.1f}%")
            print(f"   Peak GPU Utilization: {max_gpu_util}%")
            print(f"   Average VRAM Usage: {avg_memory:.0f}MB")
            print(f"   Peak VRAM Usage: {max_memory}MB")
            
            # Save detailed stats
            with open(f"gpu_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                json.dump(self.stats, f, indent=2)
            print(f"   📁 Detailed stats saved to file")

if __name__ == "__main__":
    monitor = PerformanceMonitor()
    try:
        monitor.start_monitoring()
        input("Press Enter to stop monitoring...")
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop_monitoring()
