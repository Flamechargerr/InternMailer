#!/usr/bin/env python3
"""
🚀 InternMailer - Main Entry Point
==================================
Launch the web dashboard or CLI menu.

Usage:
    python main.py              # Launch web dashboard
    python main.py --cli        # Launch CLI menu
    python main.py --web        # Launch web dashboard (explicit)
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point"""
    args = sys.argv[1:]
    
    if '--cli' in args or '-c' in args:
        # Launch CLI menu
        print("🖥️  Starting CLI menu...")
        from utils.run import main as cli_main
        cli_main()
    else:
        # Launch web dashboard by default
        print("🌐 Starting web dashboard...")
        print("Open http://localhost:5000 in your browser\n")
        from web.web_dashboard import app
        app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
