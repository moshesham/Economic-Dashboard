import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_fred_data, get_latest_value, calculate_percentage_change, calculate_yoy_change

st.set_page_config(page_title="Consumer & Housing", page_icon="🏠", layout="wide")

st.title("🏠 Consumer Spending & Housing Market")
st.markdown("Analysis of consumer behavior, personal spending, savings trends, and housing market dynamics")

# === CONSUMER SPENDING METRICS ===
st.header("🛒 Consumer Spending & Savings")

col1, col2, col3, col4 = st.columns(4)

with col1:
    pce = get_latest_value('PCE')
    pce_yoy = calculate_yoy_change('PCE')
    st.metric(
        "Personal Consumption Expenditures",
        f"${pce/1000:.2f}T" if pce is not None else "N/A",
        f"{pce_yoy:+.1f}% YoY" if pce_yoy is not None else "N/A"
    )

with col2:
    real_pce = get_latest_value('PCEC96')
    real_pce_yoy = calculate_yoy_change('PCEC96')
    st.metric(
        "Real PCE (Chained 2017 $)",
        f"${real_pce/1000:.2f}T" if real_pce is not None else "N/A",
        f"{real_pce_yoy:+.1f}% YoY" if real_pce_yoy is not None else "N/A"
    )

with col3:
    savings_rate = get_latest_value('PSAVERT')
    savings_change = calculate_percentage_change('PSAVERT', periods=12)
    st.metric(
        "Personal Saving Rate",
        f"{savings_rate:.1f}%" if savings_rate is not None else "N/A",
        f"{savings_change:+.1f}pp" if savings_change is not None else "N/A"
    )

with col4:
    retail_sales = get_latest_value('RSXFS')
    retail_yoy = calculate_yoy_change('RSXFS')
    st.metric(
        "Retail Sales (ex Food Services)",
        f"${retail_sales:.0f}B" if retail_sales is not None else "N/A",
        f"{retail_yoy:+.1f}% YoY" if retail_yoy is not None else "N/A"
    )

