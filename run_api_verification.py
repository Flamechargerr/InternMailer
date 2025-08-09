#!/usr/bin/env python3
"""
Immediately run API verification for Semantic Scholar
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from verify_api_now import verify_api_now

def main():
    """Immediately run API verification"""
    print("🚀 Immediately Running API Verification for Semantic Scholar...")
    verify_api_now()

if __name__ == "__main__":
    main()
