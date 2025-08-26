#!/usr/bin/env python3
"""
Cross-Platform Setup Script for Growth System v2
Handles installation, testing, and UI launch on Windows, macOS, and Linux
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import json

class CrossPlatformSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
        self.is_windows = platform.system() == "Windows"
        self.is_mac = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"
        
        # OS-specific paths and commands
        if self.is_windows:
            self.python_cmd = "python"
            self.pip_cmd = "venv\\Scripts\\pip"
            self.python_venv_cmd = "venv\\Scripts\\python"
            self.activate_cmd = "venv\\Scripts\\activate.bat"
        else:
            self.python_cmd = "python3"
            self.pip_cmd = "venv/bin/pip"
            self.python_venv_cmd = "venv/bin/python"
            self.activate_cmd = "source venv/bin/activate"

    def print_header(self):
        """Display setup header with OS detection"""
        print("🚀 Growth System v2 - Cross-Platform Setup")
        print("=" * 50)
        print(f"📱 Operating System: {platform.system()} {platform.release()}")
        print(f"🐍 Python Version: {sys.version}")
        print(f"📁 Project Directory: {self.project_root}")
        print("=" * 50)
        print()

    def check_python_version(self):
        """Verify Python version meets requirements (3.12+)"""
        print("🔍 Checking Python version...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 12):
            print(f"❌ Error: Python 3.12+ required, found {version.major}.{version.minor}")
            print("Please upgrade Python and try again.")
            sys.exit(1)
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Version OK")
        print()

    def check_python_executable(self):
        """Verify Python executable is available"""
        print("🔍 Checking Python executable...")
        if shutil.which(self.python_cmd):
            print(f"✅ Python executable found: {self.python_cmd}")
        else:
            print(f"❌ Error: {self.python_cmd} not found in PATH")
            print("Please ensure Python is installed and in your PATH")
            sys.exit(1)
        print()

    def create_virtual_environment(self):
        """Create virtual environment if it doesn't exist"""
        print("📦 Setting up virtual environment...")
        
        if self.venv_path.exists():
            print("✅ Virtual environment already exists")
        else:
            print("🔧 Creating new virtual environment...")
            try:
                subprocess.run([self.python_cmd, "-m", "venv", "venv"], 
                             check=True, capture_output=True, text=True)
                print("✅ Virtual environment created successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error creating virtual environment: {e}")
                sys.exit(1)
        print()

    def install_dependencies(self):
        """Install all required dependencies"""
        print("📚 Installing dependencies...")
        
        if not self.requirements_file.exists():
            print("❌ Error: requirements.txt not found")
            sys.exit(1)
        
        try:
            # Upgrade pip first
            print("⬆️ Upgrading pip...")
            subprocess.run([self.pip_cmd, "install", "--upgrade", "pip"], 
                         check=True, capture_output=True, text=True)
            
            # Install requirements
            print("📦 Installing project dependencies...")
            subprocess.run([self.pip_cmd, "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True, text=True)
            
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing dependencies: {e}")
            print("This might be due to network issues or package conflicts.")
            print("Try running manually: pip install -r requirements.txt")
            sys.exit(1)
        print()

    def run_tests(self):
        """Run the test suite to verify installation"""
        print("🧪 Running test suite...")
        
        try:
            # Run tests with the virtual environment Python
            result = subprocess.run([self.python_venv_cmd, "-m", "pytest", "tests/", "-q"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ All tests passed!")
                # Extract test summary if available
                if "passed" in result.stdout:
                    print(f"📊 Test Results: {result.stdout.strip()}")
            else:
                print("⚠️ Some tests failed, but continuing with setup...")
                print(f"Test output: {result.stdout}")
                if result.stderr:
                    print(f"Test errors: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Could not run tests: {e}")
            print("Continuing with setup...")
        print()

    def launch_ui(self):
        """Launch the Streamlit UI"""
        print("🎯 Launching Growth System UI...")
        print("🌐 The UI will open in your default web browser")
        print("📍 URL: http://localhost:8501")
        print("⏹️ Press Ctrl+C to stop the UI when done")
        print()
        
        try:
            # Launch Streamlit UI
            subprocess.run([self.python_venv_cmd, "-m", "streamlit", "run", "ui/app.py"])
        except KeyboardInterrupt:
            print("\n👋 UI stopped by user")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error launching UI: {e}")
            print("Try running manually: streamlit run ui/app.py")
        except FileNotFoundError:
            print("❌ Error: UI files not found")
            print("Make sure you're running from the project root directory")

    def run_full_setup(self):
        """Run the complete setup process"""
        try:
            self.print_header()
            self.check_python_version()
            self.check_python_executable()
            self.create_virtual_environment()
            self.install_dependencies()
            self.run_tests()
            
            print("🎉 Setup completed successfully!")
            print()
            print("Next steps:")
            print("1. The UI will launch automatically")
            print("2. To run the UI again later: python setup_cross_platform.py --ui-only")
            print("3. To run tests: python setup_cross_platform.py --test-only")
            print("4. To reinstall dependencies: python setup_cross_platform.py --install-only")
            print()
            
            # Ask user if they want to launch UI
            if input("🚀 Launch the UI now? (y/n): ").lower().startswith('y'):
                self.launch_ui()
            else:
                print("✅ Setup complete! Run 'python setup_cross_platform.py --ui-only' to launch the UI later.")
                
        except Exception as e:
            print(f"❌ Unexpected error during setup: {e}")
            print("Please check the error messages above and try again.")
            sys.exit(1)

    def run_ui_only(self):
        """Launch only the UI (for subsequent runs)"""
        self.print_header()
        print("🎯 Launching UI only...")
        self.launch_ui()

    def run_test_only(self):
        """Run only the tests"""
        self.print_header()
        print("🧪 Running tests only...")
        self.check_python_executable()
        self.run_tests()

    def run_install_only(self):
        """Run only the installation"""
        self.print_header()
        print("📦 Running installation only...")
        self.check_python_version()
        self.check_python_executable()
        self.create_virtual_environment()
        self.install_dependencies()

def main():
    """Main entry point with command line argument handling"""
    setup = CrossPlatformSetup()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "--ui-only":
            setup.run_ui_only()
        elif arg == "--test-only":
            setup.run_test_only()
        elif arg == "--install-only":
            setup.run_install_only()
        elif arg in ["--help", "-h"]:
            print("Growth System v2 - Cross-Platform Setup")
            print()
            print("Usage:")
            print("  python setup_cross_platform.py           # Full setup and launch UI")
            print("  python setup_cross_platform.py --ui-only     # Launch UI only")
            print("  python setup_cross_platform.py --test-only   # Run tests only")
            print("  python setup_cross_platform.py --install-only # Install dependencies only")
            print("  python setup_cross_platform.py --help         # Show this help")
        else:
            print(f"❌ Unknown argument: {arg}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        # No arguments - run full setup
        setup.run_full_setup()

if __name__ == "__main__":
    main()
