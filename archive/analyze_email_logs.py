#!/usr/bin/env python3
"""
Analyze followups and email_logs sections to find the actual sent emails
"""

import json
from pathlib import Path

def analyze_followups_and_logs():
    """Analyze the followups and email_logs sections"""
    
    followup_file = Path('data/followups.json')
    if not followup_file.exists():
        print("Followups.json not found")
        return
    
    print("🔍 ANALYZING FOLLOWUPS AND EMAIL_LOGS SECTIONS")
    print("=" * 60)
    
    with open(followup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_emails = []
    
    # Analyze followups section
    if 'followups' in data:
        followups = data['followups']
        print(f"📧 FOLLOWUPS SECTION:")
        print(f"   Type: {type(followups)}")
        
        if isinstance(followups, dict):
            print(f"   Keys: {list(followups.keys())}")
            for key, value in followups.items():
                print(f"   🔑 {key}: {type(value)} - {len(value) if isinstance(value, (list, dict)) else value}")
                
                # Extract emails from this section
                if isinstance(value, list):
                    for item in value[:5]:  # Check first 5 items
                        if isinstance(item, dict):
                            print(f"     📋 Sample item keys: {list(item.keys())}")
                            for item_key, item_value in item.items():
                                if isinstance(item_value, str) and '@' in item_value:
                                    print(f"       ✅ EMAIL FOUND: {item_key}: {item_value}")
                                    total_emails.append(item_value)
        
        elif isinstance(followups, list):
            print(f"   📋 List with {len(followups)} items")
            for i, item in enumerate(followups[:10]):  # Check first 10
                if isinstance(item, dict):
                    print(f"   📄 Item {i+1} keys: {list(item.keys())}")
                    for key, value in item.items():
                        if isinstance(value, str) and '@' in value and '.' in value:
                            print(f"     ✅ EMAIL FOUND: {key}: {value}")
                            total_emails.append(value)
    
    # Analyze email_logs section
    if 'email_logs' in data:
        email_logs = data['email_logs']
        print(f"\n📨 EMAIL_LOGS SECTION:")
        print(f"   Type: {type(email_logs)}")
        
        if isinstance(email_logs, dict):
            print(f"   Keys: {list(email_logs.keys())}")
            for key, value in email_logs.items():
                print(f"   🔑 {key}: {type(value)} - {len(value) if isinstance(value, (list, dict)) else value}")
                
                # Extract emails from this section
                if isinstance(value, list):
                    print(f"     📋 Processing {len(value)} log entries...")
                    for i, item in enumerate(value[:10]):  # Check first 10
                        if isinstance(item, dict):
                            if i == 0:  # Show structure for first item
                                print(f"     📄 Log entry keys: {list(item.keys())}")
                            
                            for item_key, item_value in item.items():
                                if isinstance(item_value, str) and '@' in item_value and '.' in item_value:
                                    if item_value.count('@') == 1:  # Basic email validation
                                        total_emails.append(item_value)
                    
                    # Count all emails in this log
                    log_emails = []
                    for item in value:
                        if isinstance(item, dict):
                            for item_key, item_value in item.items():
                                if isinstance(item_value, str) and '@' in item_value and '.' in item_value:
                                    if item_value.count('@') == 1:
                                        log_emails.append(item_value)
                    
                    print(f"     ✅ Found {len(log_emails)} emails in this log")
                    total_emails.extend(log_emails)
        
        elif isinstance(email_logs, list):
            print(f"   📋 List with {len(email_logs)} items")
            for i, item in enumerate(email_logs[:10]):  # Check first 10
                if isinstance(item, dict):
                    if i == 0:  # Show structure for first item
                        print(f"   📄 Log entry {i+1} keys: {list(item.keys())}")
                    
                    for key, value in item.items():
                        if isinstance(value, str) and '@' in value and '.' in value:
                            if value.count('@') == 1:  # Basic email validation
                                total_emails.append(value)
            
            # Count all emails in the entire list
            all_log_emails = []
            for item in email_logs:
                if isinstance(item, dict):
                    for key, value in item.items():
                        if isinstance(value, str) and '@' in value and '.' in value:
                            if value.count('@') == 1:
                                all_log_emails.append(value)
            
            print(f"   ✅ Found {len(all_log_emails)} total emails in email_logs")
            total_emails.extend(all_log_emails)
    
    # Remove duplicates and show results
    unique_emails = list(set(total_emails))
    print(f"\n📊 SUMMARY:")
    print(f"   📧 Total emails found: {len(total_emails)}")
    print(f"   🎯 Unique emails: {len(unique_emails)}")
    
    if unique_emails:
        print(f"\n✅ SAMPLE OF FOUND EMAILS:")
        for i, email in enumerate(unique_emails[:20], 1):
            print(f"   {i:2d}. {email}")
        
        if len(unique_emails) > 20:
            print(f"   ... and {len(unique_emails) - 20} more")
        
        return unique_emails
    else:
        print("\n❌ No emails found in followups or email_logs sections")
        return []

if __name__ == "__main__":
    emails = analyze_followups_and_logs()
    print(f"\n🎯 FINAL COUNT: {len(emails)} unique emails found")