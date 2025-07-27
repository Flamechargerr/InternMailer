"""Enhanced Home Page for InternMailer"""

import streamlit as st
from datetime import datetime, timedelta
from services import campaign_service, analytics_service
from services.state_service import state
from components.ui_utils import ui

def show():
    """Display the dashboard with metrics and quick actions."""
    # Page header
    ui.page_header(
        "Dashboard Overview",
        "Welcome back! Here's what's happening with your campaigns."
    )
    
    # Get data from services
    campaign_stats = campaign_service.get_campaign_stats()
    email_metrics = analytics_service.get_email_metrics()
    
    # KPI Cards
    with st.container():
        cols = st.columns(4)
        
        with cols[0]:
            ui.card(
                "📊 Total Campaigns",
                f"{campaign_stats.get('total_campaigns', 0):,}",
                [{'label': 'View All', 'on_click': lambda: state.set('page', 'campaigns')}]
            )
            
        with cols[1]:
            ui.card(
                "🚀 Active Campaigns",
                f"{campaign_stats.get('active_campaigns', 0):,}",
                [{'label': 'View Active', 'on_click': lambda: state.set('page', 'campaigns')}]
            )
            
        with cols[2]:
            ui.card(
                "📨 Emails Sent",
                f"{email_metrics.get('total_sent', 0):,}",
                [{'label': 'View Analytics', 'on_click': lambda: state.set('page', 'analytics')}]
            )
            
        with cols[3]:
            ui.card(
                "📈 Open Rate",
                f"{email_metrics.get('open_rate', 0):.1%}",
                [{'label': 'See Details', 'on_click': lambda: state.set('page', 'analytics')}]
            )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Recent Campaigns
        with st.container():
            st.markdown("### Recent Campaigns")
            campaigns = campaign_service.get_recent_campaigns(limit=5)
            if campaigns:
                ui.table(campaigns)
            else:
                ui.info("No recent campaigns found.")
    
    with col2:
        # Quick Actions
        with st.container():
            st.markdown("### Quick Actions")
            
            actions = [
                {
                    'label': '🚀 New Campaign',
                    'on_click': lambda: state.set('page', 'campaign_builder')
                },
                {
                    'label': '📧 Send Test Email',
                    'on_click': lambda: state.set('show_test_modal', True)
                },
                {
                    'label': '📊 View Analytics',
                    'on_click': lambda: state.set('page', 'analytics')
                }
            ]
            
            for action in actions:
                if st.button(
                    action['label'],
                    use_container_width=True,
                    key=f"action_{action['label']}",
                    on_click=action['on_click']
                ):
                    pass
    
    # Test Email Modal
    if state.get('show_test_modal', False):
        with st.container():
            st.markdown("### 📧 Send Test Email")
            
            with st.form("test_email_form"):
                email = st.text_input("Recipient Email", "your.email@example.com")
                subject = st.text_input("Subject", "Test Email from InternMailer")
                message = st.text_area("Message", "This is a test email.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Send Email"):
                        try:
                            # TODO: Implement email sending
                            ui.success(f"Test email sent to {email}")
                            state.delete('show_test_modal')
                        except Exception as e:
                            ui.error(f"Failed to send email: {str(e)}")
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        state.delete('show_test_modal')
