#!/usr/bin/env python3
"""
Automatic Requirements Installer
Installs all required packages with error handling and fallback options
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(command, description=""):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ FAILED: {description}")
            print(f"Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {description} took too long")
        return False
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠️  WARNING: Python 3.8+ is recommended for best compatibility")
        return False
    return True

def upgrade_pip():
    """Upgrade pip to latest version"""
    commands = [
        f"{sys.executable} -m pip install --upgrade pip",
        f"{sys.executable} -m pip install --upgrade setuptools wheel"
    ]
    
    for cmd in commands:
        if not run_command(cmd, "Upgrading pip and setuptools"):
            return False
    return True

def create_requirements_file():
    """Create requirements.txt file if it doesn't exist"""
    requirements_content = """# FastAPI Backend
fastapi
uvicorn
python-multipart

# Voice Input and Audio Playback
pygame==2.6.1
sounddevice==0.4.6
pyaudio

# Speech Recognition and Text-to-Speech
ffmpeg-python==0.2.0
openai-whisper
pyttsx3

# NLP & Intent Detection
transformers==4.40.0
torch==2.3.0
wit==4.2.0
openai
scikit-learn

# Spotify API
spotipy==2.25.1

# Environment Variables
python-dotenv==1.0.1

# Data Handling & Utilities
numpy==1.26.4
requests==2.31.0
pymongo==4.6.3
python-dateutil

# Calendar & External API Integration
google-api-python-client==2.122.0

# Notifications
plyer

# Testing and Debugging (Optional)
ipython==8.24.0
rich==13.7.1"""

    req_file = Path("/Users/user/chapo-bot-backend/backend/requirements.txt")
    if not req_file.exists():
        print("📝 Creating requirements.txt file...")
        with open(req_file, "w") as f:
            f.write(requirements_content)
        print("✅ requirements.txt created successfully!")
    else:
        print("📄 requirements.txt already exists")
    
    return True

def install_system_dependencies():
    """Install system dependencies based on OS"""
    system = platform.system().lower()
    
    if system == "linux":
        print("🐧 Detected Linux system")
        # Common Linux dependencies
        deps = [
            "sudo apt-get update",
            "sudo apt-get install -y python3-dev python3-pip",
            "sudo apt-get install -y portaudio19-dev python3-pyaudio",
            "sudo apt-get install -y ffmpeg",
            "sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev"
        ]
        
        for dep in deps:
            run_command(dep, f"Installing Linux dependency: {dep.split()[-1]}")
            
    elif system == "darwin":  # macOS
        print("🍎 Detected macOS system")
        # Check if Homebrew is installed
        if run_command("which brew", "Checking for Homebrew"):
            deps = [
                "brew install portaudio",
                "brew install ffmpeg",
                "brew install espeak"
            ]
            for dep in deps:
                run_command(dep, f"Installing macOS dependency: {dep.split()[-1]}")
        else:
            print("⚠️  Homebrew not found. Please install Homebrew first:")
            print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            
    elif system == "windows":
        print("🪟 Detected Windows system")
        print("⚠️  For Windows, you may need to install:")
        print("   - Microsoft Visual C++ Build Tools")
        print("   - FFmpeg (add to PATH)")
        print("   - Consider using conda for pyaudio installation")

def install_problematic_packages():
    """Install packages that commonly cause issues with special handling"""
    problematic_packages = {
        "pyaudio": [
            f"{sys.executable} -m pip install pyaudio",
            f"{sys.executable} -m pip install --only-binary=all pyaudio",
        ],
        "openai-whisper": [
            f"{sys.executable} -m pip install openai-whisper",
            f"{sys.executable} -m pip install git+https://github.com/openai/whisper.git",
        ],
        "torch": [
            f"{sys.executable} -m pip install torch==2.3.0",
            f"{sys.executable} -m pip install torch --index-url https://download.pytorch.org/whl/cpu",
        ]
    }
    
    for package, commands in problematic_packages.items():
        print(f"\n🎯 Installing {package} with fallback options...")
        success = False
        
        for i, cmd in enumerate(commands, 1):
            print(f"   Attempt {i}/{len(commands)}")
            if run_command(cmd, f"Installing {package} (method {i})"):
                success = True
                break
        
        if not success:
            print(f"❌ Failed to install {package}. You may need to install it manually.")

def main():
    """Main installation process"""
    print("🚀 AUTOMATIC REQUIREMENTS INSTALLER")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        print("⚠️  Continuing anyway, but some packages might not work...")
    
    # Create requirements.txt if needed
    create_requirements_file()
    
    # Upgrade pip
    if not upgrade_pip():
        print("⚠️  Pip upgrade failed, continuing anyway...")
    
    # Install system dependencies
    install_system_dependencies()
    
    # Try installing problematic packages first
    install_problematic_packages()
    
    # Install all requirements
    print("\n🎯 Installing all requirements from requirements.txt...")
    success = run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing all requirements"
    )
    
    if not success:
        print("\n🔄 Trying alternative installation method...")
        run_command(
            f"{sys.executable} -m pip install -r requirements.txt --no-cache-dir --force-reinstall",
            "Installing with no cache and force reinstall"
        )
    
    # Install Whisper via git as fallback
    print("\n🎵 Installing Whisper via git (fallback method)...")
    run_command(
        f"{sys.executable} -m pip install git+https://github.com/openai/whisper.git",
        "Installing Whisper from GitHub"
    )
    
    # Final verification
    print("\n🔍 INSTALLATION SUMMARY")
    print("=" * 60)
    
    # Test imports
    test_packages = [
        "fastapi", "uvicorn", "pygame", "sounddevice", "transformers", 
        "torch", "spotipy", "pymongo", "openai", "whisper"
    ]
    
    successful_imports = []
    failed_imports = []
    
    for package in test_packages:
        try:
            __import__(package)
            successful_imports.append(package)
            print(f"✅ {package}")
        except ImportError:
            failed_imports.append(package)
            print(f"❌ {package}")
    
    print(f"\n📊 RESULTS:")
    print(f"✅ Successfully installed: {len(successful_imports)}/{len(test_packages)} packages")
    
    if failed_imports:
        print(f"❌ Failed packages: {', '.join(failed_imports)}")
        print(f"\n🛠️  MANUAL INSTALLATION COMMANDS:")
        for pkg in failed_imports:
            print(f"   pip install {pkg}")
    else:
        print("🎉 ALL PACKAGES INSTALLED SUCCESSFULLY!")
    
    print(f"\n💡 If you encounter issues:")
    print(f"   1. Try running as administrator/sudo")
    print(f"   2. Use conda instead of pip for problematic packages")
    print(f"   3. Install system dependencies manually")
    print(f"   4. Check Python version compatibility")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
