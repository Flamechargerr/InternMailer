"""
InternMailer UI - Main Application

A Streamlit-based web interface for the InternMailer application.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add parent directory to path for module imports
sys.path.append(str(Path(__file__).parent.parent))

from pages import home, analytics, settings, campaign_builder, real_time_monitoring
from services import email_service, user_service, config_service

# Set page config
st.set_page_config(
    page_title="InternMailer",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Load configuration
config = config_service.load_config()

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
        /* Main Layout */
        .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: #F8F9FA;
            color: #333;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #f8f9fa;
            border-right: 1px solid #e9ecef;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #0066CC, #3385D6);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            width: 100%;
            margin: 0.5rem 0;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #004C99, #0066CC);
            transform: translateY(-2px);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        /* Cards */
        .card {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        /* Forms */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div {
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        
        /* Tabs */
        .stTabs > div > div > div > div {
            gap: 0.5rem;
        }
        
        .stTabs > div > div > div > div > div {
            background: #f1f3f5;
            border-radius: 8px 8px 0 0;
            padding: 0.75rem 1.5rem;
            margin: 0 0.25rem;
        }
        
        .stTabs > div > div > div > div > div[data-baseweb="tab"] {
            background: #fff;
            border-bottom: 3px solid #0066CC;
            font-weight: 500;
        }
        
        /* Tables */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Status Indicators */
        .status-success {
            color: #28a745;
            font-weight: 500;
        }
        
        .status-warning {
            color: #ffc107;
            font-weight: 500;
        }
        
        .status-error {
            color: #dc3545;
            font-weight: 500;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .stButton > button {
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
            }
            
            .card {
                padding: 1rem;
            }
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
