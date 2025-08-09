#!/usr/bin/env python3
"""
Immediately run API check for Semantic Scholar
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from check_api_now import check_api_now

def main():
    """Immediately run API check"""
    print("🚀 Immediately Running API Check for Semantic Scholar...")
    check_api_now()

if __name__ == "__main__":
    main()
