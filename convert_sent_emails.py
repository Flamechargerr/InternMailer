#!/usr/bin/env python3
"""
Convert existing CSV email log to JSON format for the new Ultra HTML Bulk System
"""

import pandas as pd
import json
import os
from datetime import datetime

def convert_csv_to_json():
    """Convert the existing CSV email log to JSON format."""
    
    sent_emails = set()
    
    try:
        # Read the existing CSV log
        if os.path.exists('email_log.csv'):
            df = pd.read_csv('email_log.csv')
            
            # Extract email addresses from successful sends
            if 'status' in df.columns and 'email' in df.columns:
                successful_sends = df[df['status'] == 'sent']['email'].tolist()
                sent_emails.update(successful_sends)
            elif 'email' in df.columns:
                # If no status column, assume all are sent
                all_emails = df['email'].tolist()
                sent_emails.update(all_emails)
            
            print(f"Found {len(sent_emails)} previously sent emails")
            
        # Save to JSON format
        json_data = {
            'sent_emails': list(sent_emails),
            'last_updated': datetime.now().isoformat(),
            'total_sent': len(sent_emails),
            'converted_from': 'email_log.csv'
        }
        
        with open('sent_emails_log.json', 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"✅ Converted {len(sent_emails)} email addresses to sent_emails_log.json")
        print("The new system will now skip these previously contacted professors")
        
    except Exception as e:
        print(f"❌ Error converting emails: {e}")
        # Create empty log if conversion fails
        with open('sent_emails_log.json', 'w') as f:
            json.dump({
                'sent_emails': [],
                'last_updated': datetime.now().isoformat(),
                'total_sent': 0
            }, f, indent=2)

if __name__ == "__main__":
    convert_csv_to_json()
