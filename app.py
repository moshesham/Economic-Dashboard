"""
US Economic Dashboard - Homepage
Comprehensive view of US economic health and key indicators
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.data_loader import (
    load_fred_data,
    get_latest_value,
    calculate_percentage_change,
    calculate_yoy_change
)
from config import is_offline_mode, can_use_offline_data
from modules.auth.credentials_manager import get_credentials_manager

# Page configuration
st.set_page_config(
    page_title="US Economic Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and Header
st.title("📊 US Economic Dashboard")
st.markdown("### Comprehensive real-time insights into the US economy")

# Display last refresh timestamp
col1, col2 = st.columns([3, 1])
with col2:
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.divider()

# ========== HEADLINE METRICS ==========
st.subheader("🎯 Headline Economic Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    try:
        gdp_growth = calculate_percentage_change('A191RL1Q225SBEA', periods=1)
        if gdp_growth is not None:
            st.metric(
                label="Real GDP Growth",
                value=f"{gdp_growth:.2f}%",
                delta=f"{gdp_growth:.2f}% QoQ",
                help="Quarterly real GDP growth rate"
            )
        else:
            st.metric(label="Real GDP Growth", value="N/A")
    except:
        st.metric(label="Real GDP Growth", value="N/A")

with col2:
    try:
        unrate = get_latest_value('UNRATE')
        if unrate is not None:
            st.metric(
                label="Unemployment Rate",
                value=f"{unrate:.1f}%",
                delta_color="inverse",
                help="Civilian unemployment rate"
            )
        else:
            st.metric(label="Unemployment Rate", value="N/A")
    except:
        st.metric(label="Unemployment Rate", value="N/A")

with col3:
    try:
        cpi_yoy = calculate_yoy_change('CPIAUCSL')
        if cpi_yoy is not None:
            st.metric(
                label="Inflation (CPI)",
                value=f"{cpi_yoy:.1f}%",
                delta=f"{cpi_yoy:.1f}% YoY",
                help="Consumer Price Index, year-over-year change"
            )
        else:
            st.metric(label="Inflation (CPI)", value="N/A")
    except:
        st.metric(label="Inflation (CPI)", value="N/A")

with col4:
    try:
        fed_funds = get_latest_value('FEDFUNDS')
        if fed_funds is not None:
            st.metric(
                label="Fed Funds Rate",
                value=f"{fed_funds:.2f}%",
                help="Federal funds effective rate"
            )
        else:
            st.metric(label="Fed Funds Rate", value="N/A")
    except:
        st.metric(label="Fed Funds Rate", value="N/A")

st.divider()

# ========== EMPLOYMENT & WAGES ==========
st.subheader("💼 Employment & Wages")
col1, col2, col3, col4 = st.columns(4)

with col1:
    try:
        payems = get_latest_value('PAYEMS')
        if payems is not None:
            st.metric(
                label="Total Nonfarm Payrolls",
                value=f"{payems/1000:.1f}M",
                help="Total employed in thousands"
            )
        else:
            st.metric(label="Total Nonfarm Payrolls", value="N/A")
    except:
        st.metric(label="Total Nonfarm Payrolls", value="N/A")

with col2:
    try:
        avg_earnings = get_latest_value('CES0500000003')
        if avg_earnings is not None:
            st.metric(
                label="Avg Hourly Earnings",
                value=f"${avg_earnings:.2f}",
                help="Average hourly earnings, all employees"
            )
        else:
            st.metric(label="Avg Hourly Earnings", value="N/A")
    except:
        st.metric(label="Avg Hourly Earnings", value="N/A")

with col3:
    try:
        civpart = get_latest_value('CIVPART')
        if civpart is not None:
            st.metric(
                label="Labor Force Participation",
                value=f"{civpart:.1f}%",
                help="Percentage of population in labor force"
            )
        else:
            st.metric(label="Labor Force Participation", value="N/A")
    except:
        st.metric(label="Labor Force Participation", value="N/A")

with col4:
    try:
        icsa = get_latest_value('ICSA')
        if icsa is not None:
            st.metric(
                label="Initial Jobless Claims",
                value=f"{icsa:.0f}K",
                help="Weekly initial unemployment claims"
            )
        else:
            st.metric(label="Initial Jobless Claims", value="N/A")
    except:
        st.metric(label="Initial Jobless Claims", value="N/A")

st.divider()

# ========== CONSUMER & HOUSING ==========
st.subheader("🏠 Consumer & Housing")
col1, col2, col3, col4 = st.columns(4)

with col1:
    try:
        pce = get_latest_value('PCE')
        if pce is not None:
            st.metric(
                label="Personal Consumption",
                value=f"${pce/1000:.1f}T",
                help="Personal consumption expenditures in billions"
            )
        else:
            st.metric(label="Personal Consumption", value="N/A")
    except:
        st.metric(label="Personal Consumption", value="N/A")

with col2:
    try:
        psavert = get_latest_value('PSAVERT')
        if psavert is not None:
            st.metric(
                label="Personal Saving Rate",
                value=f"{psavert:.1f}%",
                help="Personal savings as % of disposable income"
            )
        else:
            st.metric(label="Personal Saving Rate", value="N/A")
    except:
        st.metric(label="Personal Saving Rate", value="N/A")

with col3:
    try:
        houst = get_latest_value('HOUST')
        if houst is not None:
            st.metric(
                label="Housing Starts",
                value=f"{houst:.0f}K",
                help="New housing units started (thousands)"
            )
        else:
            st.metric(label="Housing Starts", value="N/A")
    except:
        st.metric(label="Housing Starts", value="N/A")

with col4:
    try:
        mortgage = get_latest_value('MORTGAGE30US')
        if mortgage is not None:
            st.metric(
                label="30-Year Mortgage Rate",
                value=f"{mortgage:.2f}%",
                help="Average 30-year fixed mortgage rate"
            )
        else:
            st.metric(label="30-Year Mortgage Rate", value="N/A")
    except:
        st.metric(label="30-Year Mortgage Rate", value="N/A")

st.divider()

# ========== CHARTS SECTION ==========
st.subheader("📈 Economic Trends")

col_left, col_right = st.columns(2)

# Left Column: GDP Growth Trend
with col_left:
    st.markdown("#### Real GDP Growth (Last 5 Years)")
    try:
        gdp_data = load_fred_data({'Real GDP Growth': 'A191RL1Q225SBEA'})
        if not gdp_data.empty:
            # Filter last 5 years
            five_years_ago = datetime.now() - timedelta(days=365*5)
            gdp_recent = gdp_data[gdp_data.index >= five_years_ago]
            
            fig_gdp = px.line(
                gdp_recent,
                x=gdp_recent.index,
                y='Real GDP Growth',
                labels={'Real GDP Growth': 'Growth Rate (%)', 'index': 'Date'}
            )
            
            fig_gdp.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            fig_gdp.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=0, b=0),
                hovermode='x unified',
                showlegend=False
            )
            fig_gdp.update_traces(line_color='#0068c9', line_width=2)
            
            st.plotly_chart(fig_gdp, use_container_width=True)
        else:
            st.info("GDP growth data not available")
    except Exception as e:
        st.error(f"Error loading GDP chart: {str(e)}")

# Right Column: Unemployment Rate Trend
with col_right:
    st.markdown("#### Unemployment Rate (Last 5 Years)")
    try:
        unemp_data = load_fred_data({'Unemployment Rate': 'UNRATE'})
        if not unemp_data.empty:
            # Filter last 5 years
            five_years_ago = datetime.now() - timedelta(days=365*5)
            unemp_recent = unemp_data[unemp_data.index >= five_years_ago]
            
            fig_unemp = px.line(
                unemp_recent,
                x=unemp_recent.index,
                y='Unemployment Rate',
                labels={'Unemployment Rate': 'Unemployment Rate (%)', 'index': 'Date'}
            )
            
            fig_unemp.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=0, b=0),
                hovermode='x unified',
                showlegend=False
            )
            fig_unemp.update_traces(line_color='#ff6b6b', line_width=2)
            
            st.plotly_chart(fig_unemp, use_container_width=True)
        else:
            st.info("Unemployment data not available")
    except Exception as e:
        st.error(f"Error loading unemployment chart: {str(e)}")

# Footer with navigation
st.divider()
st.markdown("""
### 📊 Explore More
Navigate to different sections using the sidebar:
- **GDP & Growth**: Deep dive into economic growth, GDP components, and productivity
- **Inflation & Prices**: Consumer prices, producer prices, and inflation expectations
- **Employment & Wages**: Labor market trends, wages, and income analysis (Coming Soon)
- **Consumer & Housing**: Spending, savings, retail sales, and housing market (Coming Soon)
- **Markets & Rates**: Interest rates, Treasury yields, and monetary policy (Coming Soon)
- **API Key Management**: Configure your FRED API key for authenticated access
""")

# Sidebar information
with st.sidebar:
    st.header("About")
    st.markdown("""
    This dashboard provides comprehensive insights into:
    - 📊 **GDP & Economic Growth**
    - 💰 **Inflation & Prices**
    - 💼 **Employment & Wages**
    - 🏠 **Consumer & Housing**
    - 📈 **Markets & Interest Rates**
    
    **Data Source:**
    - Federal Reserve Economic Data (FRED)
    
    **Coverage:**
    - 60+ economic indicators
    - Real-time data updates
    - Historical trends & analysis
    """)

    # Offline mode indicator
    st.divider()
    if is_offline_mode():
        st.info("🔌 **Offline Mode**: Using cached/sample data")
    else:
        st.success("🌐 **Online Mode**: Using live data")
    
    # API Key status
    creds_manager = get_credentials_manager()
    if creds_manager.has_api_key('fred'):
        st.success("🔑 **FRED API**: Authenticated")
    else:
        st.warning("🔑 **FRED API**: Using free tier")
        st.caption("Add API key in Settings for higher limits")

    # Show data availability
    with st.expander("📊 Data Status"):
        fred_status = "✅ Available" if can_use_offline_data('fred') else "❌ Not available"

        st.markdown(f"**FRED Data:** {fred_status}")
        
        # Show metrics count
        st.markdown("**Metrics Tracked:**")
        st.markdown("- GDP & Growth: 4 series")
        st.markdown("- Inflation: 5 series")
        st.markdown("- Employment: 6 series")
        st.markdown("- Consumer: 6 series")
        st.markdown("- Housing: 4 series")
        st.markdown("- Interest Rates: 5 series")

    st.caption("Built with Streamlit, Plotly, and Python")
