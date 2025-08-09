#!/usr/bin/env python3
import pandas as pd
import glob
import os

print("🔍 CHECKING DATABASE SIZES")
print("=" * 50)

# Check CSRankings files
files = glob.glob('data/csrankings-*.csv')
total = 0
for f in files:
    try:
        df = pd.read_csv(f)
        total += len(df)
        print(f"   {f}: {len(df):,} records")
    except Exception as e:
        print(f"   {f}: Error - {e}")

print(f"\n📊 Total CSRankings records: {total:,}")

# Check other databases
other_dbs = [
    'data/proffesor_clean.csv',
    'data/list.csv',
    'enhanced_background_emails.csv'
]

for db in other_dbs:
    if os.path.exists(db):
        try:
            df = pd.read_csv(db)
            print(f"📁 {db}: {len(df):,} records")
        except Exception as e:
            print(f"📁 {db}: Error - {e}")
    else:
        print(f"📁 {db}: Not found")

print("\n✅ Database analysis complete!")
