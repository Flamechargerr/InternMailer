"""
InternMailer - Automated Setup Script
Quick setup for full automation system
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    print("📦 Checking dependencies...")
    
    required = ['schedule', 'flask', 'dnspython', 'pyyaml', 'python-dotenv']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Missing packages: {', '.join(missing)}")
        print(f"   Run: pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies installed\n")
    return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    print("🔐 Checking .env file...")
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("   ❌ .env file not found")
        print("\n   Creating .env template...")
        
        with open('.env', 'w') as f:
            f.write("""# InternMailer Environment Variables

# Your Gmail address
EMAIL_ADDRESS=your_email@gmail.com

# Gmail App Password (NOT your regular password)
# Create at: https://myaccount.google.com/apppasswords
EMAIL_PASSWORD=your_16_char_app_password_here

# Gemini API Key (if using AI features)
GEMINI_API_KEY=your_gemini_key_here

# Unsubscribe secret key
UNSUBSCRIBE_SECRET_KEY=random_secret_key_here
""")
        
        print("   ✅ Created .env template")
        print("   ⚠️ Please edit .env and add your credentials!")
        return False
    
    # Check if configured
    from dotenv import load_dotenv
    load_dotenv()
    
    email = os.getenv('EMAIL_ADDRESS')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not email or email == 'your_email@gmail.com':
        print("   ❌ EMAIL_ADDRESS not configured in .env")
        return False
    
    if not password or password == 'your_16_char_app_password_here':
        print("   ❌ EMAIL_PASSWORD not configured in .env")
        print("   Create Gmail App Password at: https://myaccount.google.com/apppasswords")
        return False
    
    print("   ✅ .env file configured")
    return True

def test_system():
    """Run a quick test of the automation system"""
    print("\n🧪 Testing automation system...\n")
    
    try:
        # Test inbox monitor
        print("1. Testing inbox monitor...")
        from inbox_monitor import get_inbox_monitor
        monitor = get_inbox_monitor()
        print("   ✅ Inbox monitor ready")
        
        # Test action engine
        print("2. Testing action engine...")
        from auto_action_engine import get_auto_action_engine
        engine = get_auto_action_engine()
        print("   ✅ Action engine ready")
        
        # Test follow-up scheduler
        print("3. Testing follow-up scheduler...")
        from followup_scheduler import get_followup_scheduler
        scheduler = get_followup_scheduler()
        print("   ✅ Follow-up scheduler ready")
        
        print("\n✅ All systems operational!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

def show_next_steps():
    """Show user what to do next"""
    print("\n" + "="*50)
    print("🎉 SETUP COMPLETE!")
    print("="*50)
    
    print("\n📋 Next Steps:\n")
    print("1. Enable Gmail IMAP:")
    print("   - Gmail Settings → Forwarding and POP/IMAP")
    print("   - Enable IMAP access\n")
    
    print("2. Test the system:")
    print("   python job_automation_daemon.py --test\n")
    
    print("3. Start automation:")
    print("   python job_automation_daemon.py --start\n")
    
    print("4. Monitor logs:")
    print("   type campaign_results\\automation_log.txt\n")
    
    print("🚀 Your hands-free job agent is ready!")

def main():
    print("""
╔═══════════════════════════════════════════╗
║   InternMailer Automation Setup           ║
║   Zero-effort job hunting system          ║
╚═══════════════════════════════════════════╝
    """)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        print("   Run: pip install -r requirements.txt")
        return
    
    # Check .env file
    if not check_env_file():
        print("\n❌ Please configure .env file and run setup again")
        return
    
    # Test system
    if not test_system():
        print("\n❌ System tests failed - check error messages above")
        return
    
    # Show next steps
    show_next_steps()

if __name__ == '__main__':
    main()
