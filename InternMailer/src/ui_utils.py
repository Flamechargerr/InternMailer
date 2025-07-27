"""
UI utilities for standardized styling, status banners, and error handling.
Provides consistent UX components across the InternMailer application.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
import logging

# Theme colors
THEME_COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2', 
    'success': '#28a745',
    'warning': '#ffc107',
    'error': '#dc3545',
    'info': '#17a2b8',
    'light': '#f8f9fa',
    'dark': '#343a40'
}

# Standardized status banner styles
STATUS_BANNER_STYLES = {
    'success': {
        'color': THEME_COLORS['success'],
        'icon': '✅',
        'bg_color': '#d4edda',
        'border_color': '#c3e6cb'
    },
    'warning': {
        'color': THEME_COLORS['warning'],
        'icon': '⚠️',
        'bg_color': '#fff3cd',
        'border_color': '#ffeaa7'
    },
    'error': {
        'color': THEME_COLORS['error'],
        'icon': '❌',
        'bg_color': '#f8d7da',
        'border_color': '#f5c6cb'
    },
    'info': {
        'color': THEME_COLORS['info'],
        'icon': '💡',
        'bg_color': '#d1ecf1',
        'border_color': '#bee5eb'
    }
}

def apply_theme_styles():
    """Apply consistent theme styles across the application."""
    st.markdown(f"""
    <style>
        /* Main theme variables */
        :root {{
            --primary-color: {THEME_COLORS['primary']};
            --secondary-color: {THEME_COLORS['secondary']};
            --success-color: {THEME_COLORS['success']};
            --warning-color: {THEME_COLORS['warning']};
            --error-color: {THEME_COLORS['error']};
            --info-color: {THEME_COLORS['info']};
        }}
        
        /* Enhanced main header */
        .main-header {{
            background: linear-gradient(90deg, {THEME_COLORS['primary']} 0%, {THEME_COLORS['secondary']} 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .main-title {{
            font-size: 3rem;
            font-weight: bold;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .sub-title {{
            font-size: 1.2rem;
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }}
        
        /* Enhanced feature cards */
        .feature-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
            border-left: 4px solid {THEME_COLORS['primary']};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .feature-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        /* Standardized buttons */
        div.stButton > button {{
            background: linear-gradient(90deg, {THEME_COLORS['primary']} 0%, {THEME_COLORS['secondary']} 100%);
            color: white;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 5px;
            font-weight: bold;
            transition: all 0.2s ease;
        }}
        
        div.stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        
        /* Configuration status indicators */
        .config-status {{
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            border-left: 4px solid;
        }}
        
        .config-status.success {{
            background-color: {STATUS_BANNER_STYLES['success']['bg_color']};
            border-left-color: {STATUS_BANNER_STYLES['success']['color']};
            color: {STATUS_BANNER_STYLES['success']['color']};
        }}
        
        .config-status.warning {{
            background-color: {STATUS_BANNER_STYLES['warning']['bg_color']};
            border-left-color: {STATUS_BANNER_STYLES['warning']['color']};
            color: #856404;
        }}
        
        .config-status.error {{
            background-color: {STATUS_BANNER_STYLES['error']['bg_color']};
            border-left-color: {STATUS_BANNER_STYLES['error']['color']};
            color: {STATUS_BANNER_STYLES['error']['color']};
        }}
        
        /* Input help text styling */
        .help-text {{
            font-size: 0.85rem;
            color: #6c757d;
            margin-top: 0.25rem;
            font-style: italic;
        }}
        
        /* Sidebar enhancements */
        .sidebar-status {{
            padding: 0.5rem;
            border-radius: 4px;
            margin: 0.25rem 0;
            font-size: 0.9rem;
        }}
        
        /* Status indicators */
        .status-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem;
            border-radius: 4px;
            font-weight: 500;
        }}
        
        .status-indicator.success {{
            background-color: {STATUS_BANNER_STYLES['success']['bg_color']};
            color: {STATUS_BANNER_STYLES['success']['color']};
        }}
        
        .status-indicator.warning {{
            background-color: {STATUS_BANNER_STYLES['warning']['bg_color']};
            color: #856404;
        }}
        
        .status-indicator.error {{
            background-color: {STATUS_BANNER_STYLES['error']['bg_color']};
            color: {STATUS_BANNER_STYLES['error']['color']};
        }}
        
        .status-indicator.info {{
            background-color: {STATUS_BANNER_STYLES['info']['bg_color']};
            color: {STATUS_BANNER_STYLES['info']['color']};
        }}
    </style>
    """, unsafe_allow_html=True)

def show_status_banner(message: str, status_type: str = 'info', show_icon: bool = True):
    """
    Display a standardized status banner.
    
    Args:
        message: The message to display
        status_type: One of 'success', 'warning', 'error', 'info'
        show_icon: Whether to show the status icon
    """
    if status_type not in STATUS_BANNER_STYLES:
        status_type = 'info'
    
    style = STATUS_BANNER_STYLES[status_type]
    icon = style['icon'] if show_icon else ''
    
    # Use appropriate Streamlit function based on status type
    if status_type == 'success':
        st.success(f"{icon} {message}")
    elif status_type == 'warning':
        st.warning(f"{icon} {message}")
    elif status_type == 'error':
        st.error(f"{icon} {message}")
    else:  # info
        st.info(f"{icon} {message}")

def show_config_status(issues: List[str], success_message: str = "Configuration is valid"):
    """
    Display configuration status with persistent sidebar indicators.
    
    Args:
        issues: List of configuration issues
        success_message: Message to show when no issues exist
    """
    if issues:
        show_status_banner("Configuration Issues Detected", "error")
        for issue in issues:
            st.error(f"• {issue}")
        
        # Persist in sidebar
        with st.sidebar:
            st.markdown("""
            <div class="config-status error">
                <strong>⚠️ Configuration Issues</strong><br>
                Please resolve configuration issues to continue.
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔧 Setup Instructions", expanded=False):
                st.markdown("""
                **Required Setup:**
                1. Create a `.env` file in the project root
                2. Add your Gmail credentials:
                   ```
                   GMAIL_USER=your-email@gmail.com
                   GMAIL_APP_PASSWORD=your-app-password
                   ```
                3. Generate Gmail App Password:
                   - Go to Google Account settings
                   - Security → App passwords
                   - Generate password for "Mail"
                4. Ensure `data/proffesor.csv` exists
                """)
        return False
    else:
        show_status_banner(success_message, "success")
        
        # Persist success in sidebar
        with st.sidebar:
            st.markdown("""
            <div class="config-status success">
                <strong>✅ Configuration Valid</strong><br>
                All requirements are met.
            </div>
            """, unsafe_allow_html=True)
        return True

def add_tooltip(text: str, tooltip: str):
    """
    Add a tooltip to any text element.
    
    Args:
        text: The main text to display
        tooltip: The tooltip text to show on hover
    """
    st.markdown(f"""
    <span title="{tooltip}" style="cursor: help; border-bottom: 1px dotted #999;">
        {text}
    </span>
    """, unsafe_allow_html=True)

def create_input_with_help(input_func, label: str, help_text: str, **kwargs):
    """
    Create an input with standardized help text.
    
    Args:
        input_func: Streamlit input function (st.text_input, st.selectbox, etc.)
        label: Input label
        help_text: Help text to display
        **kwargs: Additional arguments for the input function
    """
    # Add help parameter to kwargs
    kwargs['help'] = help_text
    return input_func(label, **kwargs)

def safe_execute(func, error_message: str = "An error occurred", 
                show_error: bool = True, default_return=None):
    """
    Safely execute a function with standardized error handling.
    
    Args:
        func: Function to execute
        error_message: Custom error message to display
        show_error: Whether to show error banner
        default_return: Value to return if function fails
    """
    try:
        return func()
    except Exception as e:
        logging.error(f"{error_message}: {str(e)}")
        if show_error:
            show_status_banner(f"{error_message}: {str(e)}", "error")
        return default_return

def handle_network_call(func, operation_name: str, timeout_seconds: int = 30):
    """
    Handle network calls with proper error handling and user feedback.
    
    Args:
        func: Network function to execute
        operation_name: Name of the operation for error messages
        timeout_seconds: Timeout for the operation
    """
    try:
        with st.spinner(f"⏳ {operation_name}..."):
            return func()
    except Exception as e:
        error_msg = f"Failed to {operation_name.lower()}"
        
        # Categorize error types
        if "timeout" in str(e).lower():
            error_msg += " (connection timeout)"
        elif "connection" in str(e).lower():
            error_msg += " (connection failed)"
        elif "authentication" in str(e).lower():
            error_msg += " (authentication failed)"
        else:
            error_msg += f" ({str(e)[:50]}...)"
        
        show_status_banner(error_msg, "error")
        logging.error(f"{operation_name} failed: {str(e)}")
        return None

def create_metric_card(title: str, value: str, delta: str = None, 
                      help_text: str = None, status_type: str = None):
    """
    Create an enhanced metric card with optional status styling.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Change indicator (optional)
        help_text: Help text for the metric
        status_type: Status type for color coding
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if help_text:
            st.metric(title, value, delta, help=help_text)
        else:
            st.metric(title, value, delta)
    
    if status_type and status_type in STATUS_BANNER_STYLES:
        with col2:
            icon = STATUS_BANNER_STYLES[status_type]['icon']
            st.markdown(f"<div style='text-align: center; font-size: 1.5em;'>{icon}</div>", 
                       unsafe_allow_html=True)

def show_progress_with_status(progress: float, status_message: str = "Processing..."):
    """
    Show progress bar with status message.
    
    Args:
        progress: Progress value (0.0 to 1.0)
        status_message: Status message to display
    """
    progress_bar = st.progress(progress)
    status_placeholder = st.empty()
    status_placeholder.text(status_message)
    
    return progress_bar, status_placeholder

def display_error_details(error: Exception, operation: str, show_details: bool = False):
    """
    Display error details in a collapsible format.
    
    Args:
        error: The exception that occurred
        operation: The operation that failed
        show_details: Whether to show detailed error information
    """
    show_status_banner(f"Failed to {operation}", "error")
    
    if show_details:
        with st.expander("🔍 Error Details", expanded=False):
            st.code(f"""
Error Type: {type(error).__name__}
Error Message: {str(error)}
Operation: {operation}
            """)

def create_sidebar_status_panel(title: str, status_items: Dict[str, Any]):
    """
    Create a status panel in the sidebar.
    
    Args:
        title: Panel title
        status_items: Dictionary of status items with their states
    """
    with st.sidebar:
        st.markdown(f"### {title}")
        
        for item_name, item_status in status_items.items():
            if isinstance(item_status, dict):
                status_type = item_status.get('type', 'info')
                message = item_status.get('message', item_name)
                icon = STATUS_BANNER_STYLES[status_type]['icon']
                
                st.markdown(f"""
                <div class="sidebar-status">
                    {icon} <strong>{item_name}:</strong> {message}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Simple boolean status
                icon = "✅" if item_status else "❌"
                st.markdown(f"{icon} **{item_name}**")
