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
                            if not df.empty and 'Close' in df.columns:
                                with cols[i]:
                                    latest_price = df['Close'].iloc[-1]
                                    first_price = df['Close'].iloc[0]
                                    pct_change = ((latest_price - first_price) / first_price) * 100
                                    
                                    st.metric(
                                        label=name,
                                        value=f"${latest_price:.2f}",
                                        delta=f"{pct_change:+.2f}%"
                                    )
                    else:
                        st.warning("Could not normalize the data")
                else:
                    st.warning("No data available for selected indices")
        except Exception as e:
            st.error(f"Error loading market indices: {str(e)}")
    else:
        st.info("Please select at least one market index")

# Tab 2: US Treasury Yield Curve
with tab2:
    st.header("US Treasury Yield Curve Analysis")
    
    try:
        with st.spinner("Loading yield curve data..."):
            yield_data = get_yield_curve_data()
            
            if not yield_data.empty:
                # Filter to last 10 years
                ten_years_ago = datetime.now() - timedelta(days=3650)
                yield_data_filtered = yield_data[yield_data.index >= ten_years_ago]
                
                # Chart 1: Historical yields
                st.subheader("Historical Treasury Yields")
                
                fig_yields = go.Figure()
                
                fig_yields.add_trace(go.Scatter(
                    x=yield_data_filtered.index,
                    y=yield_data_filtered['10-Year'],
                    mode='lines',
                    name='10-Year Treasury',
                    line=dict(color='#0068c9', width=2)
                ))
                
                fig_yields.add_trace(go.Scatter(
                    x=yield_data_filtered.index,
                    y=yield_data_filtered['2-Year'],
                    mode='lines',
                    name='2-Year Treasury',
                    line=dict(color='#ff6b6b', width=2)
                ))
                
                fig_yields.update_layout(
                    height=400,
                    hovermode='x unified',
                    yaxis_title='Yield (%)',
                    xaxis_title='Date',
                    template='plotly_dark',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig_yields, use_container_width=True)
                
                # Chart 2: Yield Curve Spread
                st.subheader("Yield Curve Spread (10Y - 2Y)")
                st.markdown("*A negative spread (inversion) often precedes economic recessions*")
                
                fig_spread = go.Figure()
                
                # Separate positive and negative values for coloring
                positive_spread = yield_data_filtered['Spread'].copy()
                positive_spread[positive_spread < 0] = None
                
                negative_spread = yield_data_filtered['Spread'].copy()
                negative_spread[negative_spread >= 0] = None
                
                fig_spread.add_trace(go.Scatter(
                    x=yield_data_filtered.index,
                    y=positive_spread,
                    fill='tozeroy',
                    mode='lines',
                    name='Normal (Positive)',
                    line=dict(color='green', width=0),
                    fillcolor='rgba(0, 255, 0, 0.3)'
                ))
                
                fig_spread.add_trace(go.Scatter(
                    x=yield_data_filtered.index,
                    y=negative_spread,
                    fill='tozeroy',
                    mode='lines',
                    name='Inverted (Negative)',
                    line=dict(color='red', width=0),
                    fillcolor='rgba(255, 0, 0, 0.3)'
                ))
                
                fig_spread.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
                
                fig_spread.update_layout(
                    height=400,
                    hovermode='x unified',
                    yaxis_title='Spread (%)',
                    xaxis_title='Date',
                    template='plotly_dark',
                    showlegend=True
                )
                
                st.plotly_chart(fig_spread, use_container_width=True)
                
                # Current status
                st.divider()
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    latest_10y = yield_data_filtered['10-Year'].iloc[-1]
                    st.metric(
                        label="10-Year Treasury",
                        value=f"{latest_10y:.2f}%"
                    )
                
                with col2:
                    latest_2y = yield_data_filtered['2-Year'].iloc[-1]
                    st.metric(
                        label="2-Year Treasury",
                        value=f"{latest_2y:.2f}%"
                    )
                
                with col3:
                    latest_spread = yield_data_filtered['Spread'].iloc[-1]
                    spread_status = "⚠️ INVERTED" if latest_spread < 0 else "✅ Normal"
                    st.metric(
                        label="Spread",
                        value=f"{latest_spread:.2f}%",
                        delta=spread_status
                    )
            else:
                st.warning("Yield curve data not available")
                
    except Exception as e:
        st.error(f"Error loading yield curve data: {str(e)}")

# Tab 3: Market Volatility
with tab3:
    st.header("Market Volatility Analysis (VIX)")
    st.markdown("*The VIX Index measures market expectations of near-term volatility*")
    
    try:
        with st.spinner("Loading VIX data..."):
            vix_data = load_yfinance_data({"VIX": "^VIX"}, period="3y")
            
            if "VIX" in vix_data and not vix_data["VIX"].empty:
                df_vix = vix_data["VIX"]
                
                # VIX chart
                fig_vix = px.line(
                    df_vix,
                    x=df_vix.index,
                    y='Close',
                    title='VIX Index - Last 3 Years',
                    labels={'Close': 'VIX Level', 'index': 'Date'},
                    template='plotly_dark'
                )
                
                # Add volatility zones
                fig_vix.add_hrect(y0=0, y1=15, fillcolor="green", opacity=0.1, 
                                 annotation_text="Low Volatility", annotation_position="left")
                fig_vix.add_hrect(y0=15, y1=30, fillcolor="yellow", opacity=0.1, 
                                 annotation_text="Medium Volatility", annotation_position="left")
                fig_vix.add_hrect(y0=30, y1=100, fillcolor="red", opacity=0.1, 
                                 annotation_text="High Volatility", annotation_position="left")
                
                fig_vix.update_layout(
                    height=500,
                    hovermode='x unified'
                )
                
                fig_vix.update_traces(line_color='#ff6b6b')
                
                st.plotly_chart(fig_vix, use_container_width=True)
                
                # Current VIX gauge
                st.divider()
                st.subheader("Current VIX Level")
                
                current_vix = df_vix['Close'].iloc[-1]
                
                # Determine volatility level and color
                if current_vix < 15:
                    vix_status = "Low Volatility"
                    vix_color = "green"
                elif current_vix < 30:
                    vix_status = "Medium Volatility"
                    vix_color = "yellow"
                else:
                    vix_status = "High Volatility"
                    vix_color = "red"
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    # Create gauge chart
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=current_vix,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': f"VIX Level: {vix_status}"},
                        delta={'reference': 20},
                        gauge={
                            'axis': {'range': [None, 60]},
                            'bar': {'color': vix_color},
                            'steps': [
                                {'range': [0, 15], 'color': "rgba(0, 255, 0, 0.3)"},
                                {'range': [15, 30], 'color': "rgba(255, 255, 0, 0.3)"},
                                {'range': [30, 60], 'color': "rgba(255, 0, 0, 0.3)"}
                            ],
                            'threshold': {
                                'line': {'color': "white", 'width': 4},
                                'thickness': 0.75,
                                'value': current_vix
                            }
                        }
                    ))
                    
                    fig_gauge.update_layout(
                        height=300,
                        template='plotly_dark'
                    )
                    
                    st.plotly_chart(fig_gauge, use_container_width=True)
                
                # Statistics
                st.divider()
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
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
