#!/usr/bin/env python3
"""
🚀 InternMailer - Quick Launch Script
Simple interactive menu to run the automation system.

Usage:
    python run.py
"""

import os
import sys
import subprocess


def print_menu():
    """Print the main menu"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║               🤖 INTERNMAILER - QUICK LAUNCHER               ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📧 SENDING                                                  ║
║  ──────────────────────────────────────────────────────────  ║
║  1. Preview 3 emails (see what will be sent)                 ║
║  2. Send 5 emails (small test)                               ║
║  3. Send 10 emails                                           ║
║  4. Send 20 emails                                           ║
║  5. Send custom amount                                       ║
║                                                              ║
║  🤖 AUTOMATION                                               ║
║  ──────────────────────────────────────────────────────────  ║
║  6. Start full automation daemon                             ║
║  7. Run one automation cycle (test)                          ║
║  8. Check daemon status                                      ║
║                                                              ║
║  📊 MONITORING                                               ║
║  ──────────────────────────────────────────────────────────  ║
║  9. View campaign statistics                                 ║
║  10. View recent logs                                        ║
║                                                              ║
║  ⚙️  SETUP                                                   ║
║  ──────────────────────────────────────────────────────────  ║
║  11. Check configuration                                     ║
║  12. Install dependencies                                    ║
║                                                              ║
║  🧭 JOBS                                                     ║
║  ──────────────────────────────────────────────────────────  ║
║  13. Discover jobs                                           ║
║  14. Auto-apply to jobs                                      ║
║                                                              ║
║  0. Exit                                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def preview_emails():
    """Preview emails without sending"""
    print("\n📧 Generating email previews...\n")
    result = subprocess.run([sys.executable, 'core/email_system.py', '--preview', '3'])
    if result.returncode != 0:
        print("❌ Error running preview. Make sure email_system.py exists.")


def send_emails(count: int):
    """Send emails"""
    print(f"\n📤 Sending {count} emails...\n")
    result = subprocess.run([sys.executable, 'core/email_system.py', '--send', str(count)])
    if result.returncode != 0:
        print("❌ Error sending emails. Check your configuration.")


def send_custom():
    """Send custom amount"""
    try:
        count = input("\nHow many emails to send? ").strip()
        count = int(count)
        if count <= 0:
            print("❌ Please enter a positive number")
            return
        if count > 100:
            confirm = input(f"⚠️  That's a lot! Send {count} emails? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("Cancelled")
                return
        send_emails(count)
    except ValueError:
        print("❌ Please enter a valid number")


def start_daemon():
    """Start the automation daemon"""
    print("\n🤖 Starting automation daemon...")
    print("   This will:")
    print("   • Monitor your inbox every hour")
    print("   • Auto-respond to replies")
    print("   • Send follow-ups automatically")
    print("\n   Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([sys.executable, 'core/enhanced_daemon.py', '--start'])
    except KeyboardInterrupt:
        print("\n⏹️  Daemon stopped")


def test_cycle():
    """Run one automation cycle"""
    print("\n🧪 Running one automation cycle (test mode)...\n")
    result = subprocess.run([sys.executable, 'core/enhanced_daemon.py', '--cycle'])
    if result.returncode != 0:
        print("❌ Error running test cycle.")


def check_status():
    """Check daemon status"""
    print("\n📊 Checking status...\n")
    result = subprocess.run([sys.executable, 'core/enhanced_daemon.py', '--status'])
    if result.returncode != 0:
        print("❌ Error checking status.")


def view_stats():
    """View campaign statistics"""
    print("\n📊 Campaign Statistics\n")
    result = subprocess.run([sys.executable, 'core/email_system.py', '--stats'])
    if result.returncode != 0:
        print("❌ Error getting statistics.")


def view_logs():
    """View recent logs"""
    log_file = '/tmp/internmailer_db/automation_log.txt'
    
    if not os.path.exists(log_file):
        print(f"\n❌ Log file not found: {log_file}")
        return
    
    print(f"\n📄 Recent logs from {log_file}:\n")
    
    try:
        # Read last 50 lines
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines
            for line in last_lines:
                print(line.rstrip())
    except Exception as e:
        print(f"❌ Error reading logs: {e}")


def check_config():
    """Check configuration"""
    print("\n⚙️  Checking configuration...\n")
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file found")
        
        # Read and check key variables
        with open('.env', 'r') as f:
            content = f.read()
            
        if 'GMAIL_USER' in content or 'EMAIL_ADDRESS' in content:
            print("✅ Email configuration present")
        else:
            print("❌ Email configuration missing")
            
        if 'GMAIL_APP_PASSWORD' in content or 'EMAIL_PASSWORD' in content:
            print("✅ Password configuration present")
        else:
            print("❌ Password configuration missing")
    else:
        print("❌ .env file not found")
        print("   Create one with your Gmail credentials")
    
    # Check data directory
    if os.path.exists('data'):
        csv_files = [f for f in os.listdir('data') if f.endswith('.csv')]
        if csv_files:
            print(f"✅ Found {len(csv_files)} CSV file(s) in data/")
        else:
            print("⚠️  No CSV files in data/ directory")
    else:
        print("❌ data/ directory not found")
    
    # Check resume
    resume_paths = ['resumes/CV_Anamay_Modern.pdf', 'CV_Anamay_Modern.pdf', 'resume.pdf']
    resume_found = any(os.path.exists(p) for p in resume_paths)
    if resume_found:
        print("✅ Resume found")
    else:
        print("⚠️  Resume not found (will send without attachment)")
    
    # Check required files
    required_files = [
        'core/email_system.py', 
        'core/enhanced_daemon.py', 
        'core/inbox_monitor.py',
        'core/reply_classifier.py', 
        'core/gmail_agent.py',
        'core/followup_scheduler.py',
        'core/lead_discovery.py'
    ]
    
    print("\n📁 Core files:")
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")
    
    print()


def discover_jobs():
    """Run job discovery"""
    print("\n🧭 Running job discovery...\n")
    try:
        from core.job_discovery import JobDiscovery
        discovery = JobDiscovery()
        result = discovery.run()
        print(f"✅ Found {result['total_found']} jobs, saved {result['total_saved']}")
    except Exception as e:
        print(f"❌ Job discovery failed: {e}")


def apply_jobs():
    """Auto-apply to jobs"""
    print("\n🤖 Auto-applying to jobs...\n")
    try:
        from core.job_pipeline import JobPipeline
        pipeline = JobPipeline()
        result = pipeline.apply_pending(limit=50)
        print(f"✅ Attempted {result['attempted']} job applications")
    except Exception as e:
        print(f"❌ Job auto-apply failed: {e}")


def install_deps():
    """Install dependencies"""
    print("\n📦 Installing dependencies...\n")
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    if result.returncode == 0:
        print("\n✅ Dependencies installed successfully")
    else:
        print("\n❌ Error installing dependencies")


def main():
    """Main menu loop"""
    while True:
        print_menu()
        choice = input("Select option [0-14]: ").strip()
        
        if choice == "1":
            preview_emails()
        elif choice == "2":
            send_emails(5)
        elif choice == "3":
            send_emails(10)
        elif choice == "4":
            send_emails(20)
        elif choice == "5":
            send_custom()
        elif choice == "6":
            start_daemon()
        elif choice == "7":
            test_cycle()
        elif choice == "8":
            check_status()
        elif choice == "9":
            view_stats()
        elif choice == "10":
            view_logs()
        elif choice == "11":
            check_config()
        elif choice == "12":
            install_deps()
        elif choice == "13":
            discover_jobs()
        elif choice == "14":
            apply_jobs()
        elif choice == "0":
            print("\n👋 Goodbye!\n")
            sys.exit(0)
        else:
            print("\n❌ Invalid option. Please try again.\n")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!\n")
        sys.exit(0)