# === HOUSING MARKET METRICS ===
st.header("🏘️ Housing Market Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    housing_starts = get_latest_value('HOUST')
    starts_yoy = calculate_yoy_change('HOUST')
    st.metric(
        "Housing Starts",
        f"{housing_starts:.0f}K" if housing_starts is not None else "N/A",
        f"{starts_yoy:+.1f}% YoY" if starts_yoy is not None else "N/A"
    )

with col2:
    home_prices = get_latest_value('CSUSHPISA')
    prices_yoy = calculate_yoy_change('CSUSHPISA')
    st.metric(
        "Case-Shiller Home Price Index",
        f"{home_prices:.1f}" if home_prices is not None else "N/A",
        f"{prices_yoy:+.1f}% YoY" if prices_yoy is not None else "N/A"
    )

with col3:
    mortgage_rate = get_latest_value('MORTGAGE30US')
    mortgage_change = calculate_percentage_change('MORTGAGE30US', periods=12)
    st.metric(
        "30-Year Mortgage Rate",
        f"{mortgage_rate:.2f}%" if mortgage_rate is not None else "N/A",
        f"{mortgage_change:+.2f}pp" if mortgage_change is not None else "N/A"
    )

with col4:
    new_home_sales = get_latest_value('HSN1F')
    sales_yoy = calculate_yoy_change('HSN1F')
    st.metric(
        "New Home Sales",
        f"{new_home_sales:.0f}K" if new_home_sales is not None else "N/A",
        f"{sales_yoy:+.1f}% YoY" if sales_yoy is not None else "N/A"
    )

# === CONSUMER SPENDING TRENDS ===
st.header("📈 Consumer Spending Trends")

col1, col2 = st.columns(2)

with col1:
    pce_data = load_fred_data({'PCE': 'PCE'})
    if pce_data is not None and not pce_data.empty:
        fig = px.line(
            pce_data,
            x=pce_data.index,
            y='PCE',
            title='Personal Consumption Expenditures (10-Year History)',
            labels={'PCE': 'Billions of Dollars', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("PCE data not available")

with col2:
    savings_data = load_fred_data({'PSAVERT': 'PSAVERT'})
    if savings_data is not None and not savings_data.empty:
        fig = px.line(
            savings_data,
            x=savings_data.index,
            y='PSAVERT',
            title='Personal Saving Rate (10-Year History)',
            labels={'PSAVERT': 'Percent', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Savings rate data not available")

# === REAL VS NOMINAL SPENDING ===
st.header("💵 Real vs Nominal Consumer Spending")

col1, col2 = st.columns(2)

with col1:
    real_pce_data = load_fred_data({'PCEC96': 'PCEC96'})
    if real_pce_data is not None and not real_pce_data.empty:
        fig = px.line(
            real_pce_data,
            x=real_pce_data.index,
            y='PCEC96',
            title='Real Personal Consumption (Chained 2017 Dollars)',
            labels={'PCEC96': 'Billions of Chained 2017 Dollars', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Real PCE data not available")

with col2:
    retail_data = load_fred_data({'RSXFS': 'RSXFS'})
    if retail_data is not None and not retail_data.empty:
        fig = px.line(
            retail_data,
            x=retail_data.index,
            y='RSXFS',
            title='Retail Sales ex Food Services (10-Year History)',
            labels={'RSXFS': 'Millions of Dollars', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Retail sales data not available")

# === HOUSING MARKET TRENDS ===
st.header("🏡 Housing Market Activity")

col1, col2 = st.columns(2)

with col1:
    starts_data = load_fred_data({'HOUST': 'HOUST'})
    if starts_data is not None and not starts_data.empty:
        fig = px.line(
            starts_data,
            x=starts_data.index,
            y='HOUST',
            title='Housing Starts (10-Year History)',
            labels={'HOUST': 'Thousands of Units', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Housing starts data not available")

with col2:
    prices_data = load_fred_data({'CSUSHPISA': 'CSUSHPISA'})
    if prices_data is not None and not prices_data.empty:
        fig = px.line(
            prices_data,
            x=prices_data.index,
            y='CSUSHPISA',
            title='S&P/Case-Shiller Home Price Index (10-Year History)',
            labels={'CSUSHPISA': 'Index (Jan 2000 = 100)', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Home price data not available")

# === MORTGAGE RATES & AFFORDABILITY ===
st.header("🏦 Mortgage Rates & Housing Affordability")

col1, col2 = st.columns(2)

with col1:
    mortgage_data = load_fred_data({'MORTGAGE30US': 'MORTGAGE30US'})
    if mortgage_data is not None and not mortgage_data.empty:
        fig = px.line(
            mortgage_data,
            x=mortgage_data.index,
            y='MORTGAGE30US',
            title='30-Year Fixed Mortgage Rate (10-Year History)',
            labels={'MORTGAGE30US': 'Percent', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Mortgage rate data not available")

with col2:
    sales_data = load_fred_data({'HSN1F': 'HSN1F'})
    if sales_data is not None and not sales_data.empty:
        fig = px.line(
            sales_data,
            x=sales_data.index,
            y='HSN1F',
            title='New Single-Family Home Sales (10-Year History)',
            labels={'HSN1F': 'Thousands of Units', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("New home sales data not available")

# === FOOTER ===
st.markdown("---")
st.markdown("""
**Consumer Spending Series:**
- **PCE**: Personal Consumption Expenditures (Nominal)
- **PCEC96**: Real Personal Consumption Expenditures (Chained 2017 Dollars)
- **PSAVERT**: Personal Saving Rate (% of Disposable Income)
- **RSXFS**: Retail Sales Excluding Food Services

**Housing Market Series:**
- **HOUST**: Housing Starts (New Private Housing Units)
- **CSUSHPISA**: S&P/Case-Shiller U.S. National Home Price Index (Seasonally Adjusted)
- **MORTGAGE30US**: 30-Year Fixed Rate Mortgage Average
- **HSN1F**: New Single-Family Home Sales

*Data Source: Federal Reserve Economic Data (FRED)*
""")
