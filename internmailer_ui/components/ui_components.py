"""
UI Components Module

Professional UI components using streamlit-extras for polished visuals.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
try:
    from streamlit_extras.card import card
    from streamlit_extras.badges import badge
    from streamlit_extras.metric_cards import style_metric_cards
    from streamlit_extras.colored_header import colored_header
    from streamlit_extras.add_vertical_space import add_vertical_space
    from streamlit_extras.stoggle import stoggle
    EXTRAS_AVAILABLE = True
except ImportError:
    EXTRAS_AVAILABLE = False


def create_metric_card(title: str, value: str, delta: Optional[str] = None, 
                      delta_color: str = "normal", help_text: Optional[str] = None,
                      border_left_color: str = "#0066CC") -> None:
    """
    Create a professional metric card with custom styling.
    
    Args:
        title: The metric title
        value: The metric value
        delta: Optional delta value
        delta_color: Color for delta ("normal", "inverse", "off")
        help_text: Optional help text
        border_left_color: Left border color
    """
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col2:
        # Create container with custom styling
        with st.container():
            st.markdown(f"""
            <div style="
                background-color: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                border-left: 4px solid {border_left_color};
                margin: 0.5rem 0;
            ">
                <div style="
                    font-size: 0.9rem;
                    color: #6C757D;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 0.5rem;
                ">{title}</div>
                <div style="
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: {border_left_color};
                    margin-bottom: 0.25rem;
                ">{value}</div>
                {f'<div style="font-size: 0.8rem; color: #28A745;">{delta}</div>' if delta else ''}
                {f'<div style="font-size: 0.75rem; color: #6C757D; margin-top: 0.5rem;">{help_text}</div>' if help_text else ''}
            </div>
            """, unsafe_allow_html=True)


def create_status_badge(status: str, status_type: str = "info") -> None:
    """
    Create a status badge with appropriate styling.
    
    Args:
        status: Status text
        status_type: Type of status ("success", "warning", "danger", "info")
    """
    color_map = {
        "success": {"bg": "#D4EDDA", "text": "#28A745", "border": "#C3E6CB"},
        "warning": {"bg": "#FFF3CD", "text": "#856404", "border": "#FFEAA7"},
        "danger": {"bg": "#F8D7DA", "text": "#DC3545", "border": "#F5C6CB"},
        "info": {"bg": "#D1ECF1", "text": "#17A2B8", "border": "#BEE5EB"}
    }
    
    colors = color_map.get(status_type, color_map["info"])
    
    if EXTRAS_AVAILABLE:
        badge(type=status_type, name=status)
    else:
        st.markdown(f"""
        <span style="
            background-color: {colors['bg']};
            color: {colors['text']};
            border: 1px solid {colors['border']};
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: inline-block;
            margin: 0.25rem;
        ">{status}</span>
        """, unsafe_allow_html=True)


def create_info_card(title: str, content: str, icon: str = "ℹ️", 
                    card_color: str = "#0066CC") -> None:
    """
    Create an information card with icon and styling.
    
    Args:
        title: Card title
        content: Card content
        icon: Icon emoji
        card_color: Primary color for the card
    """
    if EXTRAS_AVAILABLE:
        with card(title=f"{icon} {title}", text=content, 
                 styles={"card": {"background-color": "#F8F9FA"}}):
            pass
    else:
        st.markdown(f"""
        <div style="
            background-color: #F8F9FA;
            border: 1px solid #DEE2E6;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        ">
            <h4 style="
                color: {card_color};
                margin-bottom: 1rem;
                font-weight: 600;
            ">{icon} {title}</h4>
            <p style="
                color: #495057;
                margin: 0;
                line-height: 1.6;
            ">{content}</p>
        </div>
        """, unsafe_allow_html=True)


def create_section_header(title: str, description: Optional[str] = None,
                         color: str = "#0066CC") -> None:
    """
    Create a styled section header.
    
    Args:
        title: Section title
        description: Optional description
        color: Header color
    """
    if EXTRAS_AVAILABLE:
        colored_header(
            label=title,
            description=description,
            color_name="blue-70"
        )
    else:
        st.markdown(f"""
        <div style="
            border-bottom: 3px solid {color};
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        ">
            <h2 style="
                color: {color};
                margin: 0;
                font-weight: 600;
                font-size: 2rem;
            ">{title}</h2>
            {f'<p style="color: #6C757D; margin: 0.5rem 0 0 0; font-size: 1.1rem;">{description}</p>' if description else ''}
        </div>
        """, unsafe_allow_html=True)


def create_progress_card(title: str, progress: float, total: Optional[int] = None,
                        color: str = "#0066CC") -> None:
    """
    Create a progress card with visual progress bar.
    
    Args:
        title: Progress title
        progress: Progress value (0-100 if percentage, or actual value)
        total: Total value (if not percentage)
        color: Progress bar color
    """
    if total:
        percentage = (progress / total) * 100
        display_text = f"{progress}/{total}"
    else:
        percentage = progress
        display_text = f"{progress}%"
    
    st.markdown(f"""
    <div style="
        background-color: white;
        border: 1px solid #DEE2E6;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        ">
            <h4 style="
                margin: 0;
                color: #212529;
                font-weight: 600;
            ">{title}</h4>
            <span style="
                color: {color};
                font-weight: 600;
                font-size: 1.1rem;
            ">{display_text}</span>
        </div>
        <div style="
            background-color: #E9ECEF;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, {color}, {color}DD);
                width: {percentage}%;
                height: 100%;
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_stats_grid(stats: List[Dict[str, Any]], columns: int = 3) -> None:
    """
    Create a grid of statistics cards.
    
    Args:
        stats: List of stat dictionaries with keys: title, value, delta, color
        columns: Number of columns in the grid
    """
    if EXTRAS_AVAILABLE:
        style_metric_cards()
    
    # Create columns
    cols = st.columns(columns)
    
    for i, stat in enumerate(stats):
        col_index = i % columns
        with cols[col_index]:
            create_metric_card(
                title=stat.get("title", ""),
                value=stat.get("value", ""),
                delta=stat.get("delta"),
                border_left_color=stat.get("color", "#0066CC")
            )


