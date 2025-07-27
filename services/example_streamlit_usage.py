"""
Example Streamlit App using the Services Layer

This example demonstrates how to use the refactored services layer
in Streamlit pages. The services provide clean, synchronous interfaces
that work seamlessly with Streamlit's execution model.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import the simple interface functions
from services import send_email, fetch_metrics, list_contacts, list_campaigns, create_contact, health_check, get_time_series_data


def main():
    """Main Streamlit app."""
    st.title("InternMailer - Services Example")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Select Page",
        ["Dashboard", "Send Email", "Contacts", "Campaigns", "Health Check"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Send Email":
        show_send_email()
    elif page == "Contacts":
        show_contacts()
    elif page == "Campaigns":
        show_campaigns()
    elif page == "Health Check":
        show_health_check()


def show_dashboard():
    """Show analytics dashboard."""
    st.header("📊 Analytics Dashboard")
    
    # Time range selection
    time_range = st.selectbox(
        "Time Range",
        ["24h", "7d", "30d", "90d"],
        index=2  # Default to 30d
    )
    
    # Fetch metrics using the simple interface
    with st.spinner("Loading metrics..."):
        metrics = fetch_metrics(time_range=time_range)
    
    if "error" in metrics:
        st.error(f"Error loading metrics: {metrics['error']}")
        return
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Emails Sent",
            value=metrics['total_emails_sent'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Delivery Rate",
            value=f"{metrics['delivery_rate']:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Open Rate", 
            value=f"{metrics['open_rate']:.1f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Click Rate",
            value=f"{metrics['click_rate']:.1f}%", 
            delta=None
        )
    
    # Campaign summary
    st.subheader("Campaign Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Campaigns", metrics['total_campaigns'])
    
    with col2:
        st.metric("Active Campaigns", metrics['active_campaigns'])
    
    # Time series chart
    st.subheader("Email Activity Over Time")
    
    with st.spinner("Loading time series data..."):
        time_series = get_time_series_data(time_range=time_range)
    
    if time_series:
        # Convert to DataFrame for charting
        df = pd.DataFrame(time_series)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create chart
        chart_data = df.set_index('timestamp')[['emails_sent', 'emails_delivered', 'emails_opened']]
        st.line_chart(chart_data)
    else:
        st.info("No time series data available")


def show_send_email():
    """Show email sending interface."""
    st.header("📧 Send Email")
    
    with st.form("send_email_form"):
        # Email form fields
        recipient = st.text_input(
            "Recipient Email",
            placeholder="professor@university.edu"
        )
        
        subject = st.text_input(
            "Subject",
            placeholder="Research Collaboration Inquiry"
        )
        
        body = st.text_area(
            "Email Body",
            placeholder="Dear Professor,\n\nI am writing to inquire about...",
            height=200
        )
        
        # Optional fields
        with st.expander("Advanced Options"):
            sender_name = st.text_input("Sender Name", placeholder="Your Name")
            sender_email = st.text_input("Sender Email", placeholder="your@email.com")
            campaign_id = st.text_input("Campaign ID (optional)")
        
        # Submit button
        submit_button = st.form_submit_button("Send Email")
        
        if submit_button:
            if not recipient or not subject or not body:
                st.error("Please fill in all required fields")
                return
            
            # Send email using the service
            with st.spinner("Sending email..."):
                result = send_email(
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    sender_name=sender_name if sender_name else None,
                    sender_email=sender_email if sender_email else None,
                    campaign_id=campaign_id if campaign_id else None
                )
            
            # Display result
            if result['status'] == 'sent':
                st.success("✅ Email sent successfully!")
                if result['message_id']:
                    st.info(f"Message ID: {result['message_id']}")
                if result['execution_time']:
                    st.info(f"Sent in {result['execution_time']:.2f} seconds")
            else:
                st.error(f"❌ Failed to send email: {result.get('error_message', 'Unknown error')}")


def show_contacts():
    """Show contacts management."""
    st.header("👥 Contacts")
    
    # Add new contact form
    with st.expander("➕ Add New Contact"):
        with st.form("add_contact_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                email = st.text_input("Email*", placeholder="contact@example.com")
                first_name = st.text_input("First Name", placeholder="John")
                organization = st.text_input("Organization", placeholder="MIT")
            
            with col2:
                last_name = st.text_input("Last Name", placeholder="Doe")
                position = st.text_input("Position", placeholder="Professor")
                research_areas = st.text_input("Research Areas (comma-separated)", placeholder="AI, Machine Learning")
            
            tags = st.text_input("Tags (comma-separated)", placeholder="academic, researcher")
            
            submit_contact = st.form_submit_button("Add Contact")
            
            if submit_contact:
                if not email:
                    st.error("Email is required")
                else:
                    # Prepare contact data
                    contact_data = {
                        'email': email,
                        'first_name': first_name if first_name else None,
                        'last_name': last_name if last_name else None,
                        'organization': organization if organization else None,
                        'position': position if position else None,
                        'research_areas': [area.strip() for area in research_areas.split(',')] if research_areas else None,
                        'tags': [tag.strip() for tag in tags.split(',')] if tags else None
                    }
                    
                    # Create contact
                    with st.spinner("Creating contact..."):
                        contact = create_contact(contact_data)
                    
                    if contact:
                        st.success(f"✅ Contact created: {contact['email']}")
                        st.rerun()  # Refresh the page to show new contact
                    else:
                        st.error("❌ Failed to create contact")
    
    # Filters
    st.subheader("📋 Contact List")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_org = st.text_input("Filter by Organization", placeholder="Enter organization name")
    
    with col2:
        filter_tags = st.text_input("Filter by Tags", placeholder="academic, researcher")
    
    with col3:
        limit = st.number_input("Limit Results", min_value=1, max_value=100, value=20)
    
    # Get contacts
    with st.spinner("Loading contacts..."):
        tags_filter = [tag.strip() for tag in filter_tags.split(',')] if filter_tags else None
        contacts = list_contacts(
            limit=int(limit),
            organization=filter_org if filter_org else None,
            tags=tags_filter
        )
    
    # Display contacts
    if contacts:
        st.info(f"Found {len(contacts)} contacts")
        
        for contact in contacts:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                    if not name:
                        name = "Unknown Name"
                    
                    st.write(f"**{name}**")
                    st.write(f"📧 {contact['email']}")
                    
                    if contact.get('organization'):
                        st.write(f"🏢 {contact['organization']}")
                    
                    if contact.get('position'):
                        st.write(f"💼 {contact['position']}")
                    
                    if contact.get('research_areas'):
                        st.write(f"🔬 {', '.join(contact['research_areas'])}")
                    
                    if contact.get('tags'):
                        tag_badges = ' '.join([f"`{tag}`" for tag in contact['tags']])
                        st.write(f"🏷️ {tag_badges}")
                
                with col2:
                    if st.button(f"📧 Email", key=f"email_{contact['id']}"):
                        st.session_state.email_recipient = contact['email']
                        st.switch_page("Send Email")  # Navigate to send email page
                
                st.divider()
    else:
        st.info("No contacts found matching the criteria")


def show_campaigns():
    """Show campaigns list."""
    st.header("🚀 Campaigns")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "draft", "active", "paused", "completed"],
            index=0
        )
    
    with col2:
        limit = st.number_input("Limit Results", min_value=1, max_value=50, value=10)
    
    # Get campaigns
    with st.spinner("Loading campaigns..."):
        campaigns = list_campaigns(
            limit=int(limit),
            status=status_filter if status_filter != "All" else None
        )
    
    # Display campaigns
    if campaigns:
        st.info(f"Found {len(campaigns)} campaigns")
        
        for campaign in campaigns:
            with st.container():
                # Campaign header
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{campaign['name']}**")
                    if campaign.get('description'):
                        st.write(campaign['description'])
                
                with col2:
                    status_color = {
                        'draft': '🟡',
                        'active': '🟢', 
                        'paused': '🟠',
                        'completed': '🔵',
                        'cancelled': '🔴'
                    }
                    status_icon = status_color.get(campaign['status'], '⚪')
                    st.write(f"{status_icon} {campaign['status'].title()}")
                
                # Campaign metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Contacts", campaign['total_contacts'])
                
                with col2:
                    st.metric("Sent", campaign['emails_sent'])
                
                with col3:
                    st.metric("Delivered", campaign['emails_delivered'])
                
                with col4:
                    st.metric("Opened", campaign['emails_opened'])
                
                # View campaign metrics button
                if st.button(f"📊 View Metrics", key=f"metrics_{campaign['id']}"):
                    with st.spinner("Loading campaign metrics..."):
                        campaign_metrics = fetch_metrics(campaign_id=campaign['id'])
                    
                    if 'error' not in campaign_metrics:
                        st.write("**Campaign Performance:**")
                        
                        metric_cols = st.columns(5)
                        with metric_cols[0]:
                            st.metric("Delivery Rate", f"{campaign_metrics['delivery_rate']:.1f}%")
                        with metric_cols[1]:
                            st.metric("Open Rate", f"{campaign_metrics['open_rate']:.1f}%")
                        with metric_cols[2]:
                            st.metric("Click Rate", f"{campaign_metrics['click_rate']:.1f}%")
                        with metric_cols[3]:
                            st.metric("Reply Rate", f"{campaign_metrics['reply_rate']:.1f}%")
                        with metric_cols[4]:
                            st.metric("Bounce Rate", f"{campaign_metrics['bounce_rate']:.1f}%")
                    else:
                        st.error(f"Error loading campaign metrics: {campaign_metrics['error']}")
                
                st.divider()
    else:
        st.info("No campaigns found")


def show_health_check():
    """Show system health status."""
    st.header("🏥 System Health Check")
    
    # Get health status
    with st.spinner("Checking system health..."):
        health = health_check()
    
    # Overall status
    if health['overall_status'] == 'healthy':
        st.success("✅ All services are running properly")
    elif health['overall_status'] == 'unhealthy':
        st.warning("⚠️ Some services have issues")
    else:
        st.error(f"❌ System error: {health.get('error', 'Unknown error')}")
    
    # Individual service status
    if 'services' in health:
        st.subheader("Service Status")
        
        for service_name, service_status in health['services'].items():
            with st.container():
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if service_status.get('status') == 'healthy':
                        st.success(f"✅ {service_name.title()}")
                    else:
                        st.error(f"❌ {service_name.title()}")
                
                with col2:
                    # Show service details
                    if service_status.get('initialized'):
                        st.write("🟢 Initialized")
                    else:
                        st.write("🔴 Not Initialized")
                    
                    # Show additional service info
                    if service_name == 'email':
                        if 'daily_emails_sent' in service_status:
                            st.write(f"📧 Daily emails sent: {service_status['daily_emails_sent']}")
                        if 'provider' in service_status:
                            st.write(f"📮 Provider: {service_status['provider']}")
                    
                    elif service_name == 'database':
                        if 'contacts_count' in service_status:
                            st.write(f"👥 Contacts: {service_status['contacts_count']}")
                        if 'campaigns_count' in service_status:
                            st.write(f"🚀 Campaigns: {service_status['campaigns_count']}")
                    
                    elif service_name == 'analytics':
                        if 'metrics_count' in service_status:
                            st.write(f"📊 Metrics recorded: {service_status['metrics_count']}")
                    
                    # Show errors if any
                    if 'error' in service_status:
                        st.error(f"Error: {service_status['error']}")
                
                st.divider()
    
    # Refresh button
    if st.button("🔄 Refresh Health Check"):
        st.rerun()


if __name__ == "__main__":
    main()
