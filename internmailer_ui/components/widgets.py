"""
Widget components for InternMailer UI

Reusable UI widgets and components.
"""

import streamlit as st
from typing import List, Dict, Any, Optional


def metric_card(title: str, value: str, delta: Optional[str] = None, 
                delta_color: str = "normal") -> None:
    """
    Display a metric card with title, value, and optional delta.
    
    Args:
        title: Metric title
        value: Main metric value
        delta: Change indicator (optional)
        delta_color: Color for delta ("normal", "inverse", "off")
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )


def status_badge(status: str, text: str = None) -> None:
    """
    Display a colored status badge.
    
    Args:
        status: Status type ("success", "warning", "error", "info")
        text: Custom text to display (optional)
    """
    if text is None:
        text = status.title()
    
    colors = {
        "success": "🟢",
        "warning": "🟡", 
        "error": "🔴",
        "info": "🔵"
    }
    
    icon = colors.get(status, "⚪")
    st.write(f"{icon} {text}")


def campaign_status_card(campaign: Dict[str, Any]) -> None:
    """
    Display a campaign status card.
    
    Args:
        campaign: Campaign data dictionary
    """
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader(campaign.get("name", "Unnamed Campaign"))
            st.write(f"Subject: {campaign.get('subject', 'No subject')}")
        
        with col2:
            status = campaign.get("status", "unknown")
            status_badge(status)
            st.write(f"Recipients: {campaign.get('recipients', 0):,}")
        
        with col3:
            open_rate = campaign.get("open_rate", 0)
            click_rate = campaign.get("click_rate", 0)
            st.metric("Open Rate", f"{open_rate:.1f}%")
            st.metric("Click Rate", f"{click_rate:.1f}%")


def data_table(data: List[Dict[str, Any]], columns: Optional[List[str]] = None,
               searchable: bool = True, paginated: bool = True) -> None:
    """
    Display a searchable, paginated data table.
    
    Args:
        data: List of data dictionaries
        columns: Column names to display (optional)
        searchable: Enable search functionality
        paginated: Enable pagination
    """
    if not data:
        st.info("No data to display")
        return
    
    # Search functionality
    if searchable:
        search_term = st.text_input("🔍 Search", placeholder="Enter search term...")
        if search_term:
            # Simple search across all string values
            data = [
                row for row in data 
                if any(search_term.lower() in str(v).lower() for v in row.values())
            ]
    
    # Pagination
    if paginated and len(data) > 25:
        page_size = st.selectbox("Items per page", [10, 25, 50, 100], index=1)
        total_pages = (len(data) - 1) // page_size + 1
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox("Page", range(1, total_pages + 1))
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        data = data[start_idx:end_idx]
    
    # Display table
    if columns:
        # Filter data to only show specified columns
        filtered_data = [{k: row.get(k, '') for k in columns} for row in data]
        st.dataframe(filtered_data, use_container_width=True)
    else:
        st.dataframe(data, use_container_width=True)


def progress_indicator(current: int, total: int, label: str = "Progress") -> None:
    """
    Display a progress indicator.
    
    Args:
        current: Current progress value
        total: Total/maximum value
        label: Progress label
    """
    progress = current / total if total > 0 else 0
    st.progress(progress)
    st.write(f"{label}: {current}/{total} ({progress:.1%})")


def alert_box(message: str, alert_type: str = "info", dismissible: bool = False) -> bool:
    """
    Display an alert box.
    
    Args:
        message: Alert message
        alert_type: Type of alert ("success", "info", "warning", "error")
        dismissible: Whether the alert can be dismissed
        
    Returns:
        True if alert is shown, False if dismissed
    """
    if dismissible:
        if f"alert_dismissed_{hash(message)}" not in st.session_state:
            st.session_state[f"alert_dismissed_{hash(message)}"] = False
        
        if st.session_state[f"alert_dismissed_{hash(message)}"]:
            return False
    
    if alert_type == "success":
        st.success(message)
    elif alert_type == "warning":
        st.warning(message)
    elif alert_type == "error":
        st.error(message)
    else:
        st.info(message)
    
    if dismissible:
        if st.button("✕ Dismiss", key=f"dismiss_{hash(message)}"):
            st.session_state[f"alert_dismissed_{hash(message)}"] = True
            st.rerun()
    
    return True
