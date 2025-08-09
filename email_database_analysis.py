#!/usr/bin/env python3
"""
Email Database Analysis - Count HR contacts vs Professors
"""

import pandas as pd
import json
import os

def analyze_email_databases():
    """Analyze all email databases"""
    print("📊 EMAIL DATABASE ANALYSIS")
    print("=" * 60)
    
    stats = {}
    
    # Check HR contacts
    try:
        if os.path.exists('data/enhanced_hr_contacts.json'):
            with open('data/enhanced_hr_contacts.json', 'r') as f:
                hr_data = json.load(f)
            stats['hr_contacts'] = len(hr_data) if isinstance(hr_data, list) else len(hr_data.get('contacts', []))
        else:
            stats['hr_contacts'] = 0
    except:
        stats['hr_contacts'] = 0
    
    # Check HR emails
    try:
        if os.path.exists('data/hr_emails.json'):
            with open('data/hr_emails.json', 'r') as f:
                hr_emails_data = json.load(f)
            stats['hr_emails'] = len(hr_emails_data) if isinstance(hr_emails_data, list) else len(hr_emails_data.get('emails', []))
        else:
            stats['hr_emails'] = 0
    except:
        stats['hr_emails'] = 0
    
    # Main professors database
    try:
        df_main = pd.read_csv('data/scraped_professors_final.csv')
        stats['main_professors'] = len(df_main)
        stats['main_professors_with_emails'] = len(df_main[df_main['email'].notna() & (df_main['email'] != '')])
    except:
        stats['main_professors'] = 0
        stats['main_professors_with_emails'] = 0
    
    # Archive professors database
    try:
        df_archive = pd.read_csv('data/archive/professors_final.csv', on_bad_lines='skip')
        stats['archive_professors'] = len(df_archive)
        stats['archive_professors_with_emails'] = len(df_archive[df_archive['Email'].notna() & (df_archive['Email'] != '')])
    except:
        stats['archive_professors'] = 0
        stats['archive_professors_with_emails'] = 0
    
    # Enhanced background emails
    try:
        df_enhanced = pd.read_csv('data/enhanced_background_emails_20250804_204317.csv')
        stats['enhanced_total'] = len(df_enhanced)
        stats['enhanced_unique'] = df_enhanced['email'].nunique() if 'email' in df_enhanced.columns else 0
    except:
        stats['enhanced_total'] = 0
        stats['enhanced_unique'] = 0
    
    # Master list
    try:
        df_master = pd.read_csv('data/professors_master_list.csv')
        stats['master_list'] = len(df_master)
    except:
        stats['master_list'] = 0
    
    # Cache database
    try:
        with open('data/scraped_professors_cache.json', 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        stats['cache_professors'] = len(cache_data)
    except:
        stats['cache_professors'] = 0
    
    # Emailed professors
    try:
        with open('data/emailed_professors.json', 'r') as f:
            emailed_data = json.load(f)
        stats['emailed_professors'] = len(emailed_data['professors'])
    except:
        stats['emailed_professors'] = 0
    
    # Display results
    print("\n🎯 HR CONTACTS (for HR Template):")
    print(f"   • Enhanced HR Contacts: {stats['hr_contacts']:,}")
    print(f"   • HR Emails: {stats['hr_emails']:,}")
    print(f"   • Total HR Contacts: {stats['hr_contacts'] + stats['hr_emails']:,}")
    
    print("\n🎓 PROFESSORS (for Academic Template):")
    print(f"   • Main Database: {stats['main_professors']:,} (with emails: {stats['main_professors_with_emails']:,})")
    print(f"   • Archive Database: {stats['archive_professors']:,} (with emails: {stats['archive_professors_with_emails']:,})")
    print(f"   • Master List: {stats['master_list']:,}")
    print(f"   • Cache Database: {stats['cache_professors']:,}")
    print(f"   • Enhanced Background: {stats['enhanced_unique']:,} unique emails")
    
    print("\n📊 SUMMARY:")
    print(f"   • Total HR Contacts Available: {stats['hr_contacts'] + stats['hr_emails']:,}")
    print(f"   • Total Professors Available: {stats['main_professors_with_emails'] + stats['archive_professors_with_emails'] + stats['master_list'] + stats['cache_professors'] + stats['enhanced_unique']:,}")
    print(f"   • Already Contacted: {stats['emailed_professors']:,}")
    print(f"   • Remaining to Contact: {stats['main_professors_with_emails'] + stats['archive_professors_with_emails'] + stats['master_list'] + stats['cache_professors'] + stats['enhanced_unique'] - stats['emailed_professors']:,}")
    
    return stats

if __name__ == "__main__":
    analyze_email_databases() 