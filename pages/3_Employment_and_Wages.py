import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.data_loader import load_fred_data, get_latest_value, calculate_percentage_change, calculate_yoy_change

st.set_page_config(page_title="Employment & Wages", page_icon="💼", layout="wide")

st.title("💼 Employment & Wages Analysis")
st.markdown("Comprehensive analysis of US labor market conditions, employment trends, and wage growth")

# === HEADLINE METRICS ===
st.header("📊 Key Employment Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    unemployment_rate = get_latest_value('UNRATE')
    unemployment_change = calculate_percentage_change('UNRATE', periods=12)
    st.metric(
        "Unemployment Rate",
        f"{unemployment_rate:.1f}%",
        f"{unemployment_change:+.1f}pp" if unemployment_change is not None else "N/A",
        delta_color="inverse"
    )

with col2:
    payrolls = get_latest_value('PAYEMS')
    payrolls_change = calculate_percentage_change('PAYEMS', periods=12)
    st.metric(
        "Total Nonfarm Payrolls",
        f"{payrolls/1000:.1f}M" if payrolls is not None else "N/A",
        f"{payrolls_change:+.1f}%" if payrolls_change is not None else "N/A"
    )

with col3:
    participation = get_latest_value('CIVPART')
    participation_change = calculate_percentage_change('CIVPART', periods=12)
    st.metric(
        "Labor Force Participation",
        f"{participation:.1f}%" if participation is not None else "N/A",
        f"{participation_change:+.1f}pp" if participation_change is not None else "N/A"
    )

with col4:
    emp_ratio = get_latest_value('EMRATIO')
    emp_ratio_change = calculate_percentage_change('EMRATIO', periods=12)
    st.metric(
        "Employment-Population Ratio",
        f"{emp_ratio:.1f}%" if emp_ratio is not None else "N/A",
        f"{emp_ratio_change:+.1f}pp" if emp_ratio_change is not None else "N/A"
    )

# === WAGE METRICS ===
st.header("💰 Wage & Earnings Trends")

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_earnings = get_latest_value('CES0500000003')
    earnings_yoy = calculate_yoy_change('CES0500000003')
    st.metric(
        "Avg Hourly Earnings (Private)",
        f"${avg_earnings:.2f}" if avg_earnings is not None else "N/A",
        f"{earnings_yoy:+.1f}% YoY" if earnings_yoy is not None else "N/A"
    )

with col2:
    real_earnings = get_latest_value('AHETPI')
    real_earnings_yoy = calculate_yoy_change('AHETPI')
    st.metric(
        "Real Avg Hourly Earnings",
        f"${real_earnings:.2f}" if real_earnings is not None else "N/A",
        f"{real_earnings_yoy:+.1f}% YoY" if real_earnings_yoy is not None else "N/A"
    )

with col3:
    claims = get_latest_value('ICSA')
    claims_change = calculate_percentage_change('ICSA', periods=4)
    st.metric(
        "Initial Jobless Claims",
        f"{claims/1000:.0f}K" if claims is not None else "N/A",
        f"{claims_change:+.1f}%" if claims_change is not None else "N/A",
        delta_color="inverse"
    )

with col4:
    continued_claims = get_latest_value('CCSA')
    continued_change = calculate_percentage_change('CCSA', periods=4)
    st.metric(
        "Continued Jobless Claims",
        f"{continued_claims/1000:.0f}K" if continued_claims is not None else "N/A",
        f"{continued_change:+.1f}%" if continued_change is not None else "N/A",
        delta_color="inverse"
    )

# === UNEMPLOYMENT TRENDS ===
st.header("📈 Unemployment Rate Trends")


unemployment_data = load_fred_data({'UNRATE': 'UNRATE'})
if unemployment_data is not None and not unemployment_data.empty:
    # Create figure with secondary y-axis for additional context
    fig = go.Figure()
    
    # Add unemployment rate line
    fig.add_trace(go.Scatter(
        x=unemployment_data.index,
        y=unemployment_data['UNRATE'],
        name='Unemployment Rate',
        line=dict(color='#FF6B6B', width=2),
        mode='lines'
    ))
    
    # Add 6-month moving average
    if len(unemployment_data) >= 6:
        ma6 = unemployment_data['UNRATE'].rolling(window=6).mean()
        fig.add_trace(go.Scatter(
            x=unemployment_data.index,
            y=ma6,
            name='6-Month MA',
            line=dict(color='#4ECDC4', width=2, dash='dash'),
            mode='lines'
        ))
    
    fig.update_layout(
        title='Unemployment Rate (Monthly) - Full History',
        xaxis_title='Date',
        yaxis_title='Unemployment Rate (%)',
        template='plotly_dark',
        hovermode='x unified',
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Unemployment rate data not available")

# === EMPLOYMENT GROWTH ===
st.header("📊 Payroll Employment Growth")

col1, col2 = st.columns(2)

with col1:

    payrolls_data = load_fred_data({'PAYEMS': 'PAYEMS'})
    if payrolls_data is not None and not payrolls_data.empty:
        fig = px.line(
            payrolls_data,
            x=payrolls_data.index,
            y='PAYEMS',
            title='Total Nonfarm Payrolls (Full History)',
            labels={'PAYEMS': 'Thousands of Employees', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Payrolls data not available")

with col2:

    participation_data = load_fred_data({'CIVPART': 'CIVPART'})
    if participation_data is not None and not participation_data.empty:
        fig = px.line(
            participation_data,
            x=participation_data.index,
            y='CIVPART',
            title='Labor Force Participation Rate (Full History)',
            labels={'CIVPART': 'Participation Rate (%)', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Participation rate data not available")

# === WAGE GROWTH ANALYSIS ===
st.header("💵 Real vs Nominal Wage Growth")

col1, col2 = st.columns(2)

with col1:

    nominal_earnings_data = load_fred_data({'CES0500000003': 'CES0500000003'})
    if nominal_earnings_data is not None and not nominal_earnings_data.empty:
        fig = px.line(
            nominal_earnings_data,
            x=nominal_earnings_data.index,
            y='CES0500000003',
            title='Average Hourly Earnings - Nominal (Full History)',
            labels={'CES0500000003': 'Dollars per Hour', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nominal earnings data not available")

with col2:

    real_earnings_data = load_fred_data({'AHETPI': 'AHETPI'})
    if real_earnings_data is not None and not real_earnings_data.empty:
        fig = px.line(
            real_earnings_data,
            x=real_earnings_data.index,
            y='AHETPI',
            title='Average Hourly Earnings - Real (Full History)',
            labels={'AHETPI': '1982-84 Dollars per Hour', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Real earnings data not available")

# === JOBLESS CLAIMS TRACKING ===
st.header("📉 Jobless Claims Trends")

col1, col2 = st.columns(2)

with col1:

    claims_data = load_fred_data({'ICSA': 'ICSA'})
    if claims_data is not None and not claims_data.empty:
        fig = px.line(
            claims_data,
            x=claims_data.index,
            y='ICSA',
            title='Initial Jobless Claims (Full History)',
            labels={'ICSA': 'Thousands of Claims', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Initial claims data not available")

with col2:

    continued_claims_data = load_fred_data({'CCSA': 'CCSA'})
    if continued_claims_data is not None and not continued_claims_data.empty:
        fig = px.line(
            continued_claims_data,
            x=continued_claims_data.index,
            y='CCSA',
            title='Continued Jobless Claims (Full History)',
            labels={'CCSA': 'Thousands of Claims', 'DATE': 'Date'}
        )
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Continued claims data not available")

# === FOOTER ===
st.markdown("---")
st.markdown("""
**Data Series Tracked:**
- **UNRATE**: Unemployment Rate
- **PAYEMS**: Total Nonfarm Payrolls
- **CIVPART**: Labor Force Participation Rate
- **EMRATIO**: Employment-Population Ratio
- **CES0500000003**: Average Hourly Earnings (Private Sector)
- **AHETPI**: Real Average Hourly Earnings (Production & Nonsupervisory)
- **ICSA**: Initial Jobless Claims (Weekly)
- **CCSA**: Continued Jobless Claims (Insured Unemployment)

*Data Source: Federal Reserve Economic Data (FRED)*
""")
