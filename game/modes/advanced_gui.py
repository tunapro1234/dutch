"""
Advanced GUI Mode - React-based web interface
"""

import sys
import os
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def check_requirements():
    """Check if required tools are available"""
    requirements = {
        'node': 'Node.js is required for React app',
        'npm': 'npm is required for React dependencies'
    }
    
    missing = []
    for cmd, desc in requirements.items():
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(desc)
    
    return missing


def start_backend_server():
    """Start the Python backend API server"""
    try:
        from game.api.server import run_server
        print("🚀 Starting backend API server...")
        
        # Run in separate thread
        server_thread = threading.Thread(
            target=run_server, 
            kwargs={'host': 'localhost', 'port': 5000, 'debug': False},
            daemon=True
        )
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        return True
        
    except ImportError as e:
        print(f"❌ Backend server error: {e}")
        print("💡 Install Flask: pip install flask flask-cors")
        return False
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False


def install_react_dependencies(js_gui_path):
    """Install React dependencies"""
    print("📦 Installing React dependencies...")
    
    try:
        result = subprocess.run(
            ['npm', 'install'],
            cwd=js_gui_path,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ npm install failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ npm install timed out - dependencies may be installing")
        return True  # Continue anyway
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def start_react_app(js_gui_path):
    """Start the React development server"""
    print("🌐 Starting React app...")
    
    try:
        # Start React dev server
        process = subprocess.Popen(
            ['npm', 'start'],
            cwd=js_gui_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for React to start
        print("⏳ Waiting for React app to start...")
        time.sleep(5)
        
        # Open browser
        react_url = "http://localhost:3000"
        print(f"🌐 Opening browser: {react_url}")
        webbrowser.open(react_url)
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start React app: {e}")
        return None


def advanced_gui_mode():
    """Launch React-based advanced GUI"""
    print("🎮 Dutch Cabo - Advanced GUI Mode")
    print("=" * 50)
    print("Starting React-based web interface...")
    print()
    
    # Check requirements
    missing = check_requirements()
    if missing:
        print("❌ Missing requirements:")
        for req in missing:
            print(f"  • {req}")
        print()
        print("💡 Install Node.js and npm first:")
        print("   https://nodejs.org/")
        return
    
    # Find js_gui directory
    current_dir = Path(__file__).parent.parent
    js_gui_path = current_dir / "js_gui"
    
    if not js_gui_path.exists():
        print(f"❌ React app directory not found: {js_gui_path}")
        return
    
    print(f"📁 React app location: {js_gui_path}")
    
    # Check if node_modules exists
    node_modules = js_gui_path / "node_modules"
    if not node_modules.exists():
        print("📦 Node modules not found, installing dependencies...")
        if not install_react_dependencies(js_gui_path):
            print("❌ Failed to install dependencies")
            return
    
    # Start backend server
    if not start_backend_server():
        print("⚠️ Backend server failed, React app will run in demo mode")
    
    # Start React app
    react_process = start_react_app(js_gui_path)
    
    if react_process:
        print("✅ Advanced GUI launched successfully!")
        print()
        print("🎯 Game Interface:")
        print("   Frontend: http://localhost:3000")
        print("   Backend:  http://localhost:5000")
        print()
        print("📋 Instructions:")
        print("   • The React app should open in your browser")
        print("   • Beautiful card rendering with animations")
        print("   • Real-time game state updates")
        print("   • Mobile-responsive design")
        print()
        print("🛑 Press Ctrl+C to stop the servers")
        
        try:
            # Keep the script running
            while True:
                time.sleep(1)
                # Check if React process is still running
                if react_process.poll() is not None:
                    print("⚠️ React app stopped")
                    break
                    
        except KeyboardInterrupt:
            print("\n🛑 Stopping servers...")
            
            # Terminate React process
            if react_process:
                react_process.terminate()
                try:
                    react_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    react_process.kill()
            
            print("✅ Servers stopped")
    
    else:
        print("❌ Failed to launch advanced GUI")
        print("💡 Try running manually:")
        print(f"   cd {js_gui_path}")
        print("   npm install")
        print("   npm start")


def quick_demo():
    """Quick demo without full setup"""
    print("🎮 Advanced GUI Demo")
    print("=" * 30)
    
    # Just open the static demo
    demo_html = Path(__file__).parent.parent / "js_gui" / "public" / "index.html"
    
    if demo_html.exists():
        print(f"📂 Opening demo: {demo_html}")
        webbrowser.open(f"file://{demo_html.absolute()}")
    else:
        print("❌ Demo file not found")
        print("💡 Use --mode advanced-gui for full React app")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dutch Cabo Advanced GUI")
    parser.add_argument("--demo", action="store_true", help="Quick demo mode")
    
    args = parser.parse_args()
    
    if args.demo:
        quick_demo()
    else:
        advanced_gui_mode() 