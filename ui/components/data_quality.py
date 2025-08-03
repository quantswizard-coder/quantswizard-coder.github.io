"""Data quality monitoring widgets for Streamlit dashboard."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


def display_data_quality_metrics(validation_results: Dict[str, Any]):
    """Display data quality metrics in a dashboard format.
    
    Args:
        validation_results: Dictionary containing validation results from DataValidator
    """
    
    st.subheader("📊 Data Quality Monitoring")
    
    # Overall quality score
    quality_score = validation_results.get('quality_score', 0.0)
    
    # Color coding for quality score
    if quality_score >= 0.95:
        color = "green"
        status = "Excellent"
    elif quality_score >= 0.85:
        color = "orange"
        status = "Good"
    else:
        color = "red"
        status = "Poor"
    
    # Main quality metric
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Overall Quality Score",
            f"{quality_score:.1%}",
            delta=None,
            help="Overall data quality assessment"
        )
    
    with col2:
        completeness = validation_results.get('metrics', {}).get('completeness_percent', 0)
        st.metric(
            "Data Completeness",
            f"{completeness:.1f}%",
            delta=None,
            help="Percentage of non-missing data points"
        )
    
    with col3:
        record_count = validation_results.get('metrics', {}).get('record_count', 0)
        st.metric(
            "Total Records",
            f"{record_count:,}",
            delta=None,
            help="Total number of data records"
        )
    
    with col4:
        duplicate_percent = validation_results.get('metrics', {}).get('duplicate_percent', 0)
        st.metric(
            "Duplicate Rate",
            f"{duplicate_percent:.2f}%",
            delta=None,
            help="Percentage of duplicate records"
        )
    
    # Quality status indicator
    st.markdown(f"**Status:** :{color}[{status}]")
    
    # Issues and recommendations
    issues = validation_results.get('issues', [])
    recommendations = validation_results.get('recommendations', [])
    
    if issues:
        st.warning("⚠️ **Data Quality Issues Detected:**")
        for issue in issues:
            st.write(f"• {issue}")
    
    if recommendations:
        st.info("💡 **Recommendations:**")
        for rec in recommendations:
            st.write(f"• {rec}")
    
    if not issues:
        st.success("✅ No data quality issues detected!")


def display_provider_status(provider_data: Dict[str, Dict]):
    """Display status of multiple data providers.
    
    Args:
        provider_data: Dictionary mapping provider names to their status data
    """
    
    st.subheader("🔌 Data Provider Status")
    
    # Create columns for each provider
    cols = st.columns(len(provider_data))
    
    for i, (provider, status_data) in enumerate(provider_data.items()):
        with cols[i]:
            # Provider status
            is_active = status_data.get('active', False)
            last_update = status_data.get('last_update', 'Unknown')
            uptime = status_data.get('uptime_percent', 0)
            
            # Status indicator
            if is_active and uptime > 95:
                status_color = "green"
                status_icon = "✅"
            elif is_active and uptime > 80:
                status_color = "orange"
                status_icon = "⚠️"
            else:
                status_color = "red"
                status_icon = "❌"
            
            st.markdown(f"**{provider.title()}**")
            st.markdown(f"{status_icon} Status: :{status_color}[{'Active' if is_active else 'Inactive'}]")
            st.write(f"Uptime: {uptime:.1f}%")
            st.write(f"Last Update: {last_update}")


def display_data_freshness(data_timestamps: Dict[str, datetime]):
    """Display data freshness indicators.
    
    Args:
        data_timestamps: Dictionary mapping data sources to their last update timestamps
    """
    
    st.subheader("🕐 Data Freshness")
    
    current_time = datetime.now()
    
    for source, timestamp in data_timestamps.items():
        time_diff = current_time - timestamp
        
        # Color coding based on freshness
        if time_diff < timedelta(minutes=5):
            color = "green"
            freshness = "Very Fresh"
        elif time_diff < timedelta(hours=1):
            color = "orange"
            freshness = "Fresh"
        elif time_diff < timedelta(hours=24):
            color = "orange"
            freshness = "Stale"
        else:
            color = "red"
            freshness = "Very Stale"
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**{source}:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        with col2:
            st.markdown(f":{color}[{freshness}]")


def create_quality_trend_chart(quality_history: pd.DataFrame) -> go.Figure:
    """Create a chart showing data quality trends over time.
    
    Args:
        quality_history: DataFrame with timestamp and quality metrics
        
    Returns:
        Plotly figure
    """
    
    fig = go.Figure()
    
    # Quality score trend
    if 'quality_score' in quality_history.columns:
        fig.add_trace(
            go.Scatter(
                x=quality_history.index,
                y=quality_history['quality_score'] * 100,
                mode='lines+markers',
                name='Quality Score (%)',
                line=dict(color='blue', width=2)
            )
        )
    
    # Completeness trend
    if 'completeness' in quality_history.columns:
        fig.add_trace(
            go.Scatter(
                x=quality_history.index,
                y=quality_history['completeness'],
                mode='lines+markers',
                name='Completeness (%)',
                line=dict(color='green', width=2)
            )
        )
    
    # Add quality thresholds
    fig.add_hline(y=95, line_dash="dash", line_color="green", 
                  annotation_text="Excellent Threshold")
    fig.add_hline(y=85, line_dash="dash", line_color="orange", 
                  annotation_text="Good Threshold")
    
    fig.update_layout(
        title="Data Quality Trends",
        xaxis_title="Time",
        yaxis_title="Quality Metrics (%)",
        height=400,
        showlegend=True,
        template="plotly_white"
    )
    
    return fig


def display_cross_provider_validation(comparison_results: Dict[str, Any]):
    """Display cross-provider validation results.
    
    Args:
        comparison_results: Results from cross-provider validation
    """
    
    st.subheader("🔄 Cross-Provider Validation")
    
    # Overall validation status
    is_valid = comparison_results.get('is_valid', False)
    max_deviation = comparison_results.get('metrics', {}).get('max_price_deviation', 0)
    providers_compared = comparison_results.get('metrics', {}).get('providers_compared', [])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_color = "green" if is_valid else "red"
        status_text = "✅ Valid" if is_valid else "❌ Invalid"
        st.markdown(f"**Validation Status:** :{status_color}[{status_text}]")
    
    with col2:
        st.metric(
            "Max Price Deviation",
            f"{max_deviation:.2%}",
            help="Maximum price difference between providers"
        )
    
    with col3:
        st.metric(
            "Providers Compared",
            len(providers_compared),
            help="Number of providers in comparison"
        )
    
    # Issues and recommendations
    issues = comparison_results.get('issues', [])
    if issues:
        st.warning("⚠️ **Cross-Provider Issues:**")
        for issue in issues:
            st.write(f"• {issue}")
    else:
        st.success("✅ All providers show consistent data!")


def display_data_monitoring_summary():
    """Display a comprehensive data monitoring summary."""
    
    st.title("📊 Data Quality Dashboard")
    
    # Placeholder data - in real implementation, this would come from actual monitoring
    sample_validation = {
        'quality_score': 0.98,
        'is_valid': True,
        'metrics': {
            'completeness_percent': 99.5,
            'record_count': 8760,
            'duplicate_percent': 0.1,
            'max_price_deviation': 0.015
        },
        'issues': [],
        'recommendations': []
    }
    
    sample_providers = {
        'yfinance': {
            'active': True,
            'last_update': '2025-08-02 11:30:00',
            'uptime_percent': 99.9
        },
        'tiingo': {
            'active': True,
            'last_update': '2025-08-02 11:29:45',
            'uptime_percent': 98.5
        },
        'alpha_vantage': {
            'active': False,
            'last_update': '2025-08-02 10:15:00',
            'uptime_percent': 75.2
        }
    }
    
    sample_timestamps = {
        'BTC-USD': datetime.now() - timedelta(minutes=2),
        'ETH-USD': datetime.now() - timedelta(minutes=5),
        'Market Data': datetime.now() - timedelta(minutes=1)
    }
    
    # Display components
    display_data_quality_metrics(sample_validation)
    st.divider()
    
    display_provider_status(sample_providers)
    st.divider()
    
    display_data_freshness(sample_timestamps)
    st.divider()
    
    display_cross_provider_validation(sample_validation)


if __name__ == "__main__":
    # For testing the component
    display_data_monitoring_summary()
