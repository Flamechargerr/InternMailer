#!/usr/bin/env python3
"""
Download Fortune 500 company list CSV into data/fortune500_2019.csv
"""

import argparse
from pathlib import Path
import requests


DEFAULT_URL = "https://raw.githubusercontent.com/cmusam/fortune500/master/csv/fortune500-2019.csv"
DEFAULT_OUT = "data/fortune500_2019.csv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    resp = requests.get(args.url, timeout=30)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    print(f"Saved Fortune 500 list to {out_path}")


if __name__ == "__main__":
    main()
