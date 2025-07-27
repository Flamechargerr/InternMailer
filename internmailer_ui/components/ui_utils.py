"""
UI Utilities for InternMailer

Common UI components and utilities used across the application.
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Union, Callable
from pathlib import Path
import base64
import time

# Type aliases
Component = Any

class UIUtils:
    """Collection of UI utility functions."""
    
    @staticmethod
    def page_header(title: str, description: str = "") -> None:
        """Display a consistent page header."""
        col1, col2 = st.columns([4, 1])
        with col1:
            st.title(title)
            if description:
                st.caption(description)
        with col2:
            st.write("")
        
        st.divider()
    
    @staticmethod
    def status_indicator(status: str) -> str:
        """Get HTML for a status indicator."""
        status_colors = {
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'info': '#17a2b8',
            'default': '#6c757d'
        }
        
        color = status_colors.get(status.lower(), status_colors['default'])
        return f'<span style="color: {color}; font-weight: 500;">●</span>'
    
    @staticmethod
    def card(title: str, content: str = "", actions: List[Dict[str, Any]] = None) -> None:
        """Display a card component."""
        with st.container():
            st.markdown(f"""
            <div class="card" style="
                background: white;
                border-radius: 10px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            ">
                <h3 style="margin-top: 0; color: #2c3e50;">{title}</h3>
                <div style="margin: 1rem 0;">{content}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if actions:
                cols = st.columns(len(actions))
                for i, action in enumerate(actions):
                    with cols[i]:
                        if st.button(
                            action.get('label', ''),
                            key=f"card_action_{i}_{int(time.time())}",
                            help=action.get('tooltip'),
                            type=action.get('type', 'secondary'),
                            use_container_width=True
                        ):
                            action['on_click']()
    
    @staticmethod
    def table(data: List[Dict[str, Any]], 
              columns: Optional[List[str]] = None,
              key: str = "table") -> None:
        """Display a styled table."""
        if not data:
            st.info("No data available")
            return
            
        df = st.dataframe(
            data,
            column_config={
                col: st.column_config.Column(
                    label=col.replace('_', ' ').title(),
                    width="medium"
                ) for col in (columns or list(data[0].keys()))
            },
            use_container_width=True,
            hide_index=True,
            key=key
        )
        
        st.markdown("""
        <style>
            .stDataFrame {
                border-radius: 8px;
                overflow: hidden;
            }
            .stDataFrame th {
                background-color: #f8f9fa !important;
                font-weight: 600 !important;
            }
            .stDataFrame tr:nth-child(even) {
                background-color: #f8f9fa;
            }
        </style>
        """, unsafe_allow_html=True)
        
        return df
    
    @staticmethod
    def loading_spinner(text: str = "Loading...") -> Callable:
        """Display a loading spinner during execution."""
        return st.spinner(text)
    
    @staticmethod
    def success(message: str) -> None:
        """Display a success message."""
        st.success(message)
    
    @staticmethod
    def error(message: str) -> None:
        """Display an error message."""
        st.error(message)
    
    @staticmethod
    def warning(message: str) -> None:
        """Display a warning message."""
        st.warning(message)
    
    @staticmethod
    def info(message: str) -> None:
        """Display an info message."""
        st.info(message)

# Global instance for easy access
ui = UIUtils()
