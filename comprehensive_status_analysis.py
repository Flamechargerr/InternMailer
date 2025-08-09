#!/usr/bin/env python3
"""
Comprehensive Status Analysis - InternMailing System
"""

import pandas as pd
import json
import os

def analyze_comprehensive_status():
    """Analyze comprehensive status of all databases and campaigns"""
    print("🔍 COMPREHENSIVE STATUS ANALYSIS - INTERNMAILING SYSTEM")
    print("=" * 80)
    
    stats = {}
    
    # HR Database Analysis
    try:
        with open('data/enhanced_hr_contacts.json', 'r') as f:
            hr_data = json.load(f)
        stats['hr_total'] = len(hr_data)
        
        # Check HR contact status
        hr_contacted = 0
        hr_pending = 0
        for contact in hr_data:
            if contact.get('status') in ['contacted', 'followed_up', 'in_talks']:
                hr_contacted += 1
            else:
                hr_pending += 1
        
        stats['hr_contacted'] = hr_contacted
        stats['hr_pending'] = hr_pending
    except:
        stats['hr_total'] = 0
        stats['hr_contacted'] = 0
        stats['hr_pending'] = 0
    
    # Professor Database Analysis
    try:
        df_main = pd.read_csv('data/scraped_professors_final.csv')
        stats['prof_main'] = len(df_main)
        stats['prof_main_with_emails'] = len(df_main[df_main['email'].notna() & (df_main['email'] != '')])
    except:
        stats['prof_main'] = 0
        stats['prof_main_with_emails'] = 0
    
    try:
        df_archive = pd.read_csv('data/archive/professors_final.csv', on_bad_lines='skip')
        stats['prof_archive'] = len(df_archive)
        stats['prof_archive_with_emails'] = len(df_archive[df_archive['Email'].notna() & (df_archive['Email'] != '')])
    except:
        stats['prof_archive'] = 0
        stats['prof_archive_with_emails'] = 0
    
    try:
        df_master = pd.read_csv('data/professors_master_list.csv')
        stats['prof_master'] = len(df_master)
    except:
        stats['prof_master'] = 0
    
    try:
        with open('data/scraped_professors_cache.json', 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        stats['prof_cache'] = len(cache_data)
    except:
        stats['prof_cache'] = 0
    
    try:
        df_enhanced = pd.read_csv('data/enhanced_background_emails_20250804_204317.csv')
        stats['prof_enhanced_total'] = len(df_enhanced)
        stats['prof_enhanced_unique'] = df_enhanced['email'].nunique() if 'email' in df_enhanced.columns else 0
    except:
        stats['prof_enhanced_total'] = 0
        stats['prof_enhanced_unique'] = 0
    
    # Emailed Professors Analysis
    try:
        with open('data/emailed_professors.json', 'r') as f:
            emailed_data = json.load(f)
        stats['prof_emailed'] = len(emailed_data['professors'])
    except:
        stats['prof_emailed'] = 0
    
    # Follow-ups Analysis
    try:
        with open('data/followups.json', 'r') as f:
            followups_data = json.load(f)
        stats['followups_total'] = len(followups_data)
    except:
        stats['followups_total'] = 0
    
    # Calculate totals
    total_professors = (stats['prof_main_with_emails'] + stats['prof_archive_with_emails'] + 
                       stats['prof_master'] + stats['prof_cache'] + stats['prof_enhanced_unique'])
    remaining_professors = total_professors - stats['prof_emailed']
    
    # Display Results
    print("\n🎯 HR CAMPAIGN STATUS:")
    print(f"   • Total HR Contacts: {stats['hr_total']:,}")
    print(f"   • Already Contacted: {stats['hr_contacted']:,}")
    print(f"   • Pending Contact: {stats['hr_pending']:,}")
    print(f"   • Contact Rate: {(stats['hr_contacted']/stats['hr_total']*100):.1f}%" if stats['hr_total'] > 0 else "   • Contact Rate: 0%")
    
    print("\n🎓 PROFESSOR CAMPAIGN STATUS:")
    print(f"   • Main Database: {stats['prof_main']:,} (with emails: {stats['prof_main_with_emails']:,})")
    print(f"   • Archive Database: {stats['prof_archive']:,} (with emails: {stats['prof_archive_with_emails']:,})")
    print(f"   • Master List: {stats['prof_master']:,}")
    print(f"   • Cache Database: {stats['prof_cache']:,}")
    print(f"   • Enhanced Background: {stats['prof_enhanced_unique']:,} unique emails")
    print(f"   • Total Professors Available: {total_professors:,}")
    print(f"   • Already Emailed: {stats['prof_emailed']:,}")
    print(f"   • Remaining to Email: {remaining_professors:,}")
    print(f"   • Email Rate: {(stats['prof_emailed']/total_professors*100):.1f}%" if total_professors > 0 else "   • Email Rate: 0%")
    
    print("\n📈 FOLLOW-UPS STATUS:")
    print(f"   • Total Follow-ups: {stats['followups_total']:,}")
    print(f"   • Follow-up Rate: {(stats['followups_total']/stats['prof_emailed']*100):.1f}%" if stats['prof_emailed'] > 0 else "   • Follow-up Rate: 0%")
    
    print("\n📊 OVERALL CAMPAIGN SUMMARY:")
    print(f"   • Total Contacts Available: {stats['hr_total'] + total_professors:,}")
    print(f"   • Total Contacted: {stats['hr_contacted'] + stats['prof_emailed']:,}")
    print(f"   • Total Remaining: {stats['hr_pending'] + remaining_professors:,}")
    print(f"   • Overall Contact Rate: {((stats['hr_contacted'] + stats['prof_emailed'])/(stats['hr_total'] + total_professors)*100):.1f}%")
    
    return stats

def check_streamlit_integration():
    """Check Streamlit app integration status"""
    print("\n🖥️ STREAMLIT APP INTEGRATION STATUS:")
    print("=" * 50)
    
    # Check if main app exists
    if os.path.exists('app.py'):
        print("✅ Main Streamlit app: app.py - EXISTS")
    else:
        print("❌ Main Streamlit app: app.py - MISSING")
    
    # Check if pages exist
    pages_dir = 'pages'
    if os.path.exists(pages_dir):
        pages = os.listdir(pages_dir)
        print(f"✅ Pages directory: {len(pages)} pages found")
        for page in pages:
            print(f"   • {page}")
    else:
        print("❌ Pages directory: MISSING")
    
    # Check if templates exist
    templates_dir = 'templates'
    if os.path.exists(templates_dir):
        templates = os.listdir(templates_dir)
        print(f"✅ Templates directory: {len(templates)} templates found")
        for template in templates:
            print(f"   • {template}")
    else:
        print("❌ Templates directory: MISSING")
    
    # Check if data files exist
    data_files = [
        'data/enhanced_hr_contacts.json',
        'data/scraped_professors_final.csv',
        'data/emailed_professors.json',
        'data/followups.json'
    ]
    
    print("\n📁 DATA FILES STATUS:")
    for file_path in data_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} - EXISTS")
        else:
            print(f"❌ {file_path} - MISSING")

if __name__ == "__main__":
    analyze_comprehensive_status()
    check_streamlit_integration() 