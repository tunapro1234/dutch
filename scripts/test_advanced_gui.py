#!/usr/bin/env python3
"""
Test script for Dutch Cabo Advanced GUI
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from game.modes.advanced_gui import advanced_gui_mode, check_requirements

def main():
    print("🧪 Testing Dutch Cabo Advanced GUI")
    print("=" * 40)
    
    # Check system requirements
    print("1. Checking system requirements...")
    missing = check_requirements()
    
    if missing:
        print("❌ Missing requirements:")
        for req in missing:
            print(f"   • {req}")
        print()
        print("💡 Install Node.js and npm:")
        print("   https://nodejs.org/")
        return False
    else:
        print("✅ All requirements satisfied")
    
    print()
    print("2. Directory structure check...")
    
    # Check if React app exists
    project_root = Path(__file__).parent.parent
    js_gui_path = project_root / "game" / "js_gui"
    
    print(f"   React app path: {js_gui_path}")
    
    if js_gui_path.exists():
        print("✅ React app directory found")
        
        # Check key files
        files_to_check = [
            "package.json",
            "src/App.js",
            "src/components/Card.js",
            "src/components/GameBoard.js",
            "public/index.html"
        ]
        
        for file_path in files_to_check:
            full_path = js_gui_path / file_path
            if full_path.exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path}")
    else:
        print("❌ React app directory not found")
        return False
    
    print()
    print("3. Backend API check...")
    
    # Check if API module exists
    api_path = project_root / "game" / "api" / "server.py"
    if api_path.exists():
        print("✅ Backend API found")
    else:
        print("❌ Backend API not found")
    
    print()
    print("🚀 Ready to launch advanced GUI!")
    print()
    
    # Ask user if they want to launch
    response = input("Launch advanced GUI now? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print()
        advanced_gui_mode()
    else:
        print("💡 To launch manually:")
        print("   python dutch.py --mode advanced-gui")
        print("   or")
        print("   python dutch.py  # then choose option 9")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1) 