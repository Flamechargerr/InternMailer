#!/usr/bin/env python3
"""
Final ULTRA Campaign Launcher
================================
This script performs a definitive duplicate check across all known log files
and then runs the ULTRA HTML Bulk Campaign system with credentials.
"""

import os
import sys
import re
import glob
import json
import pandas as pd

def get_all_contacted_emails():
    """Scans all known log files to get a master set of contacted emails."""
    print("🛡️ Starting comprehensive duplicate check across all logs...")
    contacted_emails = set()

    # 1. email_log.csv (with robust parsing)
    try:
        df = pd.read_csv('email_log.csv', on_bad_lines='skip')
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        for col in df.columns:
            if df[col].dtype == 'object':
                emails_in_col = df[col].str.findall(email_pattern).explode().dropna()
                emails_in_col = emails_in_col.str.lower().str.strip()
                original_count = len(contacted_emails)
                contacted_emails.update(emails_in_col)
                added_count = len(contacted_emails) - original_count
                if added_count > 0:
                    print(f"   - Found {added_count} emails in email_log.csv -> '{col}' column")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"   - ⚠️ Warning: Could not process email_log.csv: {e}")

    # 2. sent_emails_log.json
    try:
        with open('sent_emails_log.json', 'r') as f:
            data = json.load(f)
            sent_emails = {str(e).lower().strip() for e in data.get('sent_emails', [])}
            original_count = len(contacted_emails)
            contacted_emails.update(sent_emails)
            added_count = len(contacted_emails) - original_count
            if added_count > 0:
                 print(f"   - Found {added_count} emails in sent_emails_log.json")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # 3. campaign_results/ and fixed_campaign_results/
    for folder in ['campaign_results', 'fixed_campaign_results']:
        files = glob.glob(f'{folder}/*.txt')
        if files:
            folder_emails = set()
            for file_path in files:
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                        match = re.search(r'TO:.*?<([^>]+)>', content)
                        if match:
                            folder_emails.add(match.group(1).lower().strip())
                except Exception:
                    continue
            original_count = len(contacted_emails)
            contacted_emails.update(folder_emails)
            added_count = len(contacted_emails) - original_count
            if added_count > 0:
                print(f"   - Found {added_count} emails in {folder}/")
    
    print(f"\n📊 Total unique contacted emails found: {len(contacted_emails)}")
    return contacted_emails

def main():
    """Main execution function"""
    # Get all contacted emails
    contacted_emails = get_all_contacted_emails()

    # Load the authentic professor database
    db_path = 'production/databases/FINAL_MASTER_EMAIL_DATABASE.csv'
    print(f"\n📁 Loading authentic professor database from: {db_path}")
    if not os.path.exists(db_path):
        print(f"❌ CRITICAL ERROR: Authentic database not found at {db_path}")
        return

    df = pd.read_csv(db_path)
    original_prof_count = len(df)
    print(f"   - Loaded {original_prof_count} total professors.")

    # Filter out contacted professors
    df['email_lower'] = df['email'].str.lower().str.strip()
    df_fresh = df[~df['email_lower'].isin(contacted_emails)]
    fresh_prof_count = len(df_fresh)
    filtered_count = original_prof_count - fresh_prof_count
    print(f"   - Filtered out {filtered_count} already contacted professors.")
    print(f"💡 {fresh_prof_count} truly fresh professors remaining.")

    if fresh_prof_count == 0:
        print("\n✅ All professors in the authentic database have been contacted.")
        return

    # Prepare for the ULTRA campaign
    print("\n🚀 Preparing ULTRA Campaign...")
    
    # Use the credentials you provided earlier
    # These will be set as environment variables for the campaign
    email_address = "tripathy.anamay23@gmail.com"
    email_password = "xctf elgn llfo aohf"
    os.environ['EMAIL_ADDRESS'] = email_address
    os.environ['EMAIL_PASSWORD'] = email_password
    os.environ['MAX_EMAILS_PER_SESSION'] = '3' # Let's send 3 emails
    os.environ['CONCURRENT_WORKERS'] = '1'
    
    # Save the fresh list for the ULTRA system to use
    fresh_db_path = 'professors_database.csv'
    df_fresh.to_csv(fresh_db_path, index=False)
    print(f"   - Saved {fresh_prof_count} fresh professors to {fresh_db_path}")
    print(f"   - Set to send a batch of {os.environ['MAX_EMAILS_PER_SESSION']} emails.")

    print("\n🎯 Top 3 Fresh Professors to be Contacted:")
    for i, row in df_fresh.head(3).iterrows():
        print(f"   {i+1}. {row['name']} - {row['university']} ({row['email']})")

    confirm = input("\n✅ Ready to send live, personalized emails to these 3 fresh professors? (y/n): ").strip().lower()

    if confirm == 'y':
        try:
            print("\n🚀 Launching ULTRA HTML Bulk Campaign System...")
            from ULTRA_HTML_BULK_SYSTEM import UltraHTMLBulkCampaign
            campaign = UltraHTMLBulkCampaign()
            campaign.run_bulk_campaign()
            print("\n🎉 Campaign finished!")
        except ImportError:
            print("❌ ERROR: Could not import ULTRA_HTML_BULK_SYSTEM.py")
        except Exception as e:
            print(f"❌ ERROR: Campaign failed: {e}")
    else:
        print("\n🛑 Campaign cancelled by user.")

if __name__ == "__main__":
    main()

