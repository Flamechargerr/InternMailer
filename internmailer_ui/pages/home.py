"""
Home page for InternMailer UI

Main dashboard and overview page.
"""

import streamlit as st
from services import email_service
from components.ui_components import (
    create_metric_card, create_section_header, create_info_card,
    create_status_badge, create_progress_card, create_stats_grid,
    create_alert_box, add_spacing
)


def show():
    """Display the home page."""
    # Welcome header with description
    create_section_header(
        "📧 InternMailer Dashboard",
        "Monitor your email campaigns and manage your communication strategy"
    )
    
    # Alert for new features or important updates
    create_alert_box(
        "Welcome to the enhanced InternMailer dashboard! New features include real-time analytics and improved campaign management.",
        alert_type="info"
    )
    
    add_spacing(1)
    
    # Professional metric cards using the new components
    stats_data = [
        {"title": "Total Emails", "value": "1,234", "delta": "+12 this week", "color": "#0066CC"},
        {"title": "Open Rate", "value": "24.5%", "delta": "+2.1% improvement", "color": "#28A745"},
        {"title": "Click Rate", "value": "3.2%", "delta": "-0.5% vs last month", "color": "#DC3545"},
        {"title": "Active Campaigns", "value": "5", "delta": "+1 new campaign", "color": "#17A2B8"},
        {"title": "Bounce Rate", "value": "2.1%", "delta": "Within normal range", "color": "#FFC107"},
        {"title": "Subscribers", "value": "15,678", "delta": "+234 this month", "color": "#6F42C1"}
    ]
    
    create_stats_grid(stats_data, columns=3)
    
    add_spacing(2)
    
    # Campaign Status Section
    create_section_header("📊 Campaign Overview")
    
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
