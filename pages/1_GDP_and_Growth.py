import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_fred_data, get_latest_value, calculate_percentage_change, calculate_yoy_change

st.set_page_config(page_title="GDP & Growth", page_icon="📊", layout="wide")

st.title("📊 GDP & Economic Growth")
st.markdown("Analysis of US economic growth, GDP components, productivity, and business cycles")

# === GDP METRICS ===
st.header("🇺🇸 GDP & Output Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    gdp = get_latest_value('GDP')
    gdp_yoy = calculate_yoy_change('GDP')
    st.metric(
        "Nominal GDP",
        f"${gdp/1000:.2f}T" if gdp is not None else "N/A",
        f"{gdp_yoy:+.1f}% YoY" if gdp_yoy is not None else "N/A"
    )

with col2:
    real_gdp = get_latest_value('GDPC1')
    real_gdp_yoy = calculate_yoy_change('GDPC1')
    st.metric(
        "Real GDP (Chained 2017 $)",
        f"${real_gdp/1000:.2f}T" if real_gdp is not None else "N/A",
        f"{real_gdp_yoy:+.1f}% YoY" if real_gdp_yoy is not None else "N/A"
    )

with col3:
    gdp_growth = get_latest_value('A191RL1Q225SBEA')
    st.metric(
        "Real GDP Growth (QoQ SAAR)",
        f"{gdp_growth:.1f}%" if gdp_growth is not None else "N/A"
    )

with col4:
    gdp_per_capita = get_latest_value('A939RX0Q048SBEA')
    gdp_per_capita_yoy = calculate_yoy_change('A939RX0Q048SBEA')
    st.metric(
        "Real GDP per Capita",
        f"${gdp_per_capita:,.0f}" if gdp_per_capita is not None else "N/A",
        f"{gdp_per_capita_yoy:+.1f}% YoY" if gdp_per_capita_yoy is not None else "N/A"
    )

# === GDP COMPONENTS ===
st.header("🧩 GDP Components")

col1, col2, col3, col4 = st.columns(4)

with col1:
    consumption = get_latest_value('PCE')
    st.metric(
        "Consumption (PCE)",
        f"${consumption/1000:.2f}T" if consumption is not None else "N/A"
    )

with col2:
    investment = get_latest_value('GPDIC1')
    st.metric(
        "Gross Private Investment",
        f"${investment/1000:.2f}T" if investment is not None else "N/A"
    )

with col3:
    gov_spending = get_latest_value('GCEC1')
    st.metric(
        "Government Consumption & Investment",
        f"${gov_spending/1000:.2f}T" if gov_spending is not None else "N/A"
    )

with col4:
    net_exports = get_latest_value('NETEXP')
    st.metric(
        "Net Exports",
        f"${net_exports/1000:.2f}T" if net_exports is not None else "N/A"
    )

# === GDP GROWTH TRENDS ===
st.header("📈 GDP Growth Trends")

gdp_growth_data = load_fred_data({'A191RL1Q225SBEA': 'A191RL1Q225SBEA'})
if gdp_growth_data is not None and not gdp_growth_data.empty:
    fig = px.line(
        gdp_growth_data,
        x=gdp_growth_data.index,
        y='A191RL1Q225SBEA',
        title='Real GDP Growth Rate (QoQ SAAR)',
        labels={'A191RL1Q225SBEA': 'Percent', 'DATE': 'Date'}
    )
    fig.update_layout(
        template='plotly_dark',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("GDP growth data not available")

# === REAL GDP & PER CAPITA ===
st.header("💵 Real GDP & Per Capita Trends")

col1, col2 = st.columns(2)

with col1:
    real_gdp_data = load_fred_data({'GDPC1': 'GDPC1'})
    if real_gdp_data is not None and not real_gdp_data.empty:
        fig = px.line(
            real_gdp_data,
            x=real_gdp_data.index,
            y='GDPC1',
            title='Real GDP (Chained 2017 Dollars)',
            labels={'GDPC1': 'Billions of Chained 2017 Dollars', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Real GDP data not available")

with col2:
    gdp_per_capita_data = load_fred_data({'A939RX0Q048SBEA': 'A939RX0Q048SBEA'})
    if gdp_per_capita_data is not None and not gdp_per_capita_data.empty:
        fig = px.line(
            gdp_per_capita_data,
            x=gdp_per_capita_data.index,
            y='A939RX0Q048SBEA',
            title='Real GDP per Capita (Chained 2017 Dollars)',
            labels={'A939RX0Q048SBEA': 'Dollars', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("GDP per capita data not available")

# === PRODUCTIVITY & BUSINESS CYCLES ===
st.header("⚙️ Productivity & Business Cycles")

col1, col2 = st.columns(2)

with col1:
    productivity = get_latest_value('OPHNFB')
    productivity_yoy = calculate_yoy_change('OPHNFB')
    st.metric(
        "Nonfarm Business Productivity",
        f"{productivity:.1f}" if productivity is not None else "N/A",
        f"{productivity_yoy:+.1f}% YoY" if productivity_yoy is not None else "N/A"
    )
    prod_data = load_fred_data({'OPHNFB': 'OPHNFB'})
    if prod_data is not None and not prod_data.empty:
        fig = px.line(
            prod_data,
            x=prod_data.index,
            y='OPHNFB',
            title='Nonfarm Business Productivity (10-Year History)',
            labels={'OPHNFB': 'Index 2012=100', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Productivity data not available")

with col2:
    business_investment = get_latest_value('PNFI')
    business_investment_yoy = calculate_yoy_change('PNFI')
    st.metric(
        "Private Nonresidential Fixed Investment",
        f"${business_investment/1000:.2f}T" if business_investment is not None else "N/A",
        f"{business_investment_yoy:+.1f}% YoY" if business_investment_yoy is not None else "N/A"
    )
    invest_data = load_fred_data({'PNFI': 'PNFI'})
    if invest_data is not None and not invest_data.empty:
        fig = px.line(
            invest_data,
            x=invest_data.index,
            y='PNFI',
            title='Private Nonresidential Fixed Investment (10-Year History)',
            labels={'PNFI': 'Billions of Dollars', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Investment data not available")

# === FOOTER ===
st.markdown("---")
st.markdown("""
**GDP & Growth Series:**
- **GDP**: Gross Domestic Product (Nominal, Billions $)
- **GDPC1**: Real GDP (Chained 2017 Dollars)
- **A191RL1Q225SBEA**: Real GDP Growth Rate (QoQ SAAR)
- **A939RX0Q048SBEA**: Real GDP per Capita (Chained 2017 Dollars)
- **PCE**: Personal Consumption Expenditures
- **GPDIC1**: Gross Private Domestic Investment
- **GCEC1**: Government Consumption Expenditures & Investment
- **NETEXP**: Net Exports of Goods & Services
- **OPHNFB**: Nonfarm Business Sector: Labor Productivity (Output per Hour)
- **PNFI**: Private Nonresidential Fixed Investment

*Data Source: Federal Reserve Economic Data (FRED)*
""")
