#!/usr/bin/env python3
"""
Data Cleanup Script for InternMailer
===================================
Fixes data synchronization issues and provides comprehensive status.
"""

import sys
import os
sys.path.append('scheduler')
from streamlit_api import get_followup_manager
from src.professor_tracker import ProfessorTracker
import json

def main():
    print("🔧 InternMailer Data Cleanup & Status Report")
    print("=" * 50)
    
    # Initialize managers
    followup_manager = get_followup_manager('data')
    professor_tracker = ProfessorTracker()
    
    print("\n📊 CURRENT DATA STATUS:")
    print("-" * 30)
    
    # Get analytics
    analytics = followup_manager.get_analytics()
    stats = professor_tracker.get_stats()
    
    print(f"📧 Professors Tracked: {stats['total_emailed']}")
    print(f"📅 Total Follow-ups: {analytics['total_followups']}")
    print(f"⏰ Scheduled: {analytics['scheduled_followups']}")
    print(f"✅ Sent: {analytics['sent_followups']}")
    print(f"⚠️  Overdue: {analytics['overdue_followups']}")
    print(f"❌ Cancelled: {analytics['cancelled_followups']}")
    
    # Campaign summary
    campaign_summary = followup_manager.get_campaign_summary()
    print(f"\n🏗️  Total Campaigns: {campaign_summary['total_campaigns']}")
    
    test_campaigns = [c for c in campaign_summary['campaigns'] if c['is_test']]
    live_campaigns = [c for c in campaign_summary['campaigns'] if not c['is_test']]
    
    print(f"🧪 Test Campaigns: {len(test_campaigns)}")
    print(f"🚀 Live Campaigns: {len(live_campaigns)}")
    
    if test_campaigns:
        print("\n🧪 TEST CAMPAIGNS FOUND:")
        for campaign in test_campaigns:
            print(f"  - {campaign['name']} ({campaign['total_followups']} follow-ups)")
    
    if live_campaigns:
        print("\n🚀 LIVE CAMPAIGNS:")
        for campaign in live_campaigns:
            print(f"  - {campaign['name']} ({campaign['total_followups']} follow-ups, {campaign['total_emails']} emails sent)")
    
    # Ask for cleanup
    if test_campaigns:
        print(f"\n⚠️  Found {len(test_campaigns)} test campaigns.")
        response = input("Do you want to clean up test campaigns? (y/n): ").lower().strip()
        
        if response == 'y':
            removed_count = followup_manager.cleanup_test_campaigns()
            print(f"✅ Cleaned up {removed_count} test campaigns!")
            
            # Refresh analytics
            analytics = followup_manager.get_analytics()
            print(f"\n📊 UPDATED STATUS:")
            print(f"📅 Total Follow-ups: {analytics['total_followups']}")
            print(f"⏰ Scheduled: {analytics['scheduled_followups']}")
            print(f"⚠️  Overdue: {analytics['overdue_followups']}")
        else:
            print("❌ Cleanup cancelled.")
    
    # Data consistency check
    print("\n🔍 DATA CONSISTENCY CHECK:")
    print("-" * 30)
    
    # Check for orphaned follow-ups
    all_followups = followup_manager.get_all_followups()
    campaigns = followup_manager.get_campaigns()
    campaign_ids = [c['id'] for c in campaigns]
    
    orphaned_followups = [f for f in all_followups if f.get('campaign_id') not in campaign_ids]
    
    if orphaned_followups:
        print(f"⚠️  Found {len(orphaned_followups)} orphaned follow-ups")
    else:
        print("✅ No orphaned follow-ups found")
    
    # Check date formatting issues
    date_issues = 0
    for followup in all_followups:
        if followup.get('scheduled_at'):
            try:
                followup_manager._parse_datetime(followup['scheduled_at'])
            except:
                date_issues += 1
    
    if date_issues:
        print(f"⚠️  Found {date_issues} follow-ups with date parsing issues")
    else:
        print("✅ All dates parse correctly")
    
    print(f"\n✅ Data cleanup complete!")
    print(f"📈 Summary: {analytics['total_followups']} follow-ups across {len(campaigns)} campaigns")
    
    if analytics['overdue_followups'] > 0:
        print(f"💡 Tip: You have {analytics['overdue_followups']} overdue follow-ups. Consider processing them in the Follow-ups page.")

if __name__ == "__main__":
    main()
