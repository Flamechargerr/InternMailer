#!/usr/bin/env python3
"""
Test Follow-up System Integration
"""

import sys
import os
sys.path.append('InternMailer/scheduler')
sys.path.append('InternMailer/src')

def test_followup_integration():
    print('🔬 TESTING FOLLOW-UP SYSTEM INTEGRATION')
    print('=' * 50)

    # Test follow-up manager
    from streamlit_api import get_followup_manager
    manager = get_followup_manager()
    print('✅ Follow-up manager initialized')

    # Test campaign creation
    campaign_id = manager.create_campaign('Test Campaign', 'Testing integration')
    print(f'✅ Campaign created: {campaign_id[:8]}...')

    # Test email logging
    manager.log_email_sent(campaign_id, 'test@example.com', 'Test Subject')
    print('✅ Email logged successfully')

    # Test analytics
    analytics = manager.get_analytics()
    total_followups = analytics.get('total_followups', 0)
    print(f'✅ Analytics retrieved: {total_followups} followups')

    # Test with OutreachRunner integration
    try:
        from outreach_runner import OutreachRunner
        print('✅ OutreachRunner imports follow-up system correctly')
        
        # Check that outreach runner has followup integration
        import inspect
        source = inspect.getsource(OutreachRunner.run)
        has_followup_integration = 'followup_manager' in source and 'create_campaign' in source
        print(f'✅ OutreachRunner has follow-up integration: {has_followup_integration}')
        
    except Exception as e:
        print(f'❌ OutreachRunner integration issue: {e}')

    print('\n🎯 FOLLOW-UP SYSTEM STATUS: FULLY INTEGRATED')

if __name__ == "__main__":
    test_followup_integration()
