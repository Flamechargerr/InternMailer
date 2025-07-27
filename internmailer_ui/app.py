"""
InternMailer UI - Main Application

A Streamlit-based web interface for the InternMailer application.
"""

import streamlit as st
import os
from pages import home, analytics, settings, campaign_builder, real_time_monitoring
from services import email_service, user_service


def load_css():
    """Load custom CSS styles."""
    css_file = os.path.join(os.path.dirname(__file__), 'assets', 'style.css')
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        # Fallback inline CSS if file doesn't exist
        st.markdown("""
        <style>
        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: #F8F9FA;
        }
        .main .block-container {
            padding: 2rem 1rem;
            max-width: 1200px;
        }
        h1 {
            color: #0066CC;
            font-weight: 600;
        }
        .stButton > button {
            background: linear-gradient(135deg, #0066CC, #3385D6);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #004C99, #0066CC);
            transform: translateY(-2px);
        }
        </style>
        """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="InternMailer UI",
        page_icon="📧",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS styles
    load_css()
    
    # Sidebar navigation
    st.sidebar.title("📧 InternMailer")
    
    pages = {
        "🏠 Home": "home",
        "📊 Analytics": "analytics",
        "📈 Real-time Monitoring": "real_time_monitoring",
        "⚙️ Settings": "settings",
        "✉️ Campaign Builder": "campaign_builder"
    }
    
    selected_page = st.sidebar.selectbox("Navigate to:", list(pages.keys()))
    page_name = pages[selected_page]
    
    # Main content area
    if page_name == "home":
        home.show()
    elif page_name == "analytics":
        analytics.show()
    elif page_name == "real_time_monitoring":
        real_time_monitoring.show()
    elif page_name == "settings":
        settings.show()
    elif page_name == "campaign_builder":
        campaign_builder.show_campaign_builder()


if __name__ == "__main__":
    main()
