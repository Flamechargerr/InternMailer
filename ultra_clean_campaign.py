#!/usr/bin/env python3
"""
Ultra Clean Email Campaign
===========================
Final script with ultra-strict email validation and safe campaign launch
"""

import os
import re
import pandas as pd

def ultra_validate_email(email):
    """Ultra-strict email validation for academic emails"""
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip().lower()
    
    # Must be basic email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$', email):
        return False
    
    # Split into parts
    local, domain = email.split('@')
    domain_parts = domain.split('.')
    tld = domain_parts[-1]
    
    # Reject if local part or domain contains contamination
    contaminations = ['phone', 'fax', 'office', 'room', 'address', 'hall', '314-977-6667']
    for cont in contaminations:
        if cont in local or cont in domain:
            return False
    
    # Must be academic domain
    academic_domains = ['.edu', '.ac.uk', '.ac.in', '.ac.jp', '.ac.kr', '.ac.cn', 
                       '.edu.au', '.edu.sg', '.edu.hk']
    if not any(domain.endswith(acad[1:]) for acad in academic_domains):
        return False
    
    # TLD must be proper
    if not (2 <= len(tld) <= 4 and tld.isalpha()):
        return False
    
    # Local part must be reasonable (not too long, no weird patterns)
    if len(local) > 30 or len(local) < 2:
        return False
    
    # Domain must be reasonable  
    if len(domain) > 50 or len(domain) < 5:
        return False
        
    return True

def get_clean_professors():
    """Get ultra-clean professor list"""
    print("🧹 Ultra-Clean Email Validation")
    print("=" * 40)
    
    # Load cleaned database
    clean_db_path = 'production/databases/CLEANED_MASTER_EMAIL_DATABASE.csv'
    if not os.path.exists(clean_db_path):
        print("❌ Cleaned database not found. Run clean_database.py first!")
        return None
    
    df = pd.read_csv(clean_db_path)
    print(f"📊 Loaded {len(df)} pre-cleaned records")
    
    # Apply ultra-strict validation
    df['ultra_valid'] = df['email'].apply(ultra_validate_email)
    df_ultra_clean = df[df['ultra_valid']].copy()
    df_ultra_clean = df_ultra_clean.drop('ultra_valid', axis=1)
    
    # Remove already contacted emails (comprehensive check)
    contacted_emails = set()
    
    # Load from all possible sources
    sources = [
        'email_log.csv',
        'sent_emails_log.json',
        'followup_log.csv'
    ]
    
    for source in sources:
        try:
            if source.endswith('.csv'):
                source_df = pd.read_csv(source, on_bad_lines='skip')
                for col in source_df.columns:
                    if source_df[col].dtype == 'object':
                        emails = source_df[col].str.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}').explode().dropna()
                        contacted_emails.update(emails.str.lower().str.strip())
            elif source.endswith('.json'):
                import json
                with open(source, 'r') as f:
                    data = json.load(f)
                    if 'sent_emails' in data:
                        contacted_emails.update([str(e).lower().strip() for e in data['sent_emails']])
        except:
            continue
    
    print(f"🛡️ Found {len(contacted_emails)} previously contacted emails")
    
    # Filter out contacted emails
    df_ultra_clean = df_ultra_clean[~df_ultra_clean['email'].str.lower().isin(contacted_emails)]
    
    ultra_count = len(df_ultra_clean)
    removed_count = len(df) - ultra_count
    
    print(f"✅ Ultra-clean validation complete:")
    print(f"   - Pre-cleaned records: {len(df)}")
    print(f"   - Ultra-clean records: {ultra_count}")
    print(f"   - Additional removed: {removed_count}")
    print(f"   - Ultra success rate: {(ultra_count/len(df))*100:.1f}%")
    
    return df_ultra_clean

def run_safe_campaign():
    """Run a safe, validated campaign"""
    
    # Get ultra-clean professors
    df_professors = get_clean_professors()
    if df_professors is None or len(df_professors) == 0:
        print("❌ No clean professors available!")
        return
    
    # Show top candidates
    print(f"\n🎯 Top 5 Ultra-Clean Professor Candidates:")
    for i, row in df_professors.head(5).iterrows():
        print(f"   {i+1}. {row.get('name', 'Unknown')} - {row.get('university', 'Unknown')} ({row['email']})")
    
    # Safety confirmation
    print(f"\n⚠️  SAFETY CHECK:")
    print(f"   - Database: Ultra-cleaned and validated")
    print(f"   - Duplicates: Comprehensive check completed")
    print(f"   - Email format: Strictly validated")
    print(f"   - Batch size: 2 emails only")
    
    confirm = input(f"\n✅ Send 2 ultra-validated emails to TOP professors? (y/n): ").strip().lower()
    
    if confirm == 'y':
        # Prepare ultra-clean database for ULTRA system
        top_2 = df_professors.head(2)
        top_2.to_csv('professors_database.csv', index=False)
        
        # Set environment variables
        os.environ['EMAIL_ADDRESS'] = "tripathy.anamay23@gmail.com"
        os.environ['EMAIL_PASSWORD'] = "xctf elgn llfo aohf"
        os.environ['MAX_EMAILS_PER_SESSION'] = '2'
        os.environ['CONCURRENT_WORKERS'] = '1'
        
        print(f"\n🚀 Launching ULTRA campaign with 2 ultra-validated professors...")
        
        try:
            from ULTRA_HTML_BULK_SYSTEM import UltraHTMLBulkCampaign
            campaign = UltraHTMLBulkCampaign()
            campaign.run_bulk_campaign()
            print("\n🎉 Ultra-safe campaign completed!")
        except Exception as e:
            print(f"❌ Campaign error: {e}")
    else:
        print("🛑 Campaign cancelled - Safety first!")

if __name__ == "__main__":
    run_safe_campaign()
