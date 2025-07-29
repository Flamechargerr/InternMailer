"""
Shared UI Components
Provides consistent styling and reusable UI components for the InternMailer application
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime

class UIComponents:
    """Shared UI components and styling"""
    
    @staticmethod
    def apply_global_styles():
        """Apply global CSS styling"""
        st.markdown("""
        <style>
            .main-header {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 10px;
                color: white;
                text-align: center;
                margin-bottom: 2rem;
            }
            .main-title {
                font-size: 3rem;
                font-weight: bold;
                margin: 0;
            }
            .sub-title {
                font-size: 1.2rem;
                margin: 0.5rem 0 0 0;
                opacity: 0.9;
            }
            .feature-card {
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 1rem 0;
                border-left: 4px solid #667eea;
            }
            .professor-card {
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                margin: 0.5rem 0;
                border-left: 4px solid #667eea;
                transition: all 0.2s ease;
            }
            .professor-card:hover {
                background: #e9ecef;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .status-success {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                padding: 0.75rem;
                border-radius: 5px;
                margin: 0.5rem 0;
            }
            .status-warning {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 0.75rem;
                border-radius: 5px;
                margin: 0.5rem 0;
            }
            .status-error {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
                padding: 0.75rem;
                border-radius: 5px;
                margin: 0.5rem 0;
            }
            .email-preview {
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid #dee2e6;
                margin: 1rem 0;
            }
            .metric-card {
                background: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 0.5rem 0;
                text-align: center;
            }
            div.stButton > button {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 0.5rem 2rem;
                border-radius: 5px;
                font-weight: bold;
                transition: all 0.2s ease;
            }
            div.stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_main_header(title: str, subtitle: str = ""):
        """Create the main header with consistent styling"""
        st.markdown(f"""
        <div class="main-header">
            <h1 class="main-title">{title}</h1>
            {f'<p class="sub-title">{subtitle}</p>' if subtitle else ''}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_status_banner(message: str, status_type: str = "info"):
        """Create a status banner with different types"""
        status_class = f"status-{status_type}"
        st.markdown(f"""
        <div class="{status_class}">
            {message}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_navigation_cards():
        """Create navigation cards for the main page"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h3>📧 Email with CV</h3>
                <p>Send personalized emails with automatic CV attachment. Perfect for individual outreach to specific professors.</p>
                <ul>
                    <li>AI-powered personalization</li>
                    <li>Automatic CV attachment</li>
                    <li>Real-time email preview</li>
                    <li>Test mode available</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h3>🚀 Bulk Outreach</h3>
                <p>Launch personalized email campaigns to professors worldwide. Upload your resume, select preferences, and let AI generate tailored emails.</p>
                <ul>
                    <li>AI-powered email generation</li>
                    <li>Resume parsing & analysis</li>
                    <li>Duplicate detection</li>
                    <li>Dry run & live modes</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <h3>📅 Follow-ups</h3>
                <p>Track and manage your follow-up emails with advanced scheduling and analytics.</p>
                <ul>
                    <li>Automated follow-up scheduling</li>
                    <li>Campaign management</li>
                    <li>Response tracking</li>
                    <li>Analytics & insights</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def create_metrics_row(metrics: Dict[str, Any]):
        """Create a row of metrics with consistent styling"""
        cols = st.columns(len(metrics))
        
        for i, (key, value) in enumerate(metrics.items()):
            with cols[i]:
                if isinstance(value, dict):
                    st.metric(
                        label=value.get('label', key),
                        value=value.get('value', 0),
                        delta=value.get('delta'),
                        help=value.get('help')
                    )
                else:
                    st.metric(label=key, value=value)
    
    @staticmethod
    def create_email_preview(subject: str, body: str):
        """Create an email preview with consistent formatting"""
        st.subheader("📧 Email Preview")
        
        st.markdown("**Subject:**")
        st.code(subject)
        
        st.markdown("**Body:**")
        st.markdown(f"""
        <div class="email-preview">
            {body}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_professor_selection_interface(professors_df, key_prefix=""):
        """Create professor selection interface"""
        if professors_df.empty:
            st.warning("No professors found matching your criteria.")
            return None
        
        st.write(f"📊 Found {len(professors_df)} professors")
        
        # Professor selection
        selected_index = st.selectbox(
            "Select a professor:",
            range(len(professors_df)),
            format_func=lambda x: f"{professors_df.iloc[x]['Name']} - {professors_df.iloc[x]['University']} ({professors_df.iloc[x]['Research Area']})",
            key=f"{key_prefix}_professor_select"
        )
        
        return professors_df.iloc[selected_index]
    
    @staticmethod
    def create_campaign_settings():
        """Create campaign settings interface"""
        st.header("⚙️ Campaign Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            season = st.selectbox(
                "Internship Season",
                ["Any", "Winter", "Summer"],
                help="Select the preferred internship season"
            )
            
            batch_size = st.slider(
                "Batch Size",
                min_value=1,
                max_value=100,
                value=10,
                help="Number of emails to send in this batch"
            )
        
        with col2:
            funding = st.selectbox(
                "Funding Preference",
                ["Any", "Paid", "Unpaid"],
                help="Select funding preference for internships"
            )
            
            mode = st.radio(
                "Mode",
                ["Dry Run", "Live Send"],
                help="Dry Run: Preview emails. Live Send: Actually send emails"
            )
        
        countries = st.multiselect(
            "Target Countries (Optional)",
            ["US", "UK", "Europe", "Singapore", "Canada", "Australia", "Other"],
            help="Choose countries to target for outreach"
        )
        
        return {
            'season': season,
            'funding': funding,
            'mode': mode,
            'batch_size': batch_size,
            'countries': countries
        }
    
    @staticmethod
    def create_recent_activity_log(activities: List[Dict[str, Any]], title: str = "Recent Activity"):
        """Create a recent activity log display"""
        if not activities:
            return
        
        st.header(f"📊 {title}")
        
        for activity in activities[-5:]:  # Show last 5
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                
                with col1:
                    st.write(f"👨‍🔬 **{activity.get('professor', activity.get('recipient', 'Unknown'))}**")
                
                with col2:
                    st.write(f"🏛️ {activity.get('university', 'Unknown')}")
                
                with col3:
                    status = activity.get('status', 'unknown')
                    status_icon = "✅" if status == 'sent' else "❌"
                    st.write(f"{status_icon} {status.title()}")
                
                with col4:
                    timestamp = activity.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            st.write(dt.strftime("%m/%d %H:%M"))
                        except:
                            st.write("Recent")
                    else:
                        st.write("—")
            
            st.divider()

# Global UI components instance
ui_components = UIComponents()
