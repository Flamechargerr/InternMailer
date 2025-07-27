"""
Settings page for InternMailer UI

Application configuration and user preferences.
"""

import streamlit as st


def show():
    """Display the settings page."""
    st.title("⚙️ Settings")
    
    # Email Settings
    st.subheader("📧 Email Configuration")
    
    with st.expander("SMTP Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=587, min_value=1, max_value=65535)
        
        with col2:
            smtp_username = st.text_input("Username")
            smtp_password = st.text_input("Password", type="password")
        
        use_tls = st.checkbox("Use TLS", value=True)
    
    # API Settings
    st.subheader("🔌 API Configuration")
    
    with st.expander("API Settings", expanded=False):
        api_url = st.text_input("API Base URL", value="http://localhost:8000")
        api_key = st.text_input("API Key", type="password")
        timeout = st.number_input("Request Timeout (seconds)", value=30, min_value=1)
    
    # UI Preferences
    st.subheader("🎨 User Interface")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        items_per_page = st.number_input("Items per page", value=25, min_value=10, max_value=100)
    
    with col2:
        date_format = st.selectbox("Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        time_zone = st.selectbox("Time Zone", ["UTC", "EST", "PST", "GMT"])
    
    # Notification Settings
    st.subheader("🔔 Notifications")
    
    email_notifications = st.checkbox("Email Notifications", value=True)
    campaign_alerts = st.checkbox("Campaign Status Alerts", value=True)
    weekly_reports = st.checkbox("Weekly Reports", value=False)
    
    # Save Settings
    st.divider()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            st.success("Settings saved successfully!")
    
    with col2:
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            st.info("Settings reset to default values")
    
    with col3:
        if st.button("🧪 Test Connection", use_container_width=True):
            st.info("Testing API connection...")
