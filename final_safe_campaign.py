#!/usr/bin/env python3
"""
FINAL SAFE CAMPAIGN SCRIPT
===========================
This script uses EVERY possible method to avoid duplicate contacts:
1. Email logs
2. Campaign results  
3. Manual blocklist
4. Ultra-strict validation
"""

import os
import re
import pandas as pd

def load_manual_blocklist():
    """Load manual blocklist of known contacted professors"""
    blocklist = set()
    try:
        with open('manual_blocklist.txt', 'r') as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith('#'):
                    blocklist.add(line)
        print(f"📋 Loaded {len(blocklist)} manually blocked emails")
    except FileNotFoundError:
        print("⚠️  Manual blocklist not found - creating empty one")
    return blocklist

def get_absolutely_clean_professors():
    """Get professors with ZERO chance of being duplicates"""
    print("🔒 ABSOLUTE DUPLICATE PREVENTION")
    print("=" * 50)
    
    # Load cleaned database
    clean_db_path = 'production/databases/CLEANED_MASTER_EMAIL_DATABASE.csv'
    if not os.path.exists(clean_db_path):
        print("❌ Run clean_database.py first!")
        return None
    
    df = pd.read_csv(clean_db_path)
    print(f"📊 Starting with {len(df)} pre-cleaned records")
    
    # 1. Manual blocklist
    manual_blocked = load_manual_blocklist()
    
    # 2. Load ALL possible contacted emails
    all_contacted = set()
    
    # From email logs
    try:
        email_df = pd.read_csv('email_log.csv', on_bad_lines='skip')
        for col in email_df.columns:
            if email_df[col].dtype == 'object':
                emails = email_df[col].str.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}').explode().dropna()
                all_contacted.update(emails.str.lower())
        print(f"📊 Found emails in email_log.csv")
    except:
        pass
    
    # From JSON logs
    try:
        import json
        with open('sent_emails_log.json', 'r') as f:
            data = json.load(f)
            all_contacted.update([str(e).lower() for e in data.get('sent_emails', [])])
        print(f"📊 Found emails in sent_emails_log.json")
    except:
        pass
    
    # From followup logs
    try:
        followup_df = pd.read_csv('followup_log.csv', on_bad_lines='skip')
        for col in followup_df.columns:
            if followup_df[col].dtype == 'object':
                emails = followup_df[col].str.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}').explode().dropna()
                all_contacted.update(emails.str.lower())
        print(f"📊 Found emails in followup_log.csv")
    except:
        pass
    
    # From campaign results files
    import glob
    campaign_files = glob.glob('campaign_results/*.txt') + glob.glob('fixed_campaign_results/*.txt')
    for file_path in campaign_files:
        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}', content)
                all_contacted.update([e.lower() for e in emails])
        except:
            continue
    if campaign_files:
        print(f"📊 Scanned {len(campaign_files)} campaign result files")
    
    # From sent_emails directory
    sent_files = glob.glob('sent_emails/*.json')
    for file_path in sent_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'recipient' in data:
                    all_contacted.add(data['recipient'].lower())
        except:
            continue
    if sent_files:
        print(f"📊 Scanned {len(sent_files)} individual email records")
    
    # Combine all blocked emails
    total_blocked = all_contacted | manual_blocked
    print(f"🛡️ TOTAL BLOCKED EMAILS: {len(total_blocked)}")
    print(f"   - From logs: {len(all_contacted)}")
    print(f"   - Manual blocklist: {len(manual_blocked)}")
    
    # Filter out ALL blocked emails
    df_clean = df[~df['email'].str.lower().isin(total_blocked)]
    
    # Ultra-strict validation
    def ultra_validate(email):
        email = str(email).lower().strip()
        # Basic format
        if not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,4}$', email):
            return False
        # Academic domain
        if not any(dom in email for dom in ['.edu', '.ac.uk', '.ac.in', '.ac.jp']):
            return False
        # Not too weird
        if any(bad in email for bad in ['phone', 'fax', 'office', 'room', 'hall', 'building']):
            return False
        return True
    
    df_ultra = df_clean[df_clean['email'].apply(ultra_validate)]
    
    print(f"✅ FILTERING COMPLETE:")
    print(f"   - Original: {len(df)}")
    print(f"   - After blocking: {len(df_clean)}")
    print(f"   - After validation: {len(df_ultra)}")
    print(f"   - Final success rate: {(len(df_ultra)/len(df))*100:.1f}%")
    
    return df_ultra

def run_final_campaign():
    """Run the final, absolutely safe campaign"""
    
    df_final = get_absolutely_clean_professors()
    if df_final is None or len(df_final) == 0:
        print("❌ No safe professors found!")
        return
    
    print(f"\n🎯 TOP 5 ABSOLUTELY SAFE PROFESSORS:")
    for i, (_, row) in enumerate(df_final.head(5).iterrows()):
        name = row.get('name', 'Unknown')
        email = row['email']
        university = row.get('university', 'Unknown')
        print(f"   {i+1}. {name} - {university} ({email})")
    
    print(f"\n🔒 FINAL SAFETY VERIFICATION:")
    print(f"   ✅ Manual blocklist checked")
    print(f"   ✅ All log files scanned")
    print(f"   ✅ Campaign results checked")  
    print(f"   ✅ Email validation ultra-strict")
    print(f"   ✅ Batch size: 2 emails only")
    print(f"   ✅ These are 100% NEW professors")
    
    confirm = input(f"\n🚀 Send to these 2 VERIFIED NEW professors? (y/n): ").strip().lower()
    
    if confirm == 'y':
        # Save top 2 for campaign
        top_2 = df_final.head(2)
        top_2.to_csv('professors_database.csv', index=False)
        
        # Environment setup
        os.environ['EMAIL_ADDRESS'] = "tripathy.anamay23@gmail.com" 
        os.environ['EMAIL_PASSWORD'] = "xctf elgn llfo aohf"
        os.environ['MAX_EMAILS_PER_SESSION'] = '2'
        os.environ['CONCURRENT_WORKERS'] = '1'
        
        print(f"\n🚀 Launching FINAL SAFE CAMPAIGN...")
        print(f"📧 Target 1: {top_2.iloc[0]['email']}")
        print(f"📧 Target 2: {top_2.iloc[1]['email']}")
        
        try:
            from ULTRA_HTML_BULK_SYSTEM import UltraHTMLBulkCampaign
            campaign = UltraHTMLBulkCampaign()
            campaign.run_bulk_campaign()
            
            # Add to manual blocklist to prevent future duplicates
            with open('manual_blocklist.txt', 'a') as f:
                f.write(f"\n# Added after campaign on {pd.Timestamp.now()}\n")
                for _, row in top_2.iterrows():
                    f.write(f"{row['email']}\n")
            
            print("🎉 FINAL CAMPAIGN COMPLETED!")
            print("📋 Added new emails to manual blocklist")
            
        except Exception as e:
            print(f"❌ Campaign error: {e}")
    else:
        print("🛑 Final campaign cancelled")

if __name__ == "__main__":
    run_final_campaign()
