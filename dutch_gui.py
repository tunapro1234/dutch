#!/usr/bin/env python3
"""
Dutch Cabo Card Game - Web GUI Launcher

Launches the React web interface with game mode selection.
Completely separate from the console version.
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
import signal


class DutchGUILauncher:
    """Launcher for Dutch Cabo Web GUI"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
    def check_dependencies(self):
        """Check if required dependencies are available"""
        print("🔍 Checking dependencies...")
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, check=True)
            node_version = result.stdout.strip()
            print(f"✅ Node.js found: {node_version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Node.js not found. Please install Node.js to use the web GUI.")
            print("   Download from: https://nodejs.org/")
            return False
        
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True, check=True)
            npm_version = result.stdout.strip()
            print(f"✅ npm found: {npm_version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ npm not found. Please install npm.")
            return False
        
        # Check Python dependencies
        try:
            import flask
            import flask_cors
            print(f"✅ Flask found: {flask.__version__}")
        except ImportError:
            print("❌ Flask not found. Installing...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'flask', 'flask-cors'], check=True)
                print("✅ Flask installed successfully")
            except subprocess.CalledProcessError:
                print("❌ Failed to install Flask. Please install manually:")
                print("   pip install flask flask-cors")
                return False
        
        return True
    
    def start_backend(self):
        """Start the backend API server"""
        print("🚀 Starting backend API server...")
        
        try:
            # Start backend server
            backend_script = os.path.join(self.project_root, 'game', 'api', 'server.py')
            print(f"   Starting: python {backend_script}")
            self.backend_process = subprocess.Popen(
                ['python', backend_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.project_root
            )
            
            # Wait a moment for server to start
            print("   Waiting for backend to start...")
            time.sleep(5)
            
            # Check if process is still running
            poll_result = self.backend_process.poll()
            if poll_result is not None:
                # Process has terminated
                stdout, stderr = self.backend_process.communicate()
                print(f"❌ Backend process terminated with code {poll_result}")
                if stdout:
                    print(f"   STDOUT: {stdout.decode()}")
                if stderr:
                    print(f"   STDERR: {stderr.decode()}")
                return False
            
            # Test if backend is running
            try:
                import requests
                response = requests.get('http://localhost:5001/api/health', timeout=5)
                if response.status_code == 200:
                    print("✅ Backend server started successfully on http://localhost:5001")
                    return True
                else:
                    print(f"❌ Backend server responded with status {response.status_code}")
                    return False
            except ImportError:
                # Try with curl if requests not available
                try:
                    result = subprocess.run(['curl', '-s', 'http://localhost:5001/api/health'], 
                                          capture_output=True, timeout=5)
                    if result.returncode == 0:
                        print("✅ Backend server started successfully on http://localhost:5001")
                        return True
                    else:
                        print("❌ Backend server not responding")
                        return False
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    print("❌ Backend server not responding")
                    return False
            except Exception as e:
                print(f"❌ Failed to test backend server: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start backend server: {e}")
            return False
    
    def setup_frontend(self):
        """Setup React frontend dependencies"""
        frontend_dir = os.path.join(self.project_root, 'game', 'js_gui')
        
        if not os.path.exists(frontend_dir):
            print("❌ Frontend directory not found. Please make sure game/js_gui exists.")
            return False
        
        print("📦 Setting up React frontend...")
        
        try:
            # Install npm dependencies
            print("   Installing npm dependencies...")
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print("✅ Frontend dependencies installed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install frontend dependencies: {e}")
            return False
    
    def start_frontend(self):
        """Start the React frontend"""
        frontend_dir = os.path.join(self.project_root, 'game', 'js_gui')
        
        print("🎮 Starting React frontend...")
        
        try:
            # Set environment variable for API URL
            env = os.environ.copy()
            env['REACT_APP_API_URL'] = 'http://localhost:5001'
            env['BROWSER'] = 'none'  # Prevent npm from opening browser automatically
            
            # Start React development server
            self.frontend_process = subprocess.Popen(
                ['npm', 'start'],
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for React to start
            print("   Waiting for React server to start...")
            time.sleep(8)  # React takes a bit longer to start
            
            print("✅ React frontend started on http://localhost:3000")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start React frontend: {e}")
            return False
    
    def open_browser(self):
        """Open the web browser to the game"""
        print("🌐 Opening web browser...")
        try:
            webbrowser.open('http://localhost:3000')
            print("✅ Browser opened successfully")
        except Exception as e:
            print(f"⚠️ Could not open browser automatically: {e}")
            print("   Please open http://localhost:3000 manually")
    
    def cleanup(self):
        """Clean up processes"""
        print("\n🧹 Cleaning up...")
        
        if self.frontend_process:
            print("   Stopping React frontend...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
        
        if self.backend_process:
            print("   Stopping backend server...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        
        print("✅ Cleanup completed")
    
    def run(self):
        """Main launcher method"""
        print("🃏 Dutch Cabo Web GUI Launcher")
        print("=" * 50)
        
        try:
            # Check dependencies
            if not self.check_dependencies():
                return 1
            
            print()
            
            # Start backend
            if not self.start_backend():
                return 1
            
            print()
            
            # Setup frontend
            if not self.setup_frontend():
                self.cleanup()
                return 1
            
            print()
            
            # Start frontend
            if not self.start_frontend():
                self.cleanup()
                return 1
            
            print()
            
            # Open browser
            self.open_browser()
            
            print()
            print("🎉 Dutch Cabo Web GUI is now running!")
            print("=" * 50)
            print("🌐 Frontend: http://localhost:3000")
            print("🔧 Backend:  http://localhost:5001")
            print()
            print("Choose your game mode in the web interface:")
            print("• 🤖 AI vs AI - Watch AI players compete")
            print("• 🎯 Human vs AI - Play against AI")
            print("• 🎭 Human vs Human - Play with friends")
            print("• 🎮 Real Life Mode - Use as game assistant")
            print()
            print("Press Ctrl+C to stop the servers")
            
            # Wait for user to stop
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Shutting down...")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return 1
        
        finally:
            self.cleanup()
        
        return 0


def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print("\n🛑 Received interrupt signal")
    sys.exit(0)


def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    launcher = DutchGUILauncher()
    return launcher.run()


if __name__ == "__main__":
    sys.exit(main()) 