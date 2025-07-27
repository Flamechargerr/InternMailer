#!/usr/bin/env python3
"""
Demo script to run the InternMailer UI with Real-time Monitoring

This script demonstrates how to run the Streamlit application with 
the new real-time monitoring features.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages."""
    print("Installing required packages...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def run_streamlit_app():
    """Run the Streamlit application."""
    print("Starting InternMailer UI with Real-time Monitoring...")
    print("📈 Features included:")
    print("  - Auto-refresh every 10 seconds (configurable)")
    print("  - Live campaign status monitoring")
    print("  - Color-coded metrics and alerts")
    print("  - Real-time delivery analytics")
    print("  - Campaign activity logs")
    print("  - Interactive pause/resume controls")
    print("  - System status indicators")
    print()
    print("🌐 The application will open in your default browser.")
    print("📍 URL: http://localhost:8501")
    print("🔄 Navigate to 'Real-time Monitoring' from the sidebar menu.")
    print()
    
    try:
        # Change to the current directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Run streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down InternMailer UI...")
    except Exception as e:
        print(f"❌ Error running Streamlit app: {e}")

def main():
    """Main function to run the demo."""
    print("🚀 InternMailer UI Demo - Real-time Monitoring")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ Please run this script from the internmailer_ui directory")
        print("   cd internmailer_ui && python run_demo.py")
        return
    
    # Install requirements if needed
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    print()
    print("📋 Demo Notes:")
    print("  - The app uses fallback demo data when backend API is unavailable")
    print("  - Real-time features will work with mock data for demonstration")
    print("  - To connect to a real backend, update the API URLs in services/")
    print()
    
    input("Press Enter to start the application...")
    
    # Run the app
    run_streamlit_app()

if __name__ == "__main__":
    main()
