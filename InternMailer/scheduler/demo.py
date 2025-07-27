#!/usr/bin/env python3
"""
Demo script for the Follow-up Scheduler Backend

This script demonstrates the main functionality of the FollowupManager:
- Creating campaigns
- Logging sent emails
- Overdue detection
- Analytics
"""

import os
import sys
import time
from datetime import datetime, timezone, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scheduler.streamlit_api import FollowupManager

def main():
    print("🚀 Follow-up Scheduler Backend Demo")
    print("=" * 50)
    
    # Initialize the manager with a demo data directory
    demo_dir = 'demo_data'
    manager = FollowupManager(data_dir=demo_dir)
    
    print(f"📁 Using data directory: {demo_dir}")
    print()
    
    # 1. Create some campaigns
    print("1️⃣ Creating Campaigns")
    print("-" * 30)
    
    campaign1 = manager.create_campaign(
        "Research Internship Outreach", 
        "Reaching out to professors for research internship opportunities"
    )
    campaign2 = manager.create_campaign(
        "Industry Applications", 
        "Following up on job applications in tech industry"
    )
    
    print(f"✅ Created campaign: {campaign1[:8]}...")
    print(f"✅ Created campaign: {campaign2[:8]}...")
    print()
    
    # 2. Log some sent emails
    print("2️⃣ Logging Sent Emails")
    print("-" * 30)
    
    emails = [
        ("prof.smith@university.edu", "Research Internship Inquiry - CS Student"),
        ("prof.jones@tech.edu", "Summer Research Position Application"),
        ("hr@techcorp.com", "Software Engineer Position Follow-up"),
        ("recruiting@startup.io", "Frontend Developer Application Status")
    ]
    
    for i, (email, subject) in enumerate(emails):
        campaign_id = campaign1 if i < 2 else campaign2
        manager.log_email_sent(campaign_id, email, subject)
        print(f"📧 Logged email to {email}")
    
    print()
    
    # 3. Show initial analytics
    print("3️⃣ Initial Analytics")
    print("-" * 30)
    
    analytics = manager.get_analytics()
    print(f"📊 Total followups: {analytics['total_followups']}")
    print(f"📅 Scheduled: {analytics['scheduled_followups']}")
    print(f"⏰ Overdue: {analytics['overdue_followups']}")
    print(f"❌ Cancelled: {analytics['cancelled_followups']}")
    print(f"🏢 Campaigns: {len(analytics['campaigns'])}")
    print()
    
    # 4. Simulate overdue followups by manually adjusting dates
    print("4️⃣ Simulating Overdue Followups")
    print("-" * 30)
    
    followups = manager.get_all_followups()
    if followups:
        # Make first two followups overdue (scheduled 2 days ago)
        data = manager._read_data()
        past_time = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        
        for i, followup in enumerate(followups[:2]):
            data['followups'][followup['id']]['scheduled_at'] = past_time
            print(f"⏰ Made followup for {followup['email']} overdue")
        
        manager._write_data(data)
    print()
    
    # 5. Show overdue detection
    print("5️⃣ Overdue Detection")
    print("-" * 30)
    
    overdue_followups = manager.get_overdue_followups()
    print(f"🚨 Found {len(overdue_followups)} overdue followups:")
    
    for followup in overdue_followups:
        print(f"   • {followup['email']} - {followup['subject'][:50]}...")
    print()
    
    # 6. Process overdue followups
    print("6️⃣ Processing Overdue Followups")
    print("-" * 30)
    
    overdue_count = manager.process_overdue_followups()
    print(f"🔄 Processed {overdue_count} overdue followups")
    print()
    
    # 7. Demonstrate campaign management
    print("7️⃣ Campaign Management")
    print("-" * 30)
    
    campaigns = manager.get_campaigns()
    for campaign in campaigns:
        followups = manager.get_campaign_followups(campaign['id'])
        print(f"📋 {campaign['name']}: {len(followups)} followups")
        
        # Update campaign settings
        settings = {
            'followup_delay_days': 7,
            'max_followups': 3,
            'auto_followup': True
        }
        manager.update_campaign_settings(campaign['id'], settings)
        print(f"   ⚙️ Updated settings: {settings}")
    print()
    
    # 8. Final analytics
    print("8️⃣ Final Analytics")
    print("-" * 30)
    
    final_analytics = manager.get_analytics()
    print(f"📊 Total followups: {final_analytics['total_followups']}")
    print(f"📅 Scheduled: {final_analytics['scheduled_followups']}")
    print(f"⏰ Overdue: {final_analytics['overdue_followups']}")
    print(f"❌ Cancelled: {final_analytics['cancelled_followups']}")
    print()
    
    # 9. Demonstrate followup operations
    print("9️⃣ Followup Operations")
    print("-" * 30)
    
    if followups:
        # Cancel a followup
        followup_to_cancel = followups[-1]
        result = manager.cancel_followup(
            followup_to_cancel['id'], 
            "Company responded - no longer needed"
        )
        if result:
            print(f"❌ Cancelled followup for {followup_to_cancel['email']}")
        
        # Reschedule a followup
        if len(followups) > 1:
            followup_to_reschedule = followups[-2]
            new_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
            result = manager.reschedule_followup(followup_to_reschedule['id'], new_time)
            if result:
                print(f"📅 Rescheduled followup for {followup_to_reschedule['email']}")
    print()
    
    # 10. Show data persistence
    print("🔟 Data Persistence")
    print("-" * 30)
    
    print(f"💾 All data is stored in: {manager.followups_file}")
    print("🔄 Data persists across application restarts")
    print("🔒 File operations are atomic and thread-safe")
    print()
    
    print("✨ Demo completed successfully!")
    print(f"📁 Check {demo_dir}/followups.json to see the stored data")

if __name__ == "__main__":
    main()
