#!/usr/bin/env python3
"""
Debug script to properly extract emails from email_log.csv
"""

import pandas as pd
import re

def extract_emails_from_log():
    """Extract all actual email addresses from email_log.csv"""
    print("🔍 Debugging email_log.csv structure...")
    
    try:
        df = pd.read_csv('email_log.csv')
        print(f"📊 Total rows in email_log.csv: {len(df)}")
        print(f"📋 Columns: {df.columns.tolist()}")
        
        # Email pattern to validate actual emails
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        all_emails = set()
        
        # Check each column for actual email addresses
        for column in df.columns:
            if column in ['timestamp', 'status', 'error']:
                continue
                
            print(f"\n📂 Checking column: {column}")
            
            # Get all values in this column
            values = df[column].dropna().astype(str)
            emails_found = 0
            
            for value in values:
                value = value.strip().lower()
                if re.match(email_pattern, value):
                    all_emails.add(value)
                    emails_found += 1
            
            print(f"   📧 Found {emails_found} valid emails in {column} column")
        
        print(f"\n📊 SUMMARY:")
        print(f"📧 Total unique emails found: {len(all_emails)}")
        
        # Test specific emails
        test_emails = [
            'mahajan@washington.edu',
            'rguha@ucf.edu', 
            'ratan@ucf.edu'
        ]
        
        print(f"\n🔍 Testing specific emails:")
        for email in test_emails:
            if email.lower() in all_emails:
                print(f"   ✅ {email} - FOUND (should be skipped)")
            else:
                print(f"   ❌ {email} - NOT FOUND (will be suggested)")
        
        # Show first 10 emails for verification
        print(f"\n📝 First 10 emails found:")
        for i, email in enumerate(sorted(list(all_emails))[:10]):
            print(f"   {i+1}. {email}")
            
        return all_emails
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return set()

if __name__ == "__main__":
    emails = extract_emails_from_log()
