#!/usr/bin/env python3
"""
INTERNMAILER DASHBOARD - Full Control Center with All 20 Features
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys

# Page config
st.set_page_config(
    page_title="InternMailer Dashboard",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    .warning-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
    }
    .pause-btn {
        background-color: #f44336 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Database paths
TRACKING_DB = 'campaign_results/email_tracking.db'
ADVANCED_DB = 'campaign_results/advanced_tracking.db'
RECRUITERS_DB = 'data/recruiters.db'
PROFESSORS_DB = 'data/clean_40k_professors.db'

def get_db(path):
    if os.path.exists(path):
        return sqlite3.connect(path)
    return None

def get_advanced_manager():
    try:
        from advanced_features import get_advanced_manager as gam
        return gam()
    except:
        return None

def load_tracking():
    conn = get_db(TRACKING_DB)
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query("SELECT * FROM sent_emails ORDER BY sent_date DESC", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def load_advanced_stats():
    mgr = get_advanced_manager()
    if mgr:
        return mgr.get_full_stats()
    return {}

def get_recruiter_count():
    conn = get_db(RECRUITERS_DB)
    if not conn:
        return 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM recruiters")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_professor_count():
    # Try CSV first
    csv_path = 'data/proffesor_clean.csv'
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            return len(df)
        except:
            pass
    return 0

# ============ SIDEBAR ============
st.sidebar.title("📧 InternMailer")
st.sidebar.markdown("---")

mgr = get_advanced_manager()

# Pause/Resume button in sidebar
if mgr:
    if mgr.is_campaign_paused():
        if st.sidebar.button("▶️ Resume Campaign", key="resume"):
            mgr.resume_campaign()
            st.rerun()
        st.sidebar.error("⏸️ Campaign PAUSED")
    else:
        if st.sidebar.button("⏸️ Pause Campaign", key="pause"):
            mgr.pause_campaign()
            st.rerun()
        st.sidebar.success("✅ Campaign Active")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "🚀 Send Campaign", "📧 Email Preview", "📊 Analytics", 
     "🔄 Follow-ups", "⚙️ Settings", "🛡️ Safety Controls"]
)

st.sidebar.markdown("---")
stats = load_advanced_stats()
if stats:
    st.sidebar.metric("Sent Today", f"{stats.get('sent_today', 0)}/{stats.get('daily_limit', 50)}")
    st.sidebar.metric("Warmup Day", stats.get('warmup_day', 1))

# ============ MAIN PAGES ============

if page == "🏠 Dashboard":
    st.title("📧 InternMailer Dashboard")
    
    # Status banner
    if mgr and mgr.is_campaign_paused():
        st.error("⏸️ **Campaign is PAUSED** - No emails will be sent until you resume")
    
    # Top metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📧 Total Sent", stats.get('total_sent', 0))
    with col2:
        st.metric("📬 Opened", f"{stats.get('total_opened', 0)} ({stats.get('open_rate', '0%')})")
    with col3:
        st.metric("💬 Replied", f"{stats.get('total_replied', 0)} ({stats.get('reply_rate', '0%')})")
    with col4:
        st.metric("📅 Today", f"{stats.get('sent_today', 0)}/{stats.get('daily_limit', 50)}")
    with col5:
        st.metric("🔄 Pending Follow-ups", stats.get('pending_follow_ups', 0))
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📚 Send 5 to Professors", type="primary"):
            with st.spinner("Sending..."):
                import system
                vs = system.VerifiedEmailSystem()
                result = vs.launch_legendary_campaign_integrated(max_contacts=5, mode='academic')
                sent = result.get('successful_sends', 0) if isinstance(result, dict) else 5
                st.success(f"✅ Sent {sent} emails!")
                st.rerun()
    
    with col2:
        if st.button("🏢 Send 5 to Recruiters", type="primary"):
            with st.spinner("Sending..."):
                import system
                vs = system.VerifiedEmailSystem()
                result = vs.launch_legendary_campaign_integrated(max_contacts=5, mode='corporate')
                sent = result.get('successful_sends', 0) if isinstance(result, dict) else 5
                st.success(f"✅ Sent {sent} emails!")
                st.rerun()
    
    with col3:
        if st.button("🔄 Process Follow-ups"):
            if mgr:
                due = mgr.get_due_follow_ups()
                st.info(f"Found {len(due)} follow-ups due")
    
    with col4:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    st.markdown("---")
    
    # Recent emails
    st.subheader("📬 Recent Emails")
    tracking = load_tracking()
    if not tracking.empty:
        cols = [c for c in ['recipient_name', 'email', 'subject', 'sent_date', 'contact_type'] if c in tracking.columns]
        st.dataframe(tracking[cols].head(10), use_container_width=True)
    else:
        st.info("No emails sent yet")

elif page == "🚀 Send Campaign":
    st.title("🚀 Send Campaign")
    
    # Daily limit warning
    if stats:
        remaining = stats.get('remaining_today', 50)
        if remaining <= 0:
            st.error(f"🚫 Daily limit reached! Wait until tomorrow to send more emails.")
        else:
            st.info(f"📊 You can send **{remaining}** more emails today (Warmup Day {stats.get('warmup_day', 1)})")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👨‍🏫 Academic Campaign")
        prof_count = st.slider("Number of professors", 1, 50, 10, key="prof")
        
        if st.button("📚 Send to Professors", type="primary", use_container_width=True):
            if mgr and mgr.is_campaign_paused():
                st.error("Campaign is paused!")
            else:
                with st.spinner(f"Sending to {prof_count} professors..."):
                    import system
                    vs = system.VerifiedEmailSystem()
                    result = vs.launch_legendary_campaign_integrated(max_contacts=prof_count, mode='academic')
                    sent = result.get('successful_sends', 0) if isinstance(result, dict) else prof_count
                    st.success(f"✅ Sent {sent} emails!")
                    st.balloons()
    
    with col2:
        st.subheader("🏢 Corporate Campaign")
        rec_count = st.slider("Number of recruiters", 1, 50, 10, key="rec")
        
        if st.button("🏢 Send to Recruiters", type="primary", use_container_width=True):
            if mgr and mgr.is_campaign_paused():
                st.error("Campaign is paused!")
            else:
                with st.spinner(f"Sending to {rec_count} recruiters..."):
                    import system
                    vs = system.VerifiedEmailSystem()
                    result = vs.launch_legendary_campaign_integrated(max_contacts=rec_count, mode='corporate')
                    sent = result.get('successful_sends', 0) if isinstance(result, dict) else rec_count
                    st.success(f"✅ Sent {sent} emails!")
                    st.balloons()

elif page == "📧 Email Preview":
    st.title("📧 Email Preview")
    st.markdown("Preview emails before sending")
    
    mode = st.radio("Email Type", ["Corporate", "Academic"])
    
    if mode == "Corporate":
        company = st.text_input("Company Name", "Google")
        name = st.text_input("Recruiter Name", "Sarah")
        
        if st.button("Generate Preview"):
            import system
            vs = system.VerifiedEmailSystem()
            template = vs._get_corporate_template()
            subject, body = vs.personalize_email_corporate(
                template, 
                (name, f"test@{company.lower()}.com", company, 95, 'A+')
            )
            
            st.subheader("Subject")
            st.code(subject)
            
            st.subheader("Body")
            st.text_area("Email Body", body, height=400)
            
            if mgr:
                preview = mgr.preview_email(f"test@{company.lower()}.com", subject, body)
                st.markdown(f"**Word Count:** {preview['word_count']} | **Read Time:** {preview['estimated_read_time']}")
    
    else:  # Academic
        st.info("Academic emails are personalized based on professor research data")

elif page == "📊 Analytics":
    st.title("📊 Campaign Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Key Metrics")
        if stats:
            st.metric("Open Rate", stats.get('open_rate', '0%'))
            st.metric("Reply Rate", stats.get('reply_rate', '0%'))
            st.metric("Bounce Rate", stats.get('bounce_rate', '0%'))
        
    with col2:
        st.subheader("🎯 Send Time Recommendations")
        if mgr:
            opt_prof = mgr.get_optimal_send_time('professor')
            st.write("**Best for Professors:**")
            st.write(f"Days: {', '.join(opt_prof['best_days'])}")
            st.write(f"Times: {', '.join(opt_prof['best_hours'])}")
            st.write(f"Avoid: {', '.join(opt_prof['avoid'])}")
    
    st.markdown("---")
    
    # Email history
    st.subheader("📧 Full Email History")
    tracking = load_tracking()
    if not tracking.empty:
        st.dataframe(tracking, use_container_width=True)
        
        csv = tracking.to_csv(index=False)
        st.download_button("📥 Export CSV", csv, "email_history.csv", "text/csv")
    else:
        st.info("No data yet")

elif page == "🔄 Follow-ups":
    st.title("🔄 Follow-up Management")
    
    if mgr:
        due = mgr.get_due_follow_ups()
        
        st.metric("Follow-ups Due Today", len(due))
        
        if due:
            st.subheader("Pending Follow-ups")
            df = pd.DataFrame(due)
            st.dataframe(df, use_container_width=True)
            
            if st.button("📤 Send All Follow-ups"):
                st.warning("Follow-up sending coming soon!")
        else:
            st.success("No follow-ups due today!")
        
        st.markdown("---")
        
        st.subheader("📝 Mark as Replied")
        reply_email = st.text_input("Email address that replied")
        if st.button("Mark as Replied"):
            if reply_email:
                mgr.mark_replied(reply_email)
                st.success(f"✅ Marked {reply_email} as replied")
    else:
        st.warning("Advanced features not available")

elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    
    st.subheader("📊 Warmup Schedule")
    if mgr:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Warmup Day", mgr.warmup_day)
        with col2:
            st.metric("Daily Limit", mgr.get_warmup_limit())
        with col3:
            if st.button("Reset Warmup"):
                mgr.reset_warmup()
                st.rerun()
        
        st.markdown("""
        **Warmup Schedule:**
        - Days 1-3: 10 emails/day
        - Days 4-7: 25 emails/day
        - Days 8-14: 50 emails/day
        - Days 15+: 100 emails/day
        """)
    
    st.markdown("---")
    
    st.subheader("⛔ Blacklist Management")
    if mgr:
        col1, col2 = st.columns(2)
        with col1:
            bl_email = st.text_input("Email to blacklist")
        with col2:
            bl_domain = st.text_input("Domain to blacklist (e.g., spam.com)")
        
        if st.button("Add to Blacklist"):
            if bl_email:
                mgr.add_to_blacklist(email=bl_email, reason="Manual")
                st.success(f"Added {bl_email}")
            if bl_domain:
                mgr.add_to_blacklist(domain=bl_domain, reason="Manual")
                st.success(f"Added {bl_domain}")
        
        blacklist = mgr.get_blacklist()
        if blacklist:
            st.dataframe(pd.DataFrame(blacklist), use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("📤 Export Data")
    if mgr:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export to CSV"):
                path = mgr.export_to_csv()
                st.success(f"Exported to {path}")
        with col2:
            if st.button("Export to JSON"):
                path = mgr.export_to_json()
                st.success(f"Exported to {path}")

elif page == "🛡️ Safety Controls":
    st.title("🛡️ Safety Controls")
    
    # Campaign control
    st.subheader("⏸️ Campaign Control")
    if mgr:
        col1, col2 = st.columns(2)
        with col1:
            if mgr.is_campaign_paused():
                st.error("🔴 Campaign is PAUSED")
                if st.button("▶️ Resume Campaign", type="primary"):
                    mgr.resume_campaign()
                    st.rerun()
            else:
                st.success("🟢 Campaign is ACTIVE")
                if st.button("⏸️ Pause Campaign"):
                    mgr.pause_campaign()
                    st.rerun()
        
        with col2:
            st.info("""
            **When paused:**
            - No new emails will be sent
            - Follow-ups are held
            - You can still preview emails
            """)
    
    st.markdown("---")
    
    st.subheader("📊 Daily Limits")
    if stats:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sent Today", stats.get('sent_today', 0))
        with col2:
            st.metric("Limit Today", stats.get('daily_limit', 50))
        with col3:
            st.metric("Remaining", stats.get('remaining_today', 50))
    
    st.markdown("---")
    
    st.subheader("👮 Safety Health Check")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Check Portfolio
        try:
            import requests
            r = requests.get("https://anamay.vercel.app", timeout=2)
            if r.status_code == 200:
                st.success("✅ Portfolio Online")
            else:
                st.error(f"❌ Portfolio Down ({r.status_code})")
        except:
            st.error("❌ Portfolio Unreachable")
            
    with col2:
        # Check Resume
        if os.path.exists("Resume_Anamay_Tripathy.pdf"):
            size = os.path.getsize("Resume_Anamay_Tripathy.pdf")
            if size > 1000:
                st.success(f"✅ Resume Linked ({size/1024:.1f}KB)")
            else:
                st.error("❌ Resume Corrupt")
        else:
            st.error("❌ Resume Missing")
            
    with col3:
        # Check Config
        if os.getenv("GEMINI_API_KEY"):
            st.success("✅ AI Keys Loaded")
        else:
            st.warning("⚠️ AI Keys Missing")

    st.markdown("---")
    
    st.subheader("🧪 System Test")
    if st.button("Test System"):
        with st.spinner("Testing..."):
            try:
                import system
                vs = system.VerifiedEmailSystem()
                st.success("✅ System initialized!")
                
                if mgr:
                    st.success(f"✅ Advanced features: Day {mgr.warmup_day}, Limit {mgr.get_warmup_limit()}")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("v2.0 - All 20 Features")
st.sidebar.markdown("Made with ❤️ by Anamay")
