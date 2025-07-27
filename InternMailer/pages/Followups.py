import streamlit as st
import os
import pandas as pd
import sys
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Add src to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scheduler'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from streamlit_api import get_followup_manager

st.title("📅 Follow-up Management")

# Initialize follow-up manager
followup_manager = get_followup_manager()

# Initialize session state for persistence
if 'selected_campaign' not in st.session_state:
    st.session_state.selected_campaign = None

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 All Follow-ups", "⚙️ Campaign Settings", "📈 Analytics"])

with tab1:
    st.subheader("Follow-up Dashboard")
    
    # Get analytics
    try:
        analytics = followup_manager.get_analytics()
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Follow-ups", analytics.get('total_followups', 0))
        with col2:
            st.metric("Scheduled", analytics.get('scheduled_followups', 0))
        with col3:
            st.metric("Sent", analytics.get('sent_followups', 0))
        with col4:
            st.metric("Overdue", analytics.get('overdue_followups', 0), delta_color="inverse")
        
        # Process overdue follow-ups button
        if st.button("🚀 Process Overdue Follow-ups"):
            with st.spinner("Processing overdue follow-ups..."):
                processed = followup_manager.process_overdue_followups()
                if processed > 0:
                    st.success(f"✅ Processed {processed} overdue follow-ups!")
                    st.rerun()
                else:
                    st.info("ℹ️ No overdue follow-ups to process.")
        
        # Campaign breakdown chart
        if analytics.get('campaigns'):
            st.subheader("Follow-ups by Campaign")
            campaign_df = pd.DataFrame(analytics['campaigns'])
            if not campaign_df.empty:
                fig = px.bar(campaign_df, x='name', y='followup_count', 
                            title="Follow-ups by Campaign")
                fig.update_layout(xaxis_title="Campaign", yaxis_title="Follow-up Count")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No campaign data available yet.")
            
    except Exception as e:
        st.error(f"❌ Error loading dashboard: {str(e)}")

with tab2:
    st.subheader("All Follow-ups")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", 
                                   ["All", "scheduled", "sent", "cancelled"])
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    try:
        # Get all follow-ups
        all_followups = followup_manager.get_all_followups()
        
        if status_filter != "All":
            all_followups = [f for f in all_followups if f.get('status') == status_filter]
        
        if all_followups:
            # Display follow-ups in a table format
            for i, followup in enumerate(all_followups):
                with st.expander(f"📧 {followup.get('contact_name', 'Unknown')} ({followup.get('contact_email', 'No Email')}) - {followup.get('status', 'Unknown').title()}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**Campaign:** {followup.get('campaign_name', 'Unknown')}")
                        st.write(f"**Sequence:** {followup.get('sequence_number', 'N/A')}")
                        st.write(f"**Scheduled:** {followup.get('scheduled_at', 'N/A')[:16] if followup.get('scheduled_at') else 'N/A'}")
                        
                        if followup.get('is_overdue') and followup.get('status') == 'scheduled':
                            st.error("⚠️ OVERDUE")
                        
                        if followup.get('sent_at'):
                            st.write(f"**Sent:** {followup['sent_at'][:16]}")
                    
                    with col2:
                        if followup.get('status') == 'scheduled':
                            # Reschedule option
                            if followup.get('scheduled_at_parsed'):
                                new_date = st.date_input(f"New Date", 
                                                        value=followup['scheduled_at_parsed'].date(),
                                                        key=f"date_{followup['id']}")
                                new_time = st.time_input(f"New Time", 
                                                        value=followup['scheduled_at_parsed'].time(),
                                                        key=f"time_{followup['id']}")
                            else:
                                new_date = st.date_input(f"New Date", 
                                                        value=datetime.now().date(),
                                                        key=f"date_{followup['id']}")
                                new_time = st.time_input(f"New Time", 
                                                        value=datetime.now().time(),
                                                        key=f"time_{followup['id']}")
                            
                            if st.button(f"📅 Reschedule", key=f"reschedule_{followup['id']}"):
                                new_datetime = datetime.combine(new_date, new_time)
                                if followup_manager.reschedule_followup(followup['id'], new_datetime):
                                    st.success("✅ Rescheduled successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to reschedule.")
                    
                    with col3:
                        if followup.get('status') == 'scheduled':
                            if st.button(f"❌ Cancel", key=f"cancel_{followup['id']}"):
                                if followup_manager.cancel_followup(followup['id'], "Cancelled by user"):
                                    st.success("✅ Cancelled successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to cancel.")
        else:
            st.info("ℹ️ No follow-ups found.")
    
    except Exception as e:
        st.error(f"❌ Error loading follow-ups: {str(e)}")

