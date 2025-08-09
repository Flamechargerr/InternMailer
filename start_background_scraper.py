#!/usr/bin/env python3
"""
Start Background Scraper
Starts the background email scraper in various modes
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    requirements = [
        'pandas',
        'schedule',
        'requests',
        'pywin32'  # For Windows service
    ]
    
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"⚠️ Failed to install {package}")

def start_background_scraper(mode='continuous'):
    """Start the background scraper"""
    print(f"🚀 Starting background scraper in {mode} mode...")
    
    if mode == 'continuous':
        # Run continuously in background
        cmd = [sys.executable, 'background_scraper.py', '--continuous', '--interval', '30']
    elif mode == 'session':
        # Run single session
        cmd = [sys.executable, 'background_scraper.py', '--session']
    elif mode == 'service':
        # Create Windows service
        cmd = [sys.executable, 'background_scraper.py', '--service']
    elif mode == 'cloud':
        # Create cloud deployment
        cmd = [sys.executable, 'background_scraper.py', '--cloud']
    else:
        print("❌ Invalid mode. Use: continuous, session, service, or cloud")
        return
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting scraper: {e}")

def create_startup_script():
    """Create startup script for automatic running"""
    startup_script = """@echo off
cd /d "%~dp0"
python background_scraper.py --continuous --interval 30
pause
"""
    
    with open('start_background_scraper.bat', 'w') as f:
        f.write(startup_script)
    
    print("✅ Created startup script: start_background_scraper.bat")
    print("📋 Double-click to start background scraping")

def create_scheduled_task():
    """Create Windows scheduled task"""
    task_script = f"""
schtasks /create /tn "BackgroundEmailScraper" /tr "{os.path.abspath('start_background_scraper.bat')}" /sc onstart /ru System /f
"""
    
    with open('create_scheduled_task.bat', 'w') as f:
        f.write(task_script)
    
    print("✅ Created scheduled task script: create_scheduled_task.bat")
    print("📋 Run as administrator to create startup task")

def show_status():
    """Show current scraping status"""
    print("\n📊 BACKGROUND SCRAPER STATUS")
    print("=" * 50)
    
    # Check if scraper is running
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True)
        if 'background_scraper.py' in result.stdout:
            print("🟢 Background scraper is running")
        else:
            print("🔴 Background scraper is not running")
    except:
        print("⚠️ Could not check scraper status")
    
    # Check log files
    log_files = ['background_scraper.log', 'background_scraper_stats.json']
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"📝 {log_file} exists")
        else:
            print(f"❌ {log_file} not found")
    
    # Check output files
    output_files = ['background_scraped_emails.csv', 'scraping_progress.json']
    for output_file in output_files:
        if os.path.exists(output_file):
            print(f"📊 {output_file} exists")
        else:
            print(f"❌ {output_file} not found")

def main():
    """Main function"""
    print("🚀 BACKGROUND EMAIL SCRAPER STARTUP")
    print("=" * 50)
    
    while True:
        print("\n📋 Choose an option:")
        print("1. Install requirements")
        print("2. Start continuous scraping (runs every 30 minutes)")
        print("3. Run single scraping session")
        print("4. Create Windows service")
        print("5. Create cloud deployment")
        print("6. Create startup script")
        print("7. Create scheduled task")
        print("8. Show status")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            install_requirements()
        elif choice == '2':
            start_background_scraper('continuous')
        elif choice == '3':
            start_background_scraper('session')
        elif choice == '4':
            start_background_scraper('service')
        elif choice == '5':
            start_background_scraper('cloud')
        elif choice == '6':
            create_startup_script()
        elif choice == '7':
            create_scheduled_task()
        elif choice == '8':
            show_status()
        elif choice == '9':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 