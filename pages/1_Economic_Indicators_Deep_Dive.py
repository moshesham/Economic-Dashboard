"""
Economic Indicators Deep Dive
Interactive analysis of economic indicators across countries.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from modules.data_loader import load_fred_data

# Page configuration
st.set_page_config(
    page_title="Economic Indicators Deep Dive",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Economic Indicators Deep Dive")
st.markdown("### Compare economic indicators across countries and time periods")

# Sidebar controls
st.sidebar.header("📋 Filter Options")

# Metric selection
metric_option = st.sidebar.selectbox(
    "Select Economic Indicator",
    [
        "GDP Growth (Annual %)",
        "Inflation (CPI, Annual %)",
        "Unemployment Rate (%)"
    ]
)

# Country selection (using FRED series)
country_options = {
    "United States": {
        "GDP Growth (Annual %)": "A191RL1A225NBEA",
        "Inflation (CPI, Annual %)": "FPCPITOTLZGUSA",
        "Unemployment Rate (%)": "UNRATE"
    },
    "Euro Area": {
        "GDP Growth (Annual %)": "CLVMNACSCAB1GQEA19",
        "Inflation (CPI, Annual %)": "FPCPITOTLZGEMU",
        "Unemployment Rate (%)": "LRHUTTTTEZM156S"
    },
    "United Kingdom": {
        "GDP Growth (Annual %)": "CLVMNACSCAB1GQGB",
        "Inflation (CPI, Annual %)": "FPCPITOTLZGGBR",
        "Unemployment Rate (%)": "LRHUTTTTGBM156S"
    },
    "Japan": {
        "GDP Growth (Annual %)": "CLVMNACSCAB1GQJP",
        "Inflation (CPI, Annual %)": "FPCPITOTLZGJPN",
        "Unemployment Rate (%)": "LRHUTTTTJPM156S"
    },
    "Canada": {
        "GDP Growth (Annual %)": "CLVMNACSCAB1GQCA",
        "Inflation (CPI, Annual %)": "FPCPITOTLZGCAN",
        "Unemployment Rate (%)": "LRHUTTTTCAM156S"
    }
}

selected_countries = st.sidebar.multiselect(
    "Select Countries",
    list(country_options.keys()),
    default=["United States", "Euro Area"]
)

# Date range selection
st.sidebar.markdown("### Date Range")
default_start = datetime.now() - timedelta(days=3650)  # 10 years
default_end = datetime.now()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(default_start, default_end),
    max_value=datetime.now()
)

# Parse date range
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = default_start
    end_date = default_end

st.sidebar.divider()
st.sidebar.caption(f"Displaying data from {start_date} to {end_date}")

# Main content area
if not selected_countries:
    st.warning("⚠️ Please select at least one country from the sidebar")
else:
    try:
        # Prepare series IDs for selected countries and metric
        series_to_fetch = {}
        for country in selected_countries:
            if country in country_options:
                if metric_option in country_options[country]:
                    series_id = country_options[country][metric_option]
                    series_to_fetch[country] = series_id
        
        if series_to_fetch:
            with st.spinner("Loading data..."):
                # Load data
                df = load_fred_data(series_to_fetch)
                
                if not df.empty:
                    # Filter by date range
                    df = df.loc[start_date:end_date]
                    
                    # Remove columns with all NaN values
                    df = df.dropna(axis=1, how='all')
                    
                    if not df.empty:
                        # Create interactive chart
                        fig = px.line(
                            df,
                            x=df.index,
                            y=df.columns.tolist(),
                            title=f"{metric_option} - Comparison",
                            labels={'value': metric_option, 'variable': 'Country', 'index': 'Date'},
                            template='plotly_dark'
                        )
                        
                        fig.update_layout(
                            height=600,
                            hovermode='x unified',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        fig.update_traces(
                            hovertemplate='<b>%{fullData.name}</b><br>%{y:.2f}<extra></extra>'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display summary statistics
                        st.divider()
                        st.subheader("📊 Summary Statistics")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### Latest Values")
                            latest_values = df.iloc[-1].dropna()
                            if not latest_values.empty:
                                for country, value in latest_values.items():
                                    st.metric(label=country, value=f"{value:.2f}")
                            else:
                                st.info("No recent data available")
                        
                        with col2:
                            st.markdown("#### Average Values (Period)")
                            avg_values = df.mean()
                            for country, value in avg_values.items():
                                if not pd.isna(value):
                                    st.metric(label=country, value=f"{value:.2f}")
                        
                        # Data table (expandable)
                        with st.expander("📋 View Raw Data"):
                            st.dataframe(df.tail(50), use_container_width=True)
                    else:
                        st.warning("No data available for the selected date range")
                else:
                    st.error("Could not load data. Please check your selections and try again.")
        else:
            st.error("No valid series found for selected countries and metric")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try adjusting your filters or contact support if the issue persists.")

# Information panel
with st.sidebar:
    st.divider()
    st.markdown("### ℹ️ About this page")
    st.markdown("""
    This page allows you to:
    - Compare economic indicators across multiple countries
    - View trends over custom time periods
    - Analyze summary statistics
    
    **Data Source:** Federal Reserve Economic Data (FRED)
    """)
