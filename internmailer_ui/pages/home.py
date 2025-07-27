"""
Home Page - InternMailer Dashboard

Main dashboard providing an overview of email campaigns, analytics, and quick actions.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services import email_service, campaign_service, analytics_service
from components.ui_components import (
    create_metric_card, create_section_header, create_info_card,
    create_status_badge, create_progress_card, create_stats_grid,
    create_alert_box, add_spacing, create_button
)

def show():
    """Display the home dashboard with key metrics and quick actions."""
    # Set page configuration
    st.set_page_config(layout="wide")
    
    # Load data
    campaign_stats = campaign_service.get_campaign_stats()
    email_metrics = analytics_service.get_email_metrics()
    recent_activities = analytics_service.get_recent_activities(limit=5)
    
    # Welcome header with description
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📧 InternMailer Dashboard")
        st.markdown("Monitor your email campaigns and manage your communication strategy")
    
    with col2:
        if st.button("🚀 Launch New Campaign", use_container_width=True):
            st.session_state.page = "campaign_builder"
            st.rerun()
    
    # Alert for system status
    system_status = email_service.check_email_service_status()
    if not system_status["connected"]:
        create_alert_box(
            f"⚠️ {system_status['message']} Check your email settings.",
            alert_type="warning"
        )
    
    add_spacing(1)
    
    # Key metrics
    stats_data = [
        {
            "title": "Active Campaigns",
            "value": f"{campaign_stats['active_campaigns']}",
            "delta": f"{campaign_stats['campaigns_change']}% from last month",
            "color": "#0066CC"
        },
        {
            "title": "Emails Sent",
            "value": f"{campaign_stats['emails_sent']:,}",
            "delta": f"{campaign_stats['emails_change']}% from last month",
            "color": "#28A745"
        },
        {
            "title": "Avg. Open Rate",
            "value": f"{email_metrics['open_rate']:.1%}",
            "delta": f"{email_metrics['open_rate_change']:.1%} from average",
            "color": "#17A2B8"
        },
        {
            "title": "Avg. Response Rate",
            "value": f"{email_metrics['response_rate']:.1%}",
            "delta": f"{email_metrics['response_rate_change']:.1%} from average",
            "color": "#6F42C1"
        }
    ]
    
    create_stats_grid(stats_data, columns=4)
    
    add_spacing(2)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Campaign Performance
        st.subheader("📈 Campaign Performance")
        
        # Time period selector
        time_period = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "This year"],
            key="time_period_selector"
        )
        
        # Performance metrics
        performance_data = analytics_service.get_performance_metrics(time_period)
        
        # Display performance metrics in a nice layout
        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("Emails Sent", f"{performance_data['emails_sent']:,}")
        with metric_cols[1]:
            st.metric("Open Rate", f"{performance_data['open_rate']:.1%}")
        with metric_cols[2]:
            st.metric("Click Rate", f"{performance_data['click_rate']:.1%}")
        with metric_cols[3]:
            st.metric("Response Rate", f"{performance_data['response_rate']:.1%}")
        
        # Performance chart (placeholder)
        st.line_chart(pd.DataFrame({
            'Date': pd.date_range(end=datetime.today(), periods=30, freq='D'),
            'Emails Sent': [10, 15, 12, 18, 25, 30, 28, 32, 40, 35, 45, 50, 48, 52, 55, 60, 65, 70, 68, 72, 75, 80, 85, 82, 88, 90, 95, 100, 98, 105],
            'Open Rate': [0.2, 0.22, 0.25, 0.23, 0.27, 0.26, 0.28, 0.3, 0.32, 0.31, 0.33, 0.35, 0.34, 0.36, 0.35, 0.37, 0.38, 0.4, 0.39, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.5, 0.51]
        }).set_index('Date'))
        
        # Recent Campaigns
        st.subheader("📋 Recent Campaigns")
        recent_campaigns = campaign_service.get_recent_campaigns(limit=5)
        
        if recent_campaigns.empty:
            st.info("No recent campaigns found. Create your first campaign to get started!")
        else:
            st.dataframe(
                recent_campaigns,
                column_config={
                    "name": "Campaign Name",
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        help="Campaign status",
                        options=["Draft", "Scheduled", "Active", "Paused", "Completed"],
                        width="small"
                    ),
                    "emails_sent": "Sent",
                    "open_rate": st.column_config.ProgressColumn(
                        "Open Rate",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "start_date": "Start Date",
                    "end_date": "End Date"
                },
                hide_index=True,
                use_container_width=True
            )
    
    with col2:
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("📤 Send Test Email", use_container_width=True):
            st.session_state.show_test_email = True
        
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()
            
        if st.button("📝 Create New Template", use_container_width=True):
            st.session_state.page = "templates"
            st.rerun()
        
        if st.button("👥 Manage Contacts", use_container_width=True):
            st.session_state.page = "contacts"
            st.rerun()
        
        add_spacing(1)
        
        # System Status
        st.subheader("🔧 System Status")
        
        status_cols = st.columns([1, 2])
        with status_cols[0]:
            st.metric("Email Service", "Connected" if system_status["connected"] else "Disconnected")
            st.metric("Storage Used", f"{system_status['storage_used']}%")
        
        # Recent Activity
        st.subheader("🔄 Recent Activity")
        
        if recent_activities.empty:
            st.info("No recent activities to display.")
        else:
            for _, activity in recent_activities.iterrows():
                st.markdown(f"""
                <div class="card" style="margin-bottom: 10px; padding: 10px;">
                    <div style="font-weight: 500;">{activity['action']}</div>
                    <div style="font-size: 0.8em; color: #666;">{activity['timestamp']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Test Email Modal
    if st.session_state.get('show_test_email', False):
        with st.expander("✉️ Send Test Email", expanded=True):
            email_form = st.form("test_email_form")
            with email_form:
                email = st.text_input("Email Address", "your.email@example.com")
                subject = st.text_input("Subject", "Test Email from InternMailer")
                message = st.text_area("Message", "This is a test email sent from InternMailer.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Send Test Email"):
                        try:
                            email_service.send_email(
                                to_email=email,
                                subject=subject,
                                body=message
                            )
                            st.success("Test email sent successfully!")
                            st.session_state.show_test_email = False
                        except Exception as e:
                            st.error(f"Failed to send test email: {str(e)}")
                
                with col2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.show_test_email = False
                        st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Progress cards for active campaigns
        create_progress_card("Newsletter Campaign", 75, color="#0066CC")
        create_progress_card("Product Launch", 45, color="#28A745")
        create_progress_card("Customer Survey", 90, color="#17A2B8")
    
    with col2:
        # Information cards
        create_info_card(
            "Recent Campaign Performance",
            "Your latest newsletter achieved a 28% open rate, which is 15% above industry average. The product announcement generated 156 new leads.",
            icon="📈"
        )
        
        create_info_card(
            "Upcoming Scheduled Campaigns",
            "You have 3 campaigns scheduled for this week: Weekly Newsletter (Tomorrow), Product Update (Wednesday), and Feedback Survey (Friday).",
            icon="⏰"
        )
    
    add_spacing(2)
    
    # Status badges for system health
    create_section_header("🔧 System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.write("**Email Service:**")
        create_status_badge("Online", "success")
    
    with col2:
        st.write("**Analytics:**")
        create_status_badge("Active", "success")
    
    with col3:
        st.write("**Templates:**")
        create_status_badge("Updated", "info")
    
    with col4:
        st.write("**Queue Status:**")
        create_status_badge("Processing", "warning")
    
    add_spacing(2)
    
    # Quick actions with enhanced styling
    create_section_header("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 Create New Campaign", use_container_width=True, type="primary"):
            create_alert_box("Redirecting to campaign creator...", "info")
    
    with col2:
        if st.button("📋 View Templates", use_container_width=True):
            create_alert_box("Opening template library...", "info")
    
    with col3:
        if st.button("📈 View Reports", use_container_width=True):
            create_alert_box("Opening analytics dashboard...", "info")
