"""
Global Economic & Financial Dashboard - Homepage
Main entry point for the Streamlit application.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from modules.data_loader import (
    load_fred_data, 
    load_yfinance_data, 
    get_latest_value,
    calculate_percentage_change,
    load_world_bank_gdp
)

# Page configuration
st.set_page_config(
    page_title="Economic & Financial Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and Header
st.title("🌍 Global Economic & Financial Dashboard")
st.markdown("### Real-time insights into global economic trends and financial markets")

# Display last refresh timestamp
col1, col2 = st.columns([3, 1])
with col2:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.divider()

# Key Metrics Row
st.subheader("📈 Key Economic Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    try:
        gdp_growth = calculate_percentage_change('A191RL1Q225SBEA', periods=1)
        if gdp_growth is not None:
            st.metric(
                label="US GDP Growth",
                value=f"{gdp_growth:.2f}%",
                delta=f"{gdp_growth:.2f}% QoQ"
            )
        else:
            st.metric(label="US GDP Growth", value="N/A")
    except:
        st.metric(label="US GDP Growth", value="N/A")

with col2:
    try:
        cpi_value = get_latest_value('CPIAUCSL')
        if cpi_value is not None:
            cpi_change = calculate_percentage_change('CPIAUCSL', periods=12)
            if cpi_change is not None:
                st.metric(
                    label="US Inflation (CPI)",
                    value=f"{cpi_change:.2f}%",
                    delta=f"{cpi_change:.2f}% YoY"
                )
            else:
                st.metric(label="US Inflation (CPI)", value=f"{cpi_value:.2f}")
        else:
            st.metric(label="US Inflation (CPI)", value="N/A")
    except:
        st.metric(label="US Inflation (CPI)", value="N/A")

with col3:
    try:
        fed_funds = get_latest_value('FEDFUNDS')
        if fed_funds is not None:
            st.metric(
                label="Fed Funds Rate",
                value=f"{fed_funds:.2f}%"
            )
        else:
            st.metric(label="Fed Funds Rate", value="N/A")
    except:
        st.metric(label="Fed Funds Rate", value="N/A")

with col4:
    try:
        oil_price = get_latest_value('DCOILWTICO')
        if oil_price is not None:
            st.metric(
                label="WTI Crude Oil",
                value=f"${oil_price:.2f}"
            )
        else:
            st.metric(label="WTI Crude Oil", value="N/A")
    except:
        st.metric(label="WTI Crude Oil", value="N/A")

with col5:
    try:
        gold_price = get_latest_value('GOLDAMGBD228NLBM')
        if gold_price is not None:
            st.metric(
                label="Gold Price",
                value=f"${gold_price:.2f}"
            )
        else:
            st.metric(label="Gold Price", value="N/A")
    except:
        st.metric(label="Gold Price", value="N/A")

st.divider()

# Main Visualizations Section
st.subheader("🌐 Global Overview")

col_left, col_right = st.columns(2)

# Left Column: World GDP Map
with col_left:
    st.markdown("#### Global GDP Growth")
    try:
        world_gdp = load_world_bank_gdp()
        if not world_gdp.empty:
            fig_map = go.Figure(data=go.Choropleth(
                locations=world_gdp['ISO3'],
                z=world_gdp['GDP Growth (%)'],
                text=world_gdp['Country'],
                colorscale='RdYlGn',
                autocolorscale=False,
                reversescale=False,
                marker_line_color='darkgray',
                marker_line_width=0.5,
                colorbar_title="GDP Growth %",
            ))
            
            fig_map.update_layout(
                geo=dict(
                    showframe=False,
                    showcoastlines=True,
                    projection_type='equirectangular'
                ),
                height=400,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("World GDP data not available")
    except Exception as e:
        st.error(f"Error loading world GDP map: {str(e)}")

# Right Column: S&P 500 Performance
with col_right:
    st.markdown("#### S&P 500 Performance (5 Years)")
    try:
        sp500_data = load_yfinance_data({"S&P 500": "^GSPC"}, period="5y")
        if "S&P 500" in sp500_data and not sp500_data["S&P 500"].empty:
            df_sp500 = sp500_data["S&P 500"]
            
            fig_sp500 = px.line(
                df_sp500,
                x=df_sp500.index,
                y='Close',
                title='',
                labels={'Close': 'Price (USD)', 'x': 'Date'}
            )
            
            fig_sp500.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=0, b=0),
                hovermode='x unified'
            )
            
            fig_sp500.update_traces(line_color='#0068c9')
            
            st.plotly_chart(fig_sp500, use_container_width=True)
        else:
            st.info("S&P 500 data not available")
    except Exception as e:
        st.error(f"Error loading S&P 500 chart: {str(e)}")

# Footer with navigation
st.divider()
st.markdown("""
### 📊 Explore More
Navigate to different pages using the sidebar:
- **Economic Indicators Deep Dive**: Analyze GDP, inflation, and unemployment across countries
- **Financial Markets Deep Dive**: Explore market indices, yield curves, and volatility
""")

# Sidebar information
with st.sidebar:
    st.header("About")
    st.markdown("""
    This dashboard provides real-time insights into:
    - 🌍 Global economic indicators
    - 📈 Financial market performance
    - 📊 Treasury yield curves
    - 📉 Market volatility metrics
    
    **Data Sources:**
    - Federal Reserve Economic Data (FRED)
    - Yahoo Finance
    - World Bank
    """)
    
    st.divider()
    st.caption("Built with Streamlit, Plotly, and Python")
