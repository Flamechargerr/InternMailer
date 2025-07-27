#!/usr/bin/env python3
"""
InternMailer Startup Script

This script starts the InternMailer Streamlit application with the integrated 
follow-up scheduler. It also provides instructions for running the background 
scheduler components if needed.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def check_requirements():
    """Check if required packages are installed."""
    try:
        import streamlit
        import plotly
        import pandas
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def start_streamlit_app():
    """Start the Streamlit application."""
    app_path = Path("InternMailer/app.py")
    
    if not app_path.exists():
        print("❌ InternMailer app not found. Please run this script from the project root.")
        return False
    
    print("🚀 Starting InternMailer...")
    print("📱 The app will open in your browser automatically")
    print("🔗 If it doesn't open, go to: http://localhost:8501")
    print("\n" + "="*60)
    print("FOLLOW-UP SCHEDULER FEATURES:")
    print("="*60)
    print("✨ Integrated follow-up scheduling")
    print("📊 Real-time analytics dashboard") 
    print("⚙️  Per-campaign settings")
    print("📅 Reschedule/cancel individual follow-ups")
    print("🔄 Automatic overdue processing")
    print("="*60)
    print("\nPress Ctrl+C to stop the application")
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    return True

def show_advanced_setup():
    """Show instructions for advanced scheduler setup."""
    print("\n" + "="*60)
    print("ADVANCED SCHEDULER SETUP (Optional)")
    print("="*60)
    print("For production use with Celery background tasks:")
    print()
    print("1. Install Redis:")
    print("   - Windows: Download from https://redis.io/download")
    print("   - Linux/Mac: sudo apt install redis-server / brew install redis")
    print()
    print("2. Start Redis server:")
    print("   redis-server")
    print()
    print("3. Start Celery worker (in a new terminal):")
    print("   celery -A src.scheduler.celery_app worker --loglevel=info")
    print()
    print("4. Start Celery beat scheduler (in another terminal):")
    print("   celery -A src.scheduler.celery_app beat --loglevel=info")
    print()
    print("Note: The basic scheduler works without Redis/Celery for testing")
    print("="*60)

def main():
    """Main startup function."""
    print("🚀 InternMailer - AI-Powered Academic Outreach Platform")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("InternMailer").exists():
        print("❌ Please run this script from the InternMailer project root directory")
        return
    
    # Check requirements
    if not check_requirements():
        return
    
    # Show advanced setup info
    show_advanced_setup()
    
    # Ask if user wants to start the app
    response = input("\n▶️  Start the InternMailer app now? [Y/n]: ").strip().lower()
    if response in ['', 'y', 'yes']:
        start_streamlit_app()
    else:
        print("👋 Setup complete. Run 'python start_app.py' when ready to start.")

if __name__ == "__main__":
    main()