with tab3:
    st.subheader("Campaign Settings")
    
    try:
        # Get all campaigns
        campaigns = followup_manager.get_campaigns()
        
        if campaigns:
            campaign_options = {c['id']: c['name'] for c in campaigns}
            selected_campaign_id = st.selectbox("Select Campaign", 
                                           options=list(campaign_options.keys()),
                                           format_func=lambda x: campaign_options[x],
                                           index=0 if not st.session_state.selected_campaign else 
                                                 list(campaign_options.keys()).index(st.session_state.selected_campaign) 
                                                 if st.session_state.selected_campaign in campaign_options else 0)
            
            st.session_state.selected_campaign = selected_campaign_id
            
            # Find selected campaign data
            campaign_data = next(c for c in campaigns if c['id'] == selected_campaign_id)
            
            st.write(f"**Campaign:** {campaign_data['name']}")
            st.write(f"**Description:** {campaign_data['description']}")
            st.write(f"**Total Follow-ups:** {campaign_data.get('total_followups', 0)}")
            
            # Settings form
            with st.form(f"campaign_settings_{selected_campaign_id}"):
                st.subheader("Follow-up Settings")
                
                followup_enabled = st.checkbox("Enable Follow-ups", 
                                             value=bool(campaign_data.get('followup_enabled', True)))
                
                followup_delay = st.slider("Follow-up Delay (days)", 
                                         min_value=1, max_value=30, 
                                         value=campaign_data.get('followup_delay_days', 7))
                
                max_followups = st.slider("Maximum Follow-ups", 
                                        min_value=1, max_value=5, 
                                        value=campaign_data.get('max_followups', 3))
                
                if st.form_submit_button("💾 Save Settings"):
                    settings = {
                        'followup_enabled': followup_enabled,
                        'followup_delay_days': followup_delay,
                        'max_followups': max_followups
                    }
                    
                    if followup_manager.update_campaign_settings(selected_campaign_id, settings):
                        st.success("✅ Settings updated successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to update settings.")
            
            # Campaign-specific follow-ups
            st.subheader("Campaign Follow-ups")
            campaign_followups = followup_manager.get_campaign_followups(selected_campaign_id)
            
            if campaign_followups:
                # Status breakdown
                status_counts = {}
                for f in campaign_followups:
                    status = f.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Scheduled", status_counts.get('scheduled', 0))
                with col2:
                    st.metric("Sent", status_counts.get('sent', 0))
                with col3:
                    st.metric("Cancelled", status_counts.get('cancelled', 0))
                
                # Bulk actions
                st.subheader("Bulk Actions")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📅 Reschedule All Pending"):
                        st.info("💡 Bulk reschedule feature - coming soon!")
                
                with col2:
                    if st.button("❌ Cancel All Pending"):
                        pending_count = len([f for f in campaign_followups if f.get('status') == 'scheduled'])
                        st.warning(f"⚠️ This would cancel {pending_count} pending follow-ups. Feature coming soon.")
            else:
                st.info("ℹ️ No follow-ups found for this campaign.")
        else:
            st.info("ℹ️ No campaigns found. Run an outreach first to create a campaign.")
    
    except Exception as e:
        st.error(f"❌ Error loading campaign settings: {str(e)}")

with tab4:
    st.subheader("Follow-up Analytics")
    
    try:
        # Get analytics data
        analytics = followup_manager.get_analytics()
        
        # Overall statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Overall Statistics")
            total = analytics.get('total_followups', 0)
            if total > 0:
                success_rate = (analytics.get('sent_followups', 0) / total) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Status distribution pie chart
                status_data = {
                    'Scheduled': analytics.get('scheduled_followups', 0),
                    'Sent': analytics.get('sent_followups', 0),
                    'Cancelled': analytics.get('cancelled_followups', 0)
                }
                
                if sum(status_data.values()) > 0:
                    fig = px.pie(values=list(status_data.values()), 
                                names=list(status_data.keys()),
                                title="Follow-up Status Distribution")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No data available for analytics.")
        
        with col2:
            st.subheader("Performance Metrics")
            
            if analytics.get('total_followups', 0) > 0:
                scheduled = analytics.get('scheduled_followups', 0)
                overdue = analytics.get('overdue_followups', 0)
                overdue_rate = (overdue / scheduled) * 100 if scheduled > 0 else 0
                st.metric("Overdue Rate", f"{overdue_rate:.1f}%", delta_color="inverse")
            else:
                st.info("💡 Advanced analytics will appear here after follow-ups are processed.")
        
        # Recent activity
        st.subheader("Recent Follow-up Activity")
        try:
            recent_followups = followup_manager.get_all_followups()
            if recent_followups:
                # Sort by updated_at or created_at
                recent_followups.sort(key=lambda x: x.get('updated_at', x.get('created_at', '')), reverse=True)
                
                for followup in recent_followups[:5]:  # Show last 5
                    status_emoji = {"scheduled": "⏰", "sent": "✅", "cancelled": "❌"}
                    emoji = status_emoji.get(followup.get('status'), "❓")
                    contact_name = followup.get('contact_name', 'Unknown')
                    status = followup.get('status', 'unknown').title()
                    scheduled_date = followup.get('scheduled_at', '')[:10] if followup.get('scheduled_at') else 'N/A'
                    st.write(f"{emoji} **{contact_name}** - {status} ({scheduled_date})")
            else:
                st.info("ℹ️ No recent activity.")
        except Exception as e:
            st.warning(f"⚠️ Could not load recent activity: {str(e)}")
            
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")

# Status indicators
st.sidebar.header("📊 Quick Stats")
try:
    analytics = followup_manager.get_analytics()
    st.sidebar.metric("Active Follow-ups", analytics.get('scheduled_followups', 0))
    st.sidebar.metric("Completed", analytics.get('sent_followups', 0))
    if analytics.get('overdue_followups', 0) > 0:
        st.sidebar.error(f"⚠️ {analytics['overdue_followups']} overdue")
    else:
        st.sidebar.success("✅ No overdue follow-ups")
except Exception as e:
    st.sidebar.error("❌ Error loading stats")

# Navigation hint
st.info("💡 **Tip:** Use the sidebar to navigate back to the Outreach page to start new campaigns.")