def create_toggle_section(title: str, content_func, default_open: bool = False) -> None:
    """
    Create a collapsible toggle section.
    
    Args:
        title: Section title
        content_func: Function to call when section is open
        default_open: Whether section starts open
    """
    if EXTRAS_AVAILABLE:
        stoggle(title, content_func, default_open)
    else:
        with st.expander(title, expanded=default_open):
            content_func()


def add_spacing(lines: int = 1) -> None:
    """
    Add vertical spacing.
    
    Args:
        lines: Number of lines of spacing
    """
    if EXTRAS_AVAILABLE:
        add_vertical_space(lines)
    else:
        for _ in range(lines):
            st.write("")


def create_alert_box(message: str, alert_type: str = "info", 
                    dismissible: bool = False) -> None:
    """
    Create a styled alert box.
    
    Args:
        message: Alert message
        alert_type: Type of alert ("info", "success", "warning", "error")
        dismissible: Whether the alert can be dismissed
    """
    icon_map = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️", 
        "error": "❌"
    }
    
    color_map = {
        "info": {"bg": "#D1ECF1", "border": "#17A2B8", "text": "#0C5460"},
        "success": {"bg": "#D4EDDA", "border": "#28A745", "text": "#155724"},
        "warning": {"bg": "#FFF3CD", "border": "#FFC107", "text": "#856404"},
        "error": {"bg": "#F8D7DA", "border": "#DC3545", "text": "#721C24"}
    }
    
    colors = color_map.get(alert_type, color_map["info"])
    icon = icon_map.get(alert_type, "ℹ️")
    
    st.markdown(f"""
    <div style="
        background-color: {colors['bg']};
        border: 1px solid {colors['border']};
        border-left: 4px solid {colors['border']};
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: {colors['text']};
    ">
        <strong>{icon} </strong>{message}
    </div>
    """, unsafe_allow_html=True)


def create_data_table(data, title: Optional[str] = None, 
                     searchable: bool = True) -> None:
    """
    Create a styled data table.
    
    Args:
        data: DataFrame or data to display
        title: Optional table title
        searchable: Whether to make table searchable
    """
    if title:
        create_section_header(title)
    
    # Apply table styling
    st.markdown("""
    <style>
    .dataframe {
        border: none !important;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .dataframe thead th {
        background: linear-gradient(135deg, #0066CC, #3385D6);
        color: white;
        font-weight: 600;
        padding: 1rem;
        border: none;
    }
    .dataframe tbody td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #DEE2E6;
    }
    .dataframe tbody tr:hover {
        background-color: #F8F9FA;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.dataframe(data, use_container_width=True)
