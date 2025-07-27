#!/usr/bin/env python3
"""
InternMailer Secure Startup Script

This script starts the InternMailer application with comprehensive security 
checks and error handling.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
import setup_secure

def main():
    """Main startup function with security validation.""" 
    print("🚀 InternMailer - Secure Startup")
    print("=" * 50)
    
    # Run security validation first
    print("Running security and setup validation...")
    if not setup_secure.main():
        print("\n❌ Security validation failed. Please fix issues before continuing.")
        return False
    
    print("\n🔒 All security checks passed!")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("InternMailer").exists():
        print("❌ Please run this script from the InternMailer project root directory")
        return False
    
    # Start the application
    app_path = Path("InternMailer/app.py")
    
    if not app_path.exists():
        print("❌ InternMailer app not found. Please run this script from the project root.")
        return False
    
    print("🚀 Starting InternMailer...")
    print("📱 The app will open in your browser automatically")
    print("🔗 If it doesn't open, go to: http://localhost:8501")
    print("\n" + "="*60)
    print("SECURITY FEATURES ACTIVE:")
    print("="*60)
    print("🔒 Environment variables validated")
    print("📁 Secure directory structure")
    print("🧹 Sensitive files cleaned")
    print("🔍 Dependencies verified")
    print("="*60)
    print("\nPress Ctrl+C to stop the application")
    print("=" * 50)
    
    try:
        # Start Streamlit with security headers and configuration
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.headless", "false",
            "--server.runOnSave", "true", 
            "--browser.gatherUsageStats", "false",
            "--server.maxUploadSize", "10",  # Limit upload size to 10MB
            "--server.enableCORS", "false",  # Disable CORS for security
            "--server.enableXsrfProtection", "true"  # Enable XSRF protection
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
