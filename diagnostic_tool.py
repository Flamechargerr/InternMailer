#!/usr/bin/env python3
"""
Professor Outreach Diagnostic Tool
Helps identify why campaigns are finding so few eligible professors
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def load_professor_csv():
    """Load the professor CSV file"""
    try:
        df = pd.read_csv('professors_final.csv', on_bad_lines='skip', encoding='utf-8')
        print(f"✅ Loaded {len(df)} professors from CSV")
        return df
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return pd.DataFrame()

def load_tracking_data():
    """Load the professor tracking data"""
    try:
        with open('data/emailed_professors.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ Loaded tracking data with {len(data.get('professors', []))} entries")
            return data
    except Exception as e:
        print(f"❌ Error loading tracking data: {e}")
        return {"professors": []}

def analyze_eligibility(df, tracking_data, cooldown_days=30):
    """Analyze professor eligibility"""
    print(f"\n📊 PROFESSOR ELIGIBILITY ANALYSIS")
    print("=" * 50)
    
    total_professors = len(df)
    print(f"Total professors in CSV: {total_professors}")
    
    # Get tracked emails
    tracked_emails = set()
    dry_run_emails = set()
    sent_emails = set()
    recent_contacts = set()
    
    cutoff_date = datetime.now() - timedelta(days=cooldown_days)
    
    for prof in tracking_data.get('professors', []):
        email = prof.get('email', '').lower()
        status = prof.get('status', '')
        last_emailed = prof.get('last_emailed', '')
        
        tracked_emails.add(email)
        
        if status == 'dry_run':
            dry_run_emails.add(email)
        elif status == 'sent':
            sent_emails.add(email)
            
            # Check if recent
            if last_emailed:
                try:
                    contact_date = datetime.fromisoformat(last_emailed)
                    if contact_date > cutoff_date:
                        recent_contacts.add(email)
                except:
                    pass
    
    print(f"Total tracked emails: {len(tracked_emails)}")
    print(f"  - Dry run emails: {len(dry_run_emails)}")
    print(f"  - Sent emails: {len(sent_emails)}")
    print(f"  - Recent contacts (within {cooldown_days} days): {len(recent_contacts)}")
    
    # Calculate eligibility
    csv_emails = set(df['Email'].str.lower())
    eligible_new = csv_emails - tracked_emails
    eligible_dry_run_upgrade = csv_emails & dry_run_emails
    eligible_cooldown_expired = (csv_emails & sent_emails) - recent_contacts
    
    total_eligible = len(eligible_new) + len(eligible_dry_run_upgrade) + len(eligible_cooldown_expired)
    
    print(f"\n🎯 ELIGIBILITY BREAKDOWN:")
    print(f"  - New professors (never contacted): {len(eligible_new)}")
    print(f"  - Dry run upgrades available: {len(eligible_dry_run_upgrade)}")
    print(f"  - Cooldown expired: {len(eligible_cooldown_expired)}")
    print(f"  - TOTAL ELIGIBLE: {total_eligible}")
    
    eligibility_rate = (total_eligible / total_professors) * 100 if total_professors > 0 else 0
    print(f"  - Eligibility rate: {eligibility_rate:.1f}%")
    
    return {
        'total_professors': total_professors,
        'total_eligible': total_eligible,
        'eligible_new': eligible_new,
        'eligible_dry_run_upgrade': eligible_dry_run_upgrade,
        'eligible_cooldown_expired': eligible_cooldown_expired,
        'eligibility_rate': eligibility_rate
    }

def show_sample_eligible(df, eligible_emails, category_name, count=5):
    """Show sample eligible professors"""
    if not eligible_emails:
        return
    
    print(f"\n📋 SAMPLE {category_name.upper()} PROFESSORS:")
    sample_emails = list(eligible_emails)[:count]
    
    for email in sample_emails:
        prof_row = df[df['Email'].str.lower() == email.lower()]
        if not prof_row.empty:
            prof = prof_row.iloc[0]
            print(f"  • {prof['Name']} - {prof['University']}")
            print(f"    📧 {prof['Email']}")
            print(f"    🔬 {prof['Research Area']}")
            print()

def identify_campaign_issues():
    """Identify potential issues with campaign execution"""
    print(f"\n🔍 POTENTIAL CAMPAIGN ISSUES:")
    print("=" * 50)
    
    issues = []
    
    # Check for common filtering issues
    print("Checking for common issues...")
    
    # Check if batch size is too small
    print("❓ Is batch size limiting results?")
    print("   → Check if batch size slider is set too low (should be 10+ for testing)")
    
    # Check for country filtering
    print("❓ Is country filtering too restrictive?")
    print("   → Try leaving country selection empty for global search")
    
    # Check professor CSV loading
    print("❓ Is professor CSV being read correctly?")
    print("   → Check if 'professors_final.csv' exists and has valid data")
    
    # Check for duplicate prevention being too aggressive
    print("❓ Is duplicate prevention too aggressive?")
    print("   → Check if too many professors are marked as contacted")

def main():
    """Main diagnostic function"""
    print("🚀 PROFESSOR OUTREACH DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # Load data
    df = load_professor_csv()
    if df.empty:
        print("❌ Cannot proceed without professor data")
        return
    
    tracking_data = load_tracking_data()
    
    # Analyze eligibility
    analysis = analyze_eligibility(df, tracking_data)
    
    # Show samples
    show_sample_eligible(df, analysis['eligible_new'], "NEW", 5)
    show_sample_eligible(df, analysis['eligible_dry_run_upgrade'], "DRY RUN UPGRADE", 3)
    show_sample_eligible(df, analysis['eligible_cooldown_expired'], "COOLDOWN EXPIRED", 3)
    
    # Identify issues
    identify_campaign_issues()
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 50)
    
    if analysis['total_eligible'] == 0:
        print("❌ NO ELIGIBLE PROFESSORS FOUND!")
        print("   → Consider clearing some tracking data or expanding your professor list")
        print("   → Check if cooldown period is too long (currently 30 days)")
    elif analysis['total_eligible'] < 10:
        print("⚠️  VERY FEW ELIGIBLE PROFESSORS")
        print(f"   → Only {analysis['total_eligible']} professors available")
        print("   → Consider expanding search criteria or clearing old tracking data")
    elif analysis['eligibility_rate'] < 50:
        print("⚠️  LOW ELIGIBILITY RATE")
        print(f"   → {analysis['eligibility_rate']:.1f}% of professors are eligible")
        print("   → Most professors have been contacted recently")
    else:
        print("✅ GOOD ELIGIBILITY RATE")
        print(f"   → {analysis['total_eligible']} professors available ({analysis['eligibility_rate']:.1f}%)")
    
    print(f"\n🔧 QUICK FIXES:")
    print("1. Try increasing batch size to 20+ for testing")
    print("2. Leave country filter empty for global search")
    print("3. Check that your CSV file has diverse professors")
    print("4. Consider clearing old dry run entries if needed")

if __name__ == "__main__":
    main()
