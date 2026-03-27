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
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO),
        format='%(asctime)s %(levelname)s %(name)s: %(message)s'
    )
    args = sys.argv[1:]
    
    if '--cli' in args or '-c' in args:
        # Launch CLI menu
        logger.info("Starting CLI menu")
        from utils.run import main as cli_main
        cli_main()
    else:
        # Launch web dashboard by default
        logger.info("Starting web dashboard")
        logger.info("Open http://localhost:5050 in your browser")
        from web.web_dashboard import app
        app.run(host='0.0.0.0', port=5050, debug=True)

if __name__ == '__main__':
    main()
