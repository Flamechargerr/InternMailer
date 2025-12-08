#!/usr/bin/env python3
"""
Analyze followups.json to find actual email data
"""

import json
from pathlib import Path

def analyze_followups():
    """Analyze the structure of followups.json to find actual emails"""
    
    followup_file = Path('data/followups.json')
    if not followup_file.exists():
        print("Followups.json not found")
        return
    
    print("🔍 ANALYZING FOLLOWUPS.JSON FOR HIDDEN EMAIL DATA")
    print("=" * 60)
    
    with open(followup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📁 File size: {followup_file.stat().st_size / 1024:.1f} KB")
    print(f"🗂️ Top-level keys: {list(data.keys())}")
    
    if 'campaigns' in data:
        campaigns = data['campaigns']
        print(f"📊 Number of campaigns: {len(campaigns)}")
        
        # Analyze a few campaigns to see their structure
        print("\n🔍 ANALYZING CAMPAIGN STRUCTURES:")
        
        email_count = 0
        for i, (campaign_id, campaign_data) in enumerate(campaigns.items()):
            if i >= 5:  # Check first 5 campaigns
                break
                
            print(f"\n📧 Campaign {i+1}: {campaign_id}")
            print(f"   📝 Name: {campaign_data.get('name', 'Unknown')}")
            print(f"   📅 Created: {campaign_data.get('created_at', 'Unknown')}")
            print(f"   🔑 Keys: {list(campaign_data.keys())}")
            
            # Look for email data in each campaign
            for key, value in campaign_data.items():
                if isinstance(value, dict):
                    print(f"     🗂️ {key}: {list(value.keys()) if value else 'Empty dict'}")
                elif isinstance(value, list):
                    print(f"     📋 {key}: List with {len(value)} items")
                    if value and isinstance(value[0], dict):
                        print(f"         Sample item keys: {list(value[0].keys())}")
                        # Check if this contains emails
                        for item in value[:3]:  # Check first 3 items
                            if isinstance(item, dict):
                                for item_key, item_value in item.items():
                                    if '@' in str(item_value):
                                        print(f"         🎯 FOUND EMAIL: {item_key}: {item_value}")
                                        email_count += 1
                else:
                    print(f"     📄 {key}: {type(value).__name__}")
        
        print(f"\n📊 TOTAL EMAILS FOUND IN CAMPAIGNS: {email_count}")
        
        # Try to extract all actual emails
        all_emails = []
        for campaign_id, campaign_data in campaigns.items():
            # Recursively search for email addresses
            emails = extract_emails_recursive(campaign_data)
            all_emails.extend(emails)
        
        if all_emails:
            print(f"\n✅ FOUND {len(all_emails)} EMAIL ADDRESSES:")
            for i, email in enumerate(all_emails[:20], 1):  # Show first 20
                print(f"   {i:2d}. {email}")
            if len(all_emails) > 20:
                print(f"   ... and {len(all_emails) - 20} more")
        else:
            print("\n❌ No email addresses found in campaign data")

def extract_emails_recursive(obj, emails=None):
    """Recursively extract email addresses from nested objects"""
    if emails is None:
        emails = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and '@' in value and '.' in value:
                # Basic email validation
                if value.count('@') == 1 and len(value) > 5:
                    emails.append(value)
            else:
                extract_emails_recursive(value, emails)
    elif isinstance(obj, list):
        for item in obj:
            extract_emails_recursive(item, emails)
    
    return emails

if __name__ == "__main__":
    analyze_followups()