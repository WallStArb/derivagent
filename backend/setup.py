#!/usr/bin/env python3
"""
Setup script for Derivagent backend
Installs required dependencies and validates the setup
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Derivagent Backend...")
    
    # Essential packages for basic functionality
    essential_packages = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "pydantic==2.5.1",
        "python-dotenv==1.0.0",
        "httpx==0.25.2"
    ]
    
    print("📦 Installing essential packages...")
    for package in essential_packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ Failed to install {package}")
    
    # Try to install LiteLLM (may fail due to dependencies)
    print("\n🤖 Installing AI packages...")
    ai_packages = [
        "litellm==1.17.9",
        "openai==1.3.7"
    ]
    
    for package in ai_packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"⚠️  {package} installation failed - may need system dependencies")
    
    print("\n🎯 Setup complete! Check the output above for any failed installations.")

if __name__ == "__main__":
    main()