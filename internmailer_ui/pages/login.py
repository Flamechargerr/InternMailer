""Login page for InternMailer."""

import streamlit as st
from services.state_service import state
from components.ui_utils import ui

def show():
    """Display the login/signup form."""
    ui.page_header(
        "Welcome to InternMailer",
        "Sign in to manage your email campaigns"
    )
    
    # Two-column layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Sign In")
        
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.form_submit_button("Sign In", use_container_width=True):
                # Simple validation
                if not email or "@" not in email:
                    ui.error("Please enter a valid email address")
                    return
                
                if not password:
                    ui.error("Please enter your password")
                    return
                
                # TODO: Implement actual authentication
                # For now, just log in any non-empty credentials
                state.update({
                    'user.authenticated': True,
                    'user.email': email,
                    'user.role': 'admin'  # Default role
                }, persist=True)
                
                st.success("Successfully logged in!")
                st.rerun()
    
    with col2:
        st.markdown("### New User?")
        st.markdown("""
        Create an account to get started with InternMailer and manage 
        your email campaigns with ease.
        """)
        
        with st.expander("Create Account", expanded=False):
            with st.form("signup_form"):
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input(
                    "Create Password", 
                    type="password", 
                    key="signup_password"
                )
                confirm_password = st.text_input(
                    "Confirm Password", 
                    type="password", 
                    key="signup_confirm"
                )
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not new_email or "@" not in new_email:
                        ui.error("Please enter a valid email address")
                        return
                        
                    if not new_password or len(new_password) < 6:
                        ui.error("Password must be at least 6 characters")
                        return
                        
                    if new_password != confirm_password:
                        ui.error("Passwords do not match")
                        return
                    
                    # TODO: Implement actual user registration
                    # For now, just log the user in
                    state.update({
                        'user.authenticated': True,
                        'user.email': new_email,
                        'user.role': 'user'  # Default role for new users
                    }, persist=True)
                    
                    st.success("Account created successfully!")
                    st.rerun()
    
    # Footer with additional options
    st.markdown("---")
    st.markdown("""
    **Need help?** Contact support@internmailer.com
    
    By signing in, you agree to our Terms of Service and Privacy Policy.
    """, unsafe_allow_html=True)

# If this script is run directly, show the login page
if __name__ == "__main__":
    show()
