"""
Financial Markets Deep Dive
Interactive analysis of financial markets, yield curves, and volatility.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.data_loader import load_yfinance_data, get_yield_curve_data

# Page configuration
st.set_page_config(
    page_title="Financial Markets Deep Dive",
    page_icon="💹",
    layout="wide"
)

st.title("💹 Financial Markets Deep Dive")
st.markdown("### Comprehensive analysis of global financial markets")

# Create tabs for different market analyses
tab1, tab2, tab3 = st.tabs(["📈 Market Indices", "📊 Yield Curve", "⚡ Volatility"])

# Tab 1: Market Indices
with tab1:
    st.header("Global Market Indices Performance")
    
    # Available indices
    available_indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "FTSE 100": "^FTSE",
        "Nikkei 225": "^N225",
        "DAX": "^GDAXI",
        "Hang Seng": "^HSI"
    }
    
    # Index selection
    selected_indices = st.multiselect(
        "Select market indices to compare",
        list(available_indices.keys()),
        default=["S&P 500", "NASDAQ", "FTSE 100"]
    )
    
    # Time period selection
    col1, col2 = st.columns([3, 1])
    with col1:
        period_options = {
            "1 Month": "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year": "1y",
            "2 Years": "2y",
            "5 Years": "5y"
        }
        selected_period_label = st.select_slider(
            "Select time period",
            options=list(period_options.keys()),
            value="1 Year"
        )
        selected_period = period_options[selected_period_label]
    
    if selected_indices:
        try:
            with st.spinner("Loading market data..."):
                # Prepare ticker dictionary
                tickers_to_fetch = {name: available_indices[name] for name in selected_indices}
                
                # Load data
                market_data = load_yfinance_data(tickers_to_fetch, period=selected_period)
                
                if market_data:
                    # Normalize data to show percentage change
                    normalized_data = pd.DataFrame()
                    
                    for name, df in market_data.items():
                        if not df.empty and 'Close' in df.columns:
                            base_value = df['Close'].iloc[0]
                            normalized_data[name] = ((df['Close'] / base_value) - 1) * 100
                    
                    if not normalized_data.empty:
                        # Create line chart
                        fig = px.line(
                            normalized_data,
                            x=normalized_data.index,
                            y=normalized_data.columns.tolist(),
                            title=f"Normalized Performance - {selected_period_label}",
                            labels={'value': 'Change (%)', 'variable': 'Index', 'index': 'Date'},
                            template='plotly_dark'
                        )
                        
                        fig.update_layout(
                            height=500,
                            hovermode='x unified',
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            )
                        )
                        
                        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Summary metrics
                        st.divider()
                        st.subheader("📊 Performance Summary")
                        
                        cols = st.columns(len(selected_indices))
                        for i, (name, df) in enumerate(market_data.items()):

                            import streamlit as st
                            import pandas as pd
                            import plotly.express as px
                            import plotly.graph_objects as go
                            from modules.data_loader import load_fred_data, get_latest_value, calculate_percentage_change, calculate_yoy_change

                            st.set_page_config(page_title="Inflation & Prices", page_icon="💹", layout="wide")

                    
                    st.plotly_chart(fig_gauge, use_container_width=True)

    # === INFLATION METRICS ===

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cpi = get_latest_value('CPIAUCSL')
        cpi_yoy = calculate_yoy_change('CPIAUCSL')
        st.metric(
            "CPI (All Urban Consumers)",
            f"{cpi:.1f}" if cpi is not None else "N/A",
            f"{cpi_yoy:+.1f}% YoY" if cpi_yoy is not None else "N/A"
        )

    with col2:
        core_cpi = get_latest_value('CPILFESL')
        core_cpi_yoy = calculate_yoy_change('CPILFESL')
        st.metric(
            "Core CPI (ex Food & Energy)",
            f"{core_cpi:.1f}" if core_cpi is not None else "N/A",
            f"{core_cpi_yoy:+.1f}% YoY" if core_cpi_yoy is not None else "N/A"
        )

    with col3:
        pcepi = get_latest_value('PCEPI')
        pcepi_yoy = calculate_yoy_change('PCEPI')
        st.metric(
            "PCE Price Index",
            f"{pcepi:.1f}" if pcepi is not None else "N/A",
            f"{pcepi_yoy:+.1f}% YoY" if pcepi_yoy is not None else "N/A"
        )

    with col4:
                                core_pce = get_latest_value('PCEPILFE')
                                core_pce_yoy = calculate_yoy_change('PCEPILFE')
                                st.metric(
                                    "Core PCE Price Index",
                                    f"{core_pce:.1f}" if core_pce is not None else "N/A",
                                    f"{core_pce_yoy:+.1f}% YoY" if core_pce_yoy is not None else "N/A"
                                )

                            # === PRODUCER PRICES & EXPECTATIONS ===
                # Statistics

                            col1, col2, col3, col4 = st.columns(4)

                            with col1:
                                ppi = get_latest_value('PPIFGS')
                                ppi_yoy = calculate_yoy_change('PPIFGS')
                                st.metric(
                                    "Producer Price Index (Final Goods)",
                                    f"{ppi:.1f}" if ppi is not None else "N/A",
                                    f"{ppi_yoy:+.1f}% YoY" if ppi_yoy is not None else "N/A"
                                )

                            with col2:
                                import_prices = get_latest_value('IR')
                                import_yoy = calculate_yoy_change('IR')
                                st.metric(
                                    "Import Price Index",
                                    f"{import_prices:.1f}" if import_prices is not None else "N/A",
                                    f"{import_yoy:+.1f}% YoY" if import_yoy is not None else "N/A"
                                )

                            with col3:
                                inflation_expect = get_latest_value('T5YIE')
                                st.metric(
                                    "5-Year Breakeven Inflation",
                                    f"{inflation_expect:.2f}%" if inflation_expect is not None else "N/A"
                                )

                            with col4:
                                food_cpi = get_latest_value('CPIUFDSL')
                                food_cpi_yoy = calculate_yoy_change('CPIUFDSL')
                                st.metric(
                                    "CPI: Food",
                                    f"{food_cpi:.1f}" if food_cpi is not None else "N/A",
                                    f"{food_cpi_yoy:+.1f}% YoY" if food_cpi_yoy is not None else "N/A"
                                )

                            # === INFLATION TRENDS ===
                st.divider()

                            col1, col2 = st.columns(2)

                            with col1:
                                cpi_data = load_fred_data({'CPIAUCSL': 'CPIAUCSL'})
                                if cpi_data is not None and not cpi_data.empty:
                                    fig = px.line(
                                        cpi_data,
                                        x=cpi_data.index,
                                        y='CPIAUCSL',
                                        title='CPI (All Urban Consumers, 10-Year History)',
                                        labels={'CPIAUCSL': 'Index 1982-84=100', 'DATE': 'Date'}
                                    )
                                    fig.update_layout(
                                        template='plotly_dark',
                                        hovermode='x unified',
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("CPI data not available")

                            with col2:
                                core_cpi_data = load_fred_data({'CPILFESL': 'CPILFESL'})
                                if core_cpi_data is not None and not core_cpi_data.empty:
                                    fig = px.line(
                                        core_cpi_data,
                                        x=core_cpi_data.index,
                                        y='CPILFESL',
                                        title='Core CPI (ex Food & Energy, 10-Year History)',
                                        labels={'CPILFESL': 'Index 1982-84=100', 'DATE': 'Date'}
                                    )
                                    fig.update_layout(
                                        template='plotly_dark',
                                        hovermode='x unified',
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("Core CPI data not available")

                            # === PCE & PRODUCER PRICES ===
                col1, col2, col3, col4 = st.columns(4)

                            col1, col2 = st.columns(2)

                            with col1:
                                pcepi_data = load_fred_data({'PCEPI': 'PCEPI'})
                                if pcepi_data is not None and not pcepi_data.empty:
                                    fig = px.line(
                                        pcepi_data,
                                        x=pcepi_data.index,
                                        y='PCEPI',
                                        title='PCE Price Index (10-Year History)',
                                        labels={'PCEPI': 'Index 2012=100', 'DATE': 'Date'}
                                    )
                                    fig.update_layout(
                                        template='plotly_dark',
                                        hovermode='x unified',
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("PCEPI data not available")

                            with col2:
                                ppi_data = load_fred_data({'PPIFGS': 'PPIFGS'})
                                if ppi_data is not None and not ppi_data.empty:
                                    fig = px.line(
                                        ppi_data,
                                        x=ppi_data.index,
                                        y='PPIFGS',
                                        title='Producer Price Index: Final Goods (10-Year History)',
                                        labels={'PPIFGS': 'Index 1982=100', 'DATE': 'Date'}
                                    )
                                    fig.update_layout(
                                        template='plotly_dark',
                                        hovermode='x unified',
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("PPI data not available")

                            # === INFLATION EXPECTATIONS & IMPORT PRICES ===
                

                            col1, col2 = st.columns(2)

                            with col1:
                                inflation_exp_data = load_fred_data({'T5YIE': 'T5YIE'})
                                if inflation_exp_data is not None and not inflation_exp_data.empty:
                                    fig = px.line(
                                        inflation_exp_data,
                                        x=inflation_exp_data.index,
                                        y='T5YIE',
                                        title='5-Year Breakeven Inflation Rate (10-Year History)',
                                        labels={'T5YIE': 'Percent', 'DATE': 'Date'}
                                    )
                                    fig.update_layout(
                                        template='plotly_dark',
                                        hovermode='x unified',
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("Inflation expectations data not available")

                            with col2:
                                import_data = load_fred_data({'IR': 'IR'})
                                if import_data is not None and not import_data.empty:
                                    fig = px.line(
                                        import_data,
                                        x=import_data.index,
                                        y='IR',
                                        title='Import Price Index (10-Year History)',
                                        labels={'IR': 'Index 2000=100', 'DATE': 'Date'}
                                    )
                                    fig.update_layout(
                                        template='plotly_dark',
                                        hovermode='x unified',
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("Import price data not available")

                            # === FOOTER ===
                with col1:
                    st.metric(
                            **Inflation & Price Series:**
                            - **CPIAUCSL**: Consumer Price Index (All Urban Consumers)
                            - **CPILFESL**: Core CPI (ex Food & Energy)
                            - **PCEPI**: Personal Consumption Expenditures Price Index
                            - **PCEPILFE**: Core PCE Price Index
                            - **PPIFGS**: Producer Price Index: Final Goods
                            - **IR**: Import Price Index
                            - **T5YIE**: 5-Year Breakeven Inflation Rate (Market-Based Expectation)
                            - **CPIUFDSL**: CPI: Food

                            *Data Source: Federal Reserve Economic Data (FRED)*
                            """)
                        label="Current VIX",
                        value=f"{current_vix:.2f}"
                    )
                
                with col2:
                    avg_vix = df_vix['Close'].mean()
                    st.metric(
                        label="Average (3Y)",
                        value=f"{avg_vix:.2f}"
                    )
                
                with col3:
                    max_vix = df_vix['Close'].max()
                    st.metric(
                        label="Maximum (3Y)",
                        value=f"{max_vix:.2f}"
                    )
                
                with col4:
                    min_vix = df_vix['Close'].min()
                    st.metric(
                        label="Minimum (3Y)",
                        value=f"{min_vix:.2f}"
                    )
            else:
                st.warning("VIX data not available")
                
    except Exception as e:
        st.error(f"Error loading VIX data: {str(e)}")

# Sidebar information
with st.sidebar:
    st.header("💹 Markets Overview")
    st.markdown("""
    ### Navigation
    - **Market Indices**: Compare global stock market performance
    - **Yield Curve**: Analyze US Treasury yields and inversions
    - **Volatility**: Monitor market fear gauge (VIX)
    
    ### Data Sources
    - Yahoo Finance (Market data)
    - Federal Reserve (Treasury yields)
    
    ### Key Insights
    - Yield curve inversions often signal recessions
    - VIX > 30 indicates high market stress
    - Compare indices to identify regional trends
    """)
