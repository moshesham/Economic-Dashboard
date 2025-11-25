import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_fred_data, get_latest_value, calculate_percentage_change, calculate_yoy_change

st.set_page_config(page_title="Markets & Interest Rates", page_icon="📈", layout="wide")

st.title("📈 Financial Markets & Interest Rates")
st.markdown("Analysis of interest rates, yield curves, monetary policy, and financial market indicators")

# === INTEREST RATE METRICS ===
st.header("💹 Key Interest Rates")

col1, col2, col3, col4 = st.columns(4)

with col1:
    fed_funds = get_latest_value('FEDFUNDS')
    fed_funds_change = calculate_percentage_change('FEDFUNDS', periods=12)
    st.metric(
        "Federal Funds Rate",
        f"{fed_funds:.2f}%" if fed_funds is not None else "N/A",
        f"{fed_funds_change:+.2f}pp" if fed_funds_change is not None else "N/A"
    )

with col2:
    treasury_10y = get_latest_value('DGS10')
    treasury_10y_change = calculate_percentage_change('DGS10', periods=12)
    st.metric(
        "10-Year Treasury Yield",
        f"{treasury_10y:.2f}%" if treasury_10y is not None else "N/A",
        f"{treasury_10y_change:+.2f}pp" if treasury_10y_change is not None else "N/A"
    )

with col3:
    treasury_2y = get_latest_value('DGS2')
    treasury_2y_change = calculate_percentage_change('DGS2', periods=12)
    st.metric(
        "2-Year Treasury Yield",
        f"{treasury_2y:.2f}%" if treasury_2y is not None else "N/A",
        f"{treasury_2y_change:+.2f}pp" if treasury_2y_change is not None else "N/A"
    )

with col4:
    yield_spread = get_latest_value('T10Y2Y')
    st.metric(
        "10Y-2Y Yield Spread",
        f"{yield_spread:.2f}%" if yield_spread is not None else "N/A",
        "Inverted" if yield_spread is not None and yield_spread < 0 else "Normal" if yield_spread is not None else "N/A"
    )

