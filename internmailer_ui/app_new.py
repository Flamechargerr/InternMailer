"""InternMailer - AI-Powered Email Campaign Manager"""

import streamlit as st
from services.config_service import get_config
from services.state_service import state
from components.ui_utils import ui
from pages import home, analytics, settings, campaign_builder, real_time_monitoring

# Initialize config
config = get_config()

# Page config
st.set_page_config(
    page_title=config.get('ui.page_title', 'InternMailer'),
    page_icon=config.get('ui.page_icon', '📧'),
    layout=config.get('ui.layout', 'wide'),
    initial_sidebar_state=config.get('ui.sidebar_state', 'expanded')
)

def main():
    """Main application entry point."""
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
    # Sidebar navigation
    with st.sidebar:
        st.title('📧 InternMailer')
        st.write('---')
        
        # Navigation buttons
        nav_options = {
            '🏠 Dashboard': 'home',
            '📊 Analytics': 'analytics',
            '📝 Campaign Builder': 'campaign_builder',
            '📈 Real-time Monitoring': 'monitoring',
            '⚙️ Settings': 'settings'
        }
        
        for label, page in nav_options.items():
            if st.button(label, use_container_width=True, 
                       type='primary' if st.session_state.page == page else 'secondary'):
                st.session_state.page = page
                st.rerun()
        
        st.write('---')
        
        # User info
        if state.get('user.authenticated'):
            st.caption(f"👤 {state.get('user.email', 'User')}")
            if st.button('🚪 Sign Out', use_container_width=True):
                state.clear()
                st.rerun()
        else:
            if st.button('🔑 Sign In', use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()
    
    # Main content area
    if st.session_state.page == 'home':
        home.show()
    elif st.session_state.page == 'analytics':
        analytics.show()
    elif st.session_state.page == 'campaign_builder':
        campaign_builder.show()
    elif st.session_state.page == 'monitoring':
        real_time_monitoring.show()
    elif st.session_state.page == 'settings':
        settings.show()
    elif st.session_state.page == 'login':
        st.switch_page('pages/login.py')

if __name__ == "__main__":
    main()
