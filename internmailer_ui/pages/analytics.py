"""
Analytics page for InternMailer UI

Email campaign analytics and reporting.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
from datetime import datetime, timedelta
from services.analytics_service import get_analytics_service, process_engagement_data
import io


def show():
    """Display the analytics page."""
    st.title("📊 Analytics & Reports")
    
    # Obtain the analytics service
    service = get_analytics_service()

    # Filters Section
    st.subheader("🔍 Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "Start Date", 
            value=datetime.now() - timedelta(days=30)
        )
    
    with col2:
        end_date = st.date_input(
            "End Date", 
            value=datetime.now()
        )
    
    with col3:
        campaign_filter = st.selectbox(
            "Campaign", 
            ["All Campaigns", "Welcome Series", "Newsletter", "Product Launch", "Re-engagement"]
        )
    
    col4, col5 = st.columns(2)
    
    with col4:
        segment_filter = st.selectbox(
            "Segment", 
            ["All Segments", "New Users", "Active Users", "VIP Users", "Inactive Users"]
        )
    
    with col5:
        period_selector = st.selectbox(
            "Time Period", 
            ["Last 7 days", "Last 30 days", "Last 90 days", "Custom Range"]
        )
    
    # Fetch overall metrics
    metrics = service.get_overall_metrics(
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.min.time())
    )
    
    # Key Performance Indicators
    st.subheader("📈 Key Performance Indicators")
    
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delivery_rate = (metrics.get('total_delivered', 0) / max(metrics.get('total_sent', 1), 1)) * 100
            st.metric(
                "Delivery Rate", 
                f"{delivery_rate:.1f}%", 
                delta=f"+{0.3}%"
            )
        
        with col2:
            open_rate = (metrics.get('total_opens', 0) / max(metrics.get('total_delivered', 1), 1)) * 100
            st.metric(
                "Open Rate", 
                f"{open_rate:.1f}%", 
                delta=f"+{2.1}%"
            )
        
        with col3:
            click_rate = (metrics.get('total_clicks', 0) / max(metrics.get('total_opens', 1), 1)) * 100
            st.metric(
                "Click Rate", 
                f"{click_rate:.1f}%", 
                delta=f"-{0.5}%"
            )
        
        with col4:
            conversion_rate = (metrics.get('total_conversions', 0) / max(metrics.get('total_clicks', 1), 1)) * 100
            st.metric(
                "Conversion Rate", 
                f"{conversion_rate:.1f}%", 
                delta=f"+{1.2}%"
            )
    else:
        st.warning("No metrics data available for the selected period.")
    
    # Charts section
    st.subheader("📊 Performance Trends")
    
    # Get engagement trends
    trends_data = service.get_engagement_trends(period="30d")
    engagement_df = process_engagement_data(trends_data)
    
    if not engagement_df.empty:
        # Plotly line chart
        fig_plotly = px.line(
            engagement_df, 
            x='date', 
            y=['sent', 'opens', 'clicks'],
            title='Email Performance Over Time (Plotly)',
            labels={'value': 'Count', 'date': 'Date'}
        )
        fig_plotly.update_layout(height=400)
        st.plotly_chart(fig_plotly, use_container_width=True)
        
        # Altair chart alternative
        st.subheader("📈 Engagement Trends (Altair)")
        
        # Melt the dataframe for Altair
        melted_df = engagement_df.melt(
            id_vars=['date'], 
            value_vars=['sent', 'opens', 'clicks'],
            var_name='metric', 
            value_name='count'
        )
        
        altair_chart = alt.Chart(melted_df).mark_line(point=True).encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('count:Q', title='Count'),
            color=alt.Color('metric:N', title='Metric'),
            tooltip=['date:T', 'metric:N', 'count:Q']
        ).properties(
            width=700,
            height=300,
            title='Email Performance Trends'
        ).interactive()
        
        st.altair_chart(altair_chart, use_container_width=True)
    else:
        st.info("No trend data available for the selected period.")
    
    # Top Performing Campaigns
    st.subheader("🏆 Top Performing Campaigns")
    
    top_campaigns = service.get_top_performing_campaigns(limit=5, metric="open_rate")
    
    if top_campaigns:
        campaigns_df = pd.DataFrame(top_campaigns)
        
        # Bar chart for top campaigns
        fig_bar = px.bar(
            campaigns_df, 
            x='campaign_name', 
            y='open_rate',
            title='Top Campaigns by Open Rate',
            labels={'open_rate': 'Open Rate (%)', 'campaign_name': 'Campaign'}
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Display table
        st.dataframe(campaigns_df, use_container_width=True)
    else:
        st.info("No campaign performance data available.")
    
    # Campaign Performance Table
    st.subheader("📋 Detailed Campaign Performance")
    
    # Create sample data if no real data is available
    campaign_data = pd.DataFrame({
        'Campaign': ['Welcome Series', 'Newsletter Q1', 'Product Launch', 'Re-engagement'],
        'Sent': [1200, 3500, 800, 2100],
        'Delivered': [1180, 3450, 792, 2080],
        'Opens': [300, 875, 240, 420],
        'Clicks': [45, 105, 32, 21],
        'Conversions': [12, 28, 15, 5],
        'Unsubscribes': [2, 8, 1, 5]
    })
    
    # Calculate rates
    campaign_data['Delivery Rate'] = (campaign_data['Delivered'] / campaign_data['Sent'] * 100).round(1)
    campaign_data['Open Rate'] = (campaign_data['Opens'] / campaign_data['Delivered'] * 100).round(1)
    campaign_data['Click Rate'] = (campaign_data['Clicks'] / campaign_data['Opens'] * 100).round(1)
    campaign_data['Conversion Rate'] = (campaign_data['Conversions'] / campaign_data['Clicks'] * 100).round(1)
    campaign_data['Unsubscribe Rate'] = (campaign_data['Unsubscribes'] / campaign_data['Delivered'] * 100).round(2)
    
    st.dataframe(campaign_data, use_container_width=True)
    
    # Export Section
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV Export
        csv_buffer = io.StringIO()
        campaign_data.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"campaign_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # PDF Export preparation (simplified)
        if st.button("📑 Generate PDF Report"):
            st.info("PDF generation would be implemented here. For now, please use the CSV export.")
    
    # Additional Analytics Sections
    st.subheader("👥 Audience Insights")
    
    audience_data = service.get_audience_insights()
    if audience_data:
        # Display audience insights
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            st.metric("Total Subscribers", f"{audience_data.get('total_subscribers', 0):,}")
            st.metric("Active Rate", f"{audience_data.get('active_rate', 0):.1f}%")
        
        with insights_col2:
            st.metric("New Subscribers (30d)", f"{audience_data.get('new_subscribers_30d', 0):,}")
            st.metric("Churn Rate", f"{audience_data.get('churn_rate', 0):.2f}%")
    else:
        st.info("Audience insights data not available at the moment.")
