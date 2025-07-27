#!/usr/bin/env python3
"""
InternMailer Setup Script
Helps users set up the application with proper configuration
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🚀 InternMailer Setup Script")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_env_file():
    """Create .env file with user input"""
    print("\n🔐 Setting up Gmail configuration...")
    
    if os.path.exists('.env'):
        response = input("📝 .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("⏭️ Skipping .env file creation")
            return True
    
    print("\nTo use Gmail SMTP, you need:")
    print("1. Your Gmail address")
    print("2. An App Password (NOT your regular Gmail password)")
    print("   Generate at: https://myaccount.google.com/apppasswords")
    print()
    
    gmail_user = input("Enter your Gmail address: ").strip()
    if not gmail_user or '@' not in gmail_user:
        print("❌ Invalid email address")
        return False
    
    gmail_password = input("Enter your Gmail App Password: ").strip()
    if not gmail_password:
        print("❌ App password is required")
        return False
    
    env_content = f"""# Gmail Configuration for InternMailer
GMAIL_USER={gmail_user}
GMAIL_APP_PASSWORD={gmail_password}

# Optional: Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest

# Optional: Rate limiting (emails per hour)
EMAIL_RATE_LIMIT=50

# Optional: Testing mode (set to true to skip actual email sending)
TEST_MODE=false
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully")
    return True

def check_data_files():
    """Check if required data files exist"""
    print("\n📊 Checking data files...")
    
    data_dir = Path("InternMailer/data")
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print("📁 Created data directory")
    
    csv_file = data_dir / "proffesor.csv"
    if not csv_file.exists():
        print("⚠️  Professor CSV file not found")
        print(f"   Expected location: {csv_file}")
        print("   You can:")
        print("   1. Use the existing file if you have professor data")
        print("   2. Run the scraping scripts to generate data")
        return False
    else:
        print("✅ Professor CSV file found")
        return True

def check_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "resumes",
        "logs",
        "InternMailer/data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory: {directory}")

def check_ollama():
    """Check if Ollama is available"""
    print("\n🤖 Checking Ollama server...")
    try:
        import requests
        response = requests.get("http://localhost:11434", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            return True
    except:
        pass
    
    print("⚠️  Ollama server not detected")
    print("   For AI-powered email generation:")
    print("   1. Install Ollama: https://ollama.ai")
    print("   2. Run: ollama pull gemma3")
    print("   3. Start: ollama serve")
    print("   (Email templates will be used as fallback)")
    return False

def run_setup():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create directories
    check_directories()
    
    # Setup environment
    if not create_env_file():
        return False
    
    # Check data files
    check_data_files()
    
    # Check Ollama
    check_ollama()
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Ensure your professor CSV file is in InternMailer/data/proffesor.csv")
    print("2. Upload your resume PDF to the resumes/ directory")
    print("3. Run the application:")
    print("   cd InternMailer")
    print("   streamlit run app.py")
    print("\n💡 For help: Check the README.md file")
    
    return True

if __name__ == "__main__":
    try:
        success = run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
