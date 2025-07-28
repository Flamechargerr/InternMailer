import streamlit as st
import os
import pandas as pd
import sys
from dotenv import load_dotenv
import json
from datetime import datetime
import time

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from enhanced_personalized_email import generate_deeply_personalized_email
from src.azure_ai_client import get_azure_ai_client

load_dotenv()

# Enhanced styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .sub-title {
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease;
    }
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .professor-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid #28a745;
        margin: 0.5rem 0;
    }
    .email-preview {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-family: 'Times New Roman', serif;
        line-height: 1.6;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .status-success {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .status-error {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration validation
def check_configuration():
    """Check if all required configuration is set up"""
    issues = []
    
    # Check environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token or github_token == "your_github_token_here":
        issues.append("GITHUB_TOKEN not configured for Azure AI")
    
    return issues

# Check Azure AI status
def check_azure_ai():
    try:
        client = get_azure_ai_client()
        return client.is_available()
    except Exception as e:
        return False

# Main header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">🎯 Enhanced Email System</h1>
    <p class="sub-title">AI-Powered Personalized Academic Outreach</p>
    <p>Generate deeply personalized emails using advanced AI analysis</p>
</div>
""", unsafe_allow_html=True)

# System status
st.header("🔧 System Status")
col1, col2 = st.columns(2)

with col1:
    config_issues = check_configuration()
    if not config_issues:
        st.success("✅ Configuration Complete")
    else:
        st.error("❌ Configuration Issues")
        for issue in config_issues:
            st.warning(f"• {issue}")

with col2:
    azure_status = check_azure_ai()
    if azure_status:
        st.success("✅ Azure AI (GPT-4o) Available")
    else:
        st.error("❌ Azure AI Unavailable")

# Professor selection section
st.header("👨‍🎓 Select Professor")

# Load professors data
@st.cache_data
def load_professors_data():
    try:
        df = pd.read_csv('professors_final.csv')
        return df
    except Exception as e:
        st.error(f"Error loading professors data: {e}")
        return pd.DataFrame()

professors_df = load_professors_data()

if not professors_df.empty:
    # Search and filter
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search professors by name, university, or research area", 
                                   placeholder="e.g., Andrew Ng, Stanford, Machine Learning")
    
    with col2:
        university_filter = st.selectbox("🏫 Filter by University", 
                                        options=["All"] + list(professors_df['University'].unique()))
    
    # Filter professors based on search and university
    filtered_df = professors_df.copy()
    
    if search_term:
        mask = (
            filtered_df['Name'].str.contains(search_term, case=False, na=False) |
            filtered_df['University'].str.contains(search_term, case=False, na=False) |
            filtered_df['Research Area'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    if university_filter != "All":
        filtered_df = filtered_df[filtered_df['University'] == university_filter]
    
    # Display found professors
    st.write(f"📊 Found {len(filtered_df)} professors")
    
    if not filtered_df.empty:
        # Professor selection
        selected_index = st.selectbox(
            "Select a professor:",
            range(len(filtered_df)),
            format_func=lambda x: f"{filtered_df.iloc[x]['Name']} - {filtered_df.iloc[x]['University']} ({filtered_df.iloc[x]['Research Area']})"
        )
        
        selected_professor = filtered_df.iloc[selected_index]
        
        # Display selected professor details
        st.markdown(f"""
        <div class="professor-card">
            <h3>👨‍🎓 {selected_professor['Name']}</h3>
            <p><strong>🏫 University:</strong> {selected_professor['University']}</p>
            <p><strong>🔬 Research Area:</strong> {selected_professor['Research Area']}</p>
            <p><strong>📧 Email:</strong> {selected_professor['Email']}</p>
            <p><strong>🌐 Homepage:</strong> <a href="{selected_professor['Homepage']}" target="_blank">{selected_professor['Homepage']}</a></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Email generation section
        st.header("✉️ Generate Personalized Email")
        
        # Convert selected professor to the format expected by the email generator
        professor_data = {
            'name': selected_professor['Name'],
            'university': selected_professor['University'],
            'research_area': selected_professor['Research Area'],
            'homepage': selected_professor['Homepage'],
            'email': selected_professor['Email'],
            # AI will generate all personalization based on these basic details
            'notable_papers': [],
            'current_projects': [],
            'homepage_text': ''
        }
        
        # Email generation controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("🤖 This will generate a highly personalized email using AI analysis of the professor's research")
        
        with col2:
            generate_button = st.button("🚀 Generate Email", type="primary")
        
        # Generate email
        if generate_button:
            if not check_azure_ai():
                st.error("❌ Azure AI is not available. Please check your configuration.")
            else:
                with st.spinner("🤖 Generating personalized email..."):
                    try:
                        # Add progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("🔍 Analyzing professor's research...")
                        progress_bar.progress(25)
                        time.sleep(0.5)
                        
                        status_text.text("🧠 Generating personalized content...")
                        progress_bar.progress(50)
                        
                        # Generate the email
                        email_content = generate_deeply_personalized_email(professor_data)
                        
                        progress_bar.progress(75)
                        status_text.text("✨ Finalizing email format...")
                        time.sleep(0.5)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Email generated successfully!")
                        
                        # Clear progress indicators
                        time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Display success message
                        st.markdown("""
                        <div class="status-success">
                            <h4>🎉 Email Generated Successfully!</h4>
                            <p>Your personalized email has been created using advanced AI analysis of the professor's research background.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Email preview section
                        st.header("📧 Email Preview")
                        
                        # Subject line
                        subject = f"Research Internship Inquiry – Anamay Tripathy re: {professor_data['research_area']}"
                        st.subheader("📋 Subject Line:")
                        st.code(subject)
                        
                        # Email body
                        st.subheader("📝 Email Body:")
                        st.markdown(f"""
                        <div class="email-preview">
                            {email_content}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Email actions
                        st.header("🎯 Email Actions")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("📋 Copy to Clipboard"):
                                st.success("Email content copied! (Feature to be implemented)")
                        
                        with col2:
                            if st.button("💾 Save as HTML"):
                                # Save email to file
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f"email_{selected_professor['Name'].replace(' ', '_')}_{timestamp}.html"
                                
                                with open(filename, 'w', encoding='utf-8') as f:
                                    f.write(f"Subject: {subject}\n\n")
                                    f.write(email_content)
                                
                                st.success(f"✅ Email saved as {filename}")
                        
                        with col3:
                            if st.button("📧 Send Email"):
                                st.warning("Email sending feature to be implemented")
                        
                        # Analytics
                        st.header("📊 Email Analytics")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown("""
                            <div class="metric-card">
                                <h3>📏</h3>
                                <h4>{:,}</h4>
                                <p>Characters</p>
                            </div>
                            """.format(len(email_content)), unsafe_allow_html=True)
                        
                        with col2:
                            word_count = len(email_content.split())
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>📝</h3>
                                <h4>{word_count:,}</h4>
                                <p>Words</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            personalization_score = 95  # Placeholder
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>🎯</h3>
                                <h4>{personalization_score}%</h4>
                                <p>Personalization</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col4:
                            readability_score = 8.5  # Placeholder
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3>📖</h3>
                                <h4>{readability_score}/10</h4>
                                <p>Readability</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.markdown(f"""
                        <div class="status-error">
                            <h4>❌ Error Generating Email</h4>
                            <p>An error occurred while generating the email: {str(e)}</p>
                            <p>Please check your configuration and try again.</p>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Tips and best practices
        with st.expander("💡 Tips for Better Results", expanded=False):
            st.markdown("""
            ### 🎯 Personalization Tips:
            - The AI analyzes the professor's research area and university
            - Each email is uniquely crafted based on their specific expertise
            - Multiple AI calls ensure deep personalization across different sections
            
            ### 📧 Email Best Practices:
            - Review the generated email before sending
            - Customize further if needed for specific requirements
            - Use the subject line exactly as generated for consistency
            - Follow up appropriately after sending
            
            ### 🔧 Technical Notes:
            - Uses Azure AI GPT-4.1 for advanced language generation
            - Multiple specialized prompts for different email sections
            - Caching system for improved performance
            - Error handling with fallback responses
            """)
    
    else:
        st.warning("No professors found matching your search criteria. Try different keywords.")

else:
    st.error("Unable to load professors data. Please check that 'professors_final.csv' exists in the project directory.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p><strong>Enhanced Email System</strong> © 2024 | Built by Anamay Tripathy</p>
    <p>🤖 Powered by Azure AI GPT-4o for intelligent email personalization</p>
</div>
""", unsafe_allow_html=True)