# === MONETARY POLICY & MONEY SUPPLY ===
st.header("🏛️ Monetary Policy Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    m2_supply = get_latest_value('M2SL')
    m2_yoy = calculate_yoy_change('M2SL')
    st.metric(
        "M2 Money Supply",
        f"${m2_supply/1000:.2f}T" if m2_supply is not None else "N/A",
        f"{m2_yoy:+.1f}% YoY" if m2_yoy is not None else "N/A"
    )

with col2:
    prime_rate = get_latest_value('DPRIME')
    prime_change = calculate_percentage_change('DPRIME', periods=12)
    st.metric(
        "Bank Prime Loan Rate",
        f"{prime_rate:.2f}%" if prime_rate is not None else "N/A",
        f"{prime_change:+.2f}pp" if prime_change is not None else "N/A"
    )

with col3:
    treasury_3m = get_latest_value('DGS3MO')
    treasury_3m_change = calculate_percentage_change('DGS3MO', periods=12)
    st.metric(
        "3-Month Treasury Bill",
        f"{treasury_3m:.2f}%" if treasury_3m is not None else "N/A",
        f"{treasury_3m_change:+.2f}pp" if treasury_3m_change is not None else "N/A"
    )

with col4:
    treasury_5y = get_latest_value('DGS5')
    treasury_5y_change = calculate_percentage_change('DGS5', periods=12)
    st.metric(
        "5-Year Treasury Yield",
        f"{treasury_5y:.2f}%" if treasury_5y is not None else "N/A",
        f"{treasury_5y_change:+.2f}pp" if treasury_5y_change is not None else "N/A"
    )

# === YIELD CURVE ANALYSIS ===
st.header("📊 Treasury Yield Curve")

# Try to create yield curve visualization
try:
    treasury_3m_val = get_latest_value('DGS3MO')
    treasury_2y_val = get_latest_value('DGS2')
    treasury_5y_val = get_latest_value('DGS5')
    treasury_10y_val = get_latest_value('DGS10')
    treasury_30y_val = get_latest_value('DGS30')
    
    if all(v is not None for v in [treasury_3m_val, treasury_2y_val, treasury_5y_val, treasury_10y_val, treasury_30y_val]):
        yield_curve_df = pd.DataFrame({
            'Maturity': ['3-Month', '2-Year', '5-Year', '10-Year', '30-Year'],
            'Yield': [treasury_3m_val, treasury_2y_val, treasury_5y_val, treasury_10y_val, treasury_30y_val],
            'Months': [3/12, 2, 5, 10, 30]
        })
        
        fig = px.line(
            yield_curve_df,
            x='Months',
            y='Yield',
            title='Current U.S. Treasury Yield Curve',
            labels={'Months': 'Maturity (Years)', 'Yield': 'Yield (%)'},
            markers=True
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Insufficient data to create yield curve visualization")
except Exception as e:
    st.warning(f"Unable to create yield curve: {str(e)}")

# === INTEREST RATE TRENDS ===
st.header("📈 Interest Rate Trends")

col1, col2 = st.columns(2)

with col1:
    fed_funds_data = load_fred_data({'FEDFUNDS': 'FEDFUNDS'})
    if fed_funds_data is not None and not fed_funds_data.empty:
        fig = px.line(
            fed_funds_data,
            x=fed_funds_data.index,
            y='FEDFUNDS',
            title='Federal Funds Rate (10-Year History)',
            labels={'FEDFUNDS': 'Percent', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Fed funds rate data not available")

with col2:
    treasury_10y_data = load_fred_data({'DGS10': 'DGS10'})
    if treasury_10y_data is not None and not treasury_10y_data.empty:
        fig = px.line(
            treasury_10y_data,
            x=treasury_10y_data.index,
            y='DGS10',
            title='10-Year Treasury Yield (10-Year History)',
            labels={'DGS10': 'Percent', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("10-year treasury data not available")

# === YIELD SPREAD TRACKING ===
st.header("📉 Yield Spread Analysis (Recession Indicator)")

col1, col2 = st.columns(2)

with col1:
    spread_10y2y_data = load_fred_data({'T10Y2Y': 'T10Y2Y'})
    if spread_10y2y_data is not None and not spread_10y2y_data.empty:
        fig = px.line(
            spread_10y2y_data,
            x=spread_10y2y_data.index,
            y='T10Y2Y',
            title='10-Year minus 2-Year Treasury Spread (10-Year History)',
            labels={'T10Y2Y': 'Percentage Points', 'DATE': 'Date'}
        )
        # Add horizontal line at 0 to show inversion
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Inversion Threshold")
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Yield spread data not available")

with col2:
    treasury_2y_data = load_fred_data({'DGS2': 'DGS2'})
    if treasury_2y_data is not None and not treasury_2y_data.empty:
        fig = px.line(
            treasury_2y_data,
            x=treasury_2y_data.index,
            y='DGS2',
            title='2-Year Treasury Yield (10-Year History)',
            labels={'DGS2': 'Percent', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("2-year treasury data not available")

# === MONEY SUPPLY TRENDS ===
st.header("💰 Money Supply Growth")

col1, col2 = st.columns(2)

with col1:
    m2_data = load_fred_data({'M2SL': 'M2SL'})
    if m2_data is not None and not m2_data.empty:
        fig = px.line(
            m2_data,
            x=m2_data.index,
            y='M2SL',
            title='M2 Money Supply (10-Year History)',
            labels={'M2SL': 'Billions of Dollars', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("M2 money supply data not available")

with col2:
    prime_rate_data = load_fred_data({'DPRIME': 'DPRIME'})
    if prime_rate_data is not None and not prime_rate_data.empty:
        fig = px.line(
            prime_rate_data,
            x=prime_rate_data.index,
            y='DPRIME',
            title='Bank Prime Loan Rate (10-Year History)',
            labels={'DPRIME': 'Percent', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Prime rate data not available")

# === FOOTER ===
st.markdown("---")
st.markdown("""
**Policy & Short-Term Rates:**
- **FEDFUNDS**: Federal Funds Effective Rate (Target Policy Rate)
- **DGS3MO**: 3-Month Treasury Bill (Secondary Market Rate)
- **DPRIME**: Bank Prime Loan Rate (Commercial Lending Benchmark)

**Treasury Yield Curve:**
- **DGS2**: 2-Year Treasury Constant Maturity Rate
- **DGS5**: 5-Year Treasury Constant Maturity Rate
- **DGS10**: 10-Year Treasury Constant Maturity Rate
- **DGS30**: 30-Year Treasury Constant Maturity Rate
- **T10Y2Y**: 10-Year minus 2-Year Treasury Spread (Recession Indicator)

**Money Supply:**
- **M2SL**: M2 Money Stock (Currency + Deposits + Money Market Funds)

*Data Source: Federal Reserve Economic Data (FRED)*
""")
