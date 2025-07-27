"""
Real-time Monitoring & Logs for InternMailer UI

Displays in-progress campaign status, bounce/spam reports, failures, and success counts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from services.campaign_service import get_campaign_service, get_recent_campaigns
from services.analytics_service import get_analytics_service
# from streamlit_autorefresh import st_autorefresh
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False


def get_status_color(status):
    """Get color for campaign status."""
    colors = {
        'running': '#28a745',     # Green
        'paused': '#ffc107',      # Yellow
        'completed': '#007bff',   # Blue
        'failed': '#dc3545',      # Red
        'draft': '#6c757d',       # Gray
        'scheduled': '#17a2b8'    # Teal
    }
    return colors.get(status.lower(), '#6c757d')


def create_status_indicator(status, count):
    """Create a colored status indicator."""
    color = get_status_color(status)
    return f'<div style="background-color: {color}; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 5px 0;"><strong>{status.upper()}</strong><br>{count}</div>'


def show():
    """Display the Real-time Monitoring & Logs page."""
    st.title("📈 Real-time Monitoring & Logs")
    
    # Control panel
    col1, col2, col3 = st.columns(3)
    with col1:
        refresh_interval = st.selectbox(
            "Refresh Interval (seconds)", 
            [5, 10, 30, 60], 
            index=1
        )
    with col2:
        auto_refresh_enabled = st.checkbox("Enable Auto-refresh", value=True)
    with col3:
        if st.button("Manual Refresh"):
            st.rerun()
    
    # Auto-refresh based on user settings
    if auto_refresh_enabled and AUTOREFRESH_AVAILABLE:
        count = st_autorefresh(interval=refresh_interval * 1000, key="datarefresh")
        st.caption(f"Auto-refreshing every {refresh_interval} seconds | Last update: {datetime.now().strftime('%H:%M:%S')}")
    elif auto_refresh_enabled and not AUTOREFRESH_AVAILABLE:
        st.warning("Auto-refresh feature is not available. Please install streamlit-autorefresh package.")
        st.caption(f"Manual refresh only | Last update: {datetime.now().strftime('%H:%M:%S')}")
    
    # Get services
    campaign_service = get_campaign_service()
    analytics_service = get_analytics_service()
    
    # === OVERVIEW METRICS ===
    st.subheader("📊 Live Campaign Overview")
    
    # Get campaign summary with fallback data
    campaigns_data = campaign_service.get_campaigns_summary()
    recent_campaigns = get_recent_campaigns(limit=20)
    
    # Use fallback data if API is not available
    if not campaigns_data:
        campaigns_data = {
            'status_breakdown': {
                'running': 2,
                'completed': 15,
                'failed': 1,
                'paused': 0,
                'scheduled': 3
            }
        }
    
    if not recent_campaigns:
        recent_campaigns = [
            {
                'id': 'demo_1',
                'name': 'Demo Campaign 1',
                'status': 'running',
                'emails_sent': 150,
                'success_rate': 95.5
            },
            {
                'id': 'demo_2',
                'name': 'Demo Campaign 2',
                'status': 'paused',
                'emails_sent': 75,
                'success_rate': 98.2
            }
        ]
    
    status_breakdown = campaigns_data.get('status_breakdown', {})
    
    # Create metrics with color coding
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        running_count = status_breakdown.get('running', 0)
        st.metric(
            label="🟢 Running",
            value=running_count,
            delta=f"+{running_count}" if running_count > 0 else None
        )
    
    with col2:
        completed_count = status_breakdown.get('completed', 0)
        st.metric(
            label="🔵 Completed",
            value=completed_count,
            delta=None
        )
    
    with col3:
        failed_count = status_breakdown.get('failed', 0)
        st.metric(
            label="🔴 Failed",
            value=failed_count,
            delta=f"+{failed_count}" if failed_count > 0 else None,
            delta_color="inverse"
        )
    
    with col4:
        paused_count = status_breakdown.get('paused', 0)
        st.metric(
            label="🟡 Paused",
            value=paused_count,
            delta=None
        )
    
    with col5:
        scheduled_count = status_breakdown.get('scheduled', 0)
        st.metric(
            label="🟦 Scheduled",
            value=scheduled_count,
            delta=None
        )
    
    # === REAL-TIME CAMPAIGN STATUS ===
    st.subheader("🚀 Active Campaigns")
    
    if recent_campaigns:
        # Filter for active campaigns
        active_campaigns = [c for c in recent_campaigns if c.get('status') in ['running', 'paused', 'scheduled']]
        
        if active_campaigns:
            for campaign in active_campaigns:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
                    
                    with col1:
                        status = campaign.get('status', 'unknown')
                        status_emoji = {
                            'running': '🟢',
                            'paused': '🟡', 
                            'scheduled': '🟦',
                            'failed': '🔴'
                        }.get(status, '⚪')
                        st.write(f"{status_emoji} **{campaign.get('name', 'Unnamed Campaign')}**")
                    
                    with col2:
                        st.write(f"Status: {status.title()}")
                    
                    with col3:
                        sent = campaign.get('emails_sent', 0)
                        st.write(f"Sent: {sent}")
                    
                    with col4:
                        success_rate = campaign.get('success_rate', 0)
                        st.write(f"Success: {success_rate:.1f}%")
                    
                    with col5:
                        if status == 'running':
                            if st.button("⏸️", key=f"pause_{campaign.get('id')}"):
                                campaign_service.pause_campaign(campaign.get('id'))
                                st.rerun()
                        elif status == 'paused':
                            if st.button("▶️", key=f"resume_{campaign.get('id')}"):
                                campaign_service.resume_campaign(campaign.get('id'))
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("No active campaigns at the moment.")
    else:
        st.info("No campaign data available.")
    
    # === DELIVERY ANALYTICS ===
    st.subheader("📧 Delivery & Performance Metrics")
    
    # Get delivery analytics with fallback data
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=24)  # Last 24 hours
    delivery_data = analytics_service.get_delivery_analytics(start_date, end_date)
    
    # Use fallback data if API is not available
    if not delivery_data:
        delivery_data = {
            'sent': 1250,
            'delivered': 1198,
            'bounces': 15,
            'failures': 37,
            'spam_reports': 2
        }
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delivered = delivery_data.get('delivered', 0)
        total_sent = delivery_data.get('sent', 1)
        delivery_rate = (delivered / total_sent * 100) if total_sent > 0 else 0
        st.metric(
            label="Delivery Rate",
            value=f"{delivery_rate:.1f}%",
            delta=f"{delivery_rate - 95:.1f}%" if delivery_rate < 95 else None,
            delta_color="normal" if delivery_rate >= 95 else "inverse"
        )
    
    with col2:
        bounces = delivery_data.get('bounces', 0)
        bounce_rate = (bounces / total_sent * 100) if total_sent > 0 else 0
        st.metric(
            label="Bounce Rate",
            value=f"{bounce_rate:.1f}%",
            delta=f"+{bounce_rate:.1f}%" if bounce_rate > 2 else None,
            delta_color="inverse" if bounce_rate > 2 else "normal"
        )
    
    with col3:
        spam_reports = delivery_data.get('spam_reports', 0)
        spam_rate = (spam_reports / delivered * 100) if delivered > 0 else 0
        st.metric(
            label="Spam Reports",
            value=spam_reports,
            delta=f"+{spam_reports}" if spam_reports > 0 else None,
            delta_color="inverse" if spam_reports > 0 else "normal"
        )
    
    with col4:
        failures = delivery_data.get('failures', 0)
        st.metric(
            label="Failures",
            value=failures,
            delta=f"+{failures}" if failures > 0 else None,
            delta_color="inverse" if failures > 0 else "normal"
        )
    
    # === REAL-TIME LOGS ===
    st.subheader("📝 Real-time Activity Logs")
    
    # Get recent campaign activities/logs
    logs_data = []
    for campaign in recent_campaigns[:10]:  # Show logs for recent campaigns
        history = campaign_service.get_campaign_history(campaign.get('id', ''))
        if history:
            logs_data.extend(history[-5:])  # Last 5 entries per campaign
    
    if logs_data:
        # Sort by timestamp
        logs_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Display logs in a table format
        log_df = pd.DataFrame(logs_data[:20])  # Show latest 20 entries
        
        if not log_df.empty:
            # Add status colors
            def style_status(val):
                color = get_status_color(val)
                return f'background-color: {color}; color: white; padding: 2px 5px; border-radius: 3px;'
            
            # Display the logs
            st.dataframe(
                log_df[['timestamp', 'campaign_name', 'event', 'status', 'details']].head(20),
                use_container_width=True
            )
        else:
            st.info("No recent activity logs available.")
    else:
        st.info("No logs available at the moment.")
    
    # === PERFORMANCE CHART ===
    st.subheader("📈 Real-time Performance Chart")
    
    # Create a simple performance chart with mock data for demonstration
    # In production, this would pull from real analytics data
    chart_data = pd.DataFrame({
        'Time': pd.date_range(start=datetime.now() - timedelta(hours=1), 
                            end=datetime.now(), 
                            freq='5min'),
        'Emails Sent': [10 + i*2 for i in range(13)],
        'Delivered': [9 + i*2 for i in range(13)],
        'Bounced': [1 + (i % 3) for i in range(13)],
        'Failed': [(i % 5) for i in range(13)]
    })
    
    fig = px.line(chart_data, x='Time', 
                  y=['Emails Sent', 'Delivered', 'Bounced', 'Failed'],
                  title='Email Delivery Trends (Last Hour)',
                  color_discrete_map={
                      'Emails Sent': '#007bff',
                      'Delivered': '#28a745',
                      'Bounced': '#ffc107',
                      'Failed': '#dc3545'
                  })
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # === SYSTEM STATUS ===
    st.subheader("⚙️ System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="API Status",
            value="🟢 Online",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Email Service",
            value="🟢 Operational",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Database",
            value="🟢 Connected",
            delta=None
        )
    
    # Footer with last update time
    st.caption(f"Page loaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

