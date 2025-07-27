"""
Chart components for InternMailer UI

Reusable chart components using Plotly.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def email_performance_chart(data: pd.DataFrame, title: str = "Email Performance"):
    """
    Create an email performance line chart.
    
    Args:
        data: DataFrame with columns: date, sent, opens, clicks
        title: Chart title
    """
    fig = px.line(
        data, 
        x='date', 
        y=['sent', 'opens', 'clicks'],
        title=title,
        labels={'value': 'Count', 'variable': 'Metric'}
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Count",
        legend_title="Metrics"
    )
    
    return fig


def campaign_funnel_chart(campaign_data: dict):
    """
    Create a funnel chart for campaign conversion.
    
    Args:
        campaign_data: Dict with keys: sent, delivered, opened, clicked, converted
    """
    fig = go.Figure(go.Funnel(
        y=["Sent", "Delivered", "Opened", "Clicked", "Converted"],
        x=[
            campaign_data.get('sent', 0),
            campaign_data.get('delivered', 0),
            campaign_data.get('opened', 0),
            campaign_data.get('clicked', 0),
            campaign_data.get('converted', 0)
        ],
        textinfo="value+percent initial"
    ))
    
    fig.update_layout(title="Campaign Conversion Funnel")
    
    return fig


def engagement_heatmap(data: pd.DataFrame):
    """
    Create a heatmap showing engagement by day/hour.
    
    Args:
        data: DataFrame with columns: day, hour, engagement_rate
    """
    pivot_data = data.pivot(index='day', columns='hour', values='engagement_rate')
    
    fig = px.imshow(
        pivot_data,
        title="Engagement Rate by Day and Hour",
        labels=dict(x="Hour of Day", y="Day of Week", color="Engagement Rate"),
        aspect="auto"
    )
    
    return fig
