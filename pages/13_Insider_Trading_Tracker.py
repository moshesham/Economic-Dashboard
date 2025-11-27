"""
Insider Trading Tracker Dashboard

Track and analyze SEC Form 4 insider transactions to generate trading signals.
Research shows insider purchases outperform the market by 6-10% annually.

Features:
- Real-time Form 4 transaction tracking
- Insider sentiment scoring
- Unusual activity detection
- Signal backtesting
- Predictive analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional

# Import insider trading tracker
try:
    from modules.features.insider_trading_tracker import InsiderTradingTracker
    TRACKER_AVAILABLE = True
except ImportError as e:
    TRACKER_AVAILABLE = False
    TRACKER_ERROR = str(e)

# Import database functions
try:
    from modules.database import get_db_connection
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Insider Trading Tracker - Economic Dashboard",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Insider Trading Tracker")
st.markdown("""
Track corporate insider transactions from SEC Form 4 filings and generate trading signals.
**Research shows insider purchases outperform the market by 6-10% annually.**
""")

if not TRACKER_AVAILABLE:
    st.error(f"Insider Trading Tracker module not available: {TRACKER_ERROR}")
    st.stop()

st.divider()

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Configuration")
    
    ticker = st.text_input(
        "Enter Ticker Symbol:",
        value="AAPL",
        placeholder="e.g., AAPL, MSFT, GOOGL"
    ).upper().strip()
    
    st.divider()
    
    st.subheader("📊 Analysis Parameters")
    
    lookback_days = st.slider(
        "Transaction History (days):",
        min_value=30,
        max_value=730,
        value=180,
        step=30,
        help="How far back to fetch insider transactions"
    )
    
    sentiment_period = st.slider(
        "Sentiment Period (days):",
        min_value=30,
        max_value=180,
        value=90,
        step=30,
        help="Period for calculating insider sentiment score"
    )
    
    st.divider()
    
    st.subheader("🎯 Backtest Settings")
    
    signal_threshold = st.slider(
        "Signal Threshold:",
        min_value=10.0,
        max_value=50.0,
        value=20.0,
        step=5.0,
        help="Sentiment score threshold for buy signals"
    )
    
    holding_period = st.slider(
        "Holding Period (days):",
        min_value=30,
        max_value=180,
        value=90,
        step=30,
        help="How long to hold after signal"
    )
    
    st.divider()
    
    refresh_data = st.button("🔄 Refresh Data", type="primary")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Transaction Feed",
    "💹 Sentiment Analysis", 
    "⚠️ Unusual Activity",
    "📈 Backtest Results"
])

# Initialize tracker
if not ticker:
    st.info("👈 Enter a ticker symbol in the sidebar to get started")
    st.stop()

tracker = InsiderTradingTracker()

# Load data
with st.spinner(f"Loading insider transactions for {ticker}..."):
    transactions_df = tracker.get_insider_transactions(ticker, days_back=lookback_days)

if transactions_df.empty:
    st.warning(f"No insider transactions found for {ticker} in the last {lookback_days} days")
    st.info("""
    **Possible reasons:**
    - No Form 4 filings in this period
    - SEC API may be rate-limiting requests
    - Ticker symbol may be incorrect
    - Company insiders may not have traded recently
    
    Try:
    - Increasing the lookback period
    - Trying a different ticker (e.g., AAPL, MSFT, GOOGL)
    - Checking back later
    """)
    st.stop()

# ============================================================================
# Tab 1: Transaction Feed
# ============================================================================
with tab1:
    st.subheader("📋 Recent Insider Transactions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_transactions = len(transactions_df)
        st.metric("Total Transactions", f"{total_transactions:,}")
    
    with col2:
        if 'transaction_value' in transactions_df.columns:
            total_value = transactions_df['transaction_value'].sum()
            st.metric("Total Value", f"${total_value:,.0f}")
        else:
            st.metric("Total Value", "N/A")
    
    with col3:
        if 'insider_name' in transactions_df.columns:
            unique_insiders = transactions_df['insider_name'].nunique()
            st.metric("Unique Insiders", unique_insiders)
        else:
            st.metric("Unique Insiders", "N/A")
    
    with col4:
        if 'transaction_date' in transactions_df.columns:
            latest_date = transactions_df['transaction_date'].max()
            st.metric("Latest Transaction", latest_date.strftime('%Y-%m-%d'))
        else:
            st.metric("Latest Transaction", "N/A")
    
    st.divider()
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'transaction_code' in transactions_df.columns:
            trans_codes = st.multiselect(
                "Filter by Transaction Type:",
                options=transactions_df['transaction_code'].unique(),
                default=None
            )
        else:
            trans_codes = []
    
    with col2:
        if 'insider_name' in transactions_df.columns:
            insider_filter = st.multiselect(
                "Filter by Insider:",
                options=sorted(transactions_df['insider_name'].unique()),
                default=None
            )
        else:
            insider_filter = []
    
    with col3:
        min_value = st.number_input(
            "Min Transaction Value:",
            min_value=0,
            value=0,
            step=10000,
            format="%d"
        )
    
    # Apply filters
    filtered_df = transactions_df.copy()
    
    if trans_codes:
        filtered_df = filtered_df[filtered_df['transaction_code'].isin(trans_codes)]
    
    if insider_filter:
        filtered_df = filtered_df[filtered_df['insider_name'].isin(insider_filter)]
    
    if min_value > 0 and 'transaction_value' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['transaction_value'] >= min_value]
    
    st.markdown(f"**Showing {len(filtered_df)} of {len(transactions_df)} transactions**")
    
    # Display transactions table
    if not filtered_df.empty:
        # Prepare display columns
        display_cols = [
            'transaction_date', 'insider_name', 'insider_title', 
            'transaction_type', 'shares', 'price_per_share', 
            'transaction_value', 'shares_owned_after'
        ]
        
        available_cols = [c for c in display_cols if c in filtered_df.columns]
        
        if available_cols:
            display_df = filtered_df[available_cols].copy()
            
            # Format numeric columns
            if 'shares' in display_df.columns:
                display_df['shares'] = display_df['shares'].apply(lambda x: f"{x:,.0f}")
            if 'price_per_share' in display_df.columns:
                display_df['price_per_share'] = display_df['price_per_share'].apply(lambda x: f"${x:,.2f}")
            if 'transaction_value' in display_df.columns:
                display_df['transaction_value'] = display_df['transaction_value'].apply(lambda x: f"${x:,.0f}")
            if 'shares_owned_after' in display_df.columns:
                display_df['shares_owned_after'] = display_df['shares_owned_after'].apply(lambda x: f"{x:,.0f}")
            
            # Rename columns
            display_df.columns = [
                col.replace('_', ' ').title() for col in display_df.columns
            ]
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
        else:
            st.dataframe(filtered_df, use_container_width=True, height=400)
    
    # Visualizations
    st.divider()
    st.subheader("📊 Transaction Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'transaction_type' in filtered_df.columns and not filtered_df.empty:
            # Transaction type distribution
            type_counts = filtered_df['transaction_type'].value_counts()
            
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Transaction Type Distribution",
                hole=0.4
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'transaction_date' in filtered_df.columns and 'transaction_value' in filtered_df.columns:
            # Transaction value over time
            daily_value = filtered_df.groupby('transaction_date')['transaction_value'].sum().reset_index()
            
            fig = px.bar(
                daily_value,
                x='transaction_date',
                y='transaction_value',
                title="Transaction Value Over Time",
                labels={'transaction_date': 'Date', 'transaction_value': 'Total Value ($)'}
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    
    # Top insiders
    if 'insider_name' in filtered_df.columns and 'transaction_value' in filtered_df.columns:
        st.divider()
        st.subheader("👥 Top Insider Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top Buyers (by value)**")
            buy_mask = filtered_df['transaction_code'].isin(tracker.bullish_codes)
            if buy_mask.any():
                top_buyers = tracker.get_top_insider_buyers(filtered_df, days=sentiment_period, top_n=10)
                if not top_buyers.empty:
                    st.dataframe(top_buyers, use_container_width=True)
                else:
                    st.info("No buyer activity in selected period")
            else:
                st.info("No purchases found")
        
        with col2:
            st.markdown("**Top Sellers (by value)**")
            sell_mask = filtered_df['transaction_code'].isin(tracker.bearish_codes)
            if sell_mask.any():
                sellers = filtered_df[sell_mask].groupby(['insider_name', 'insider_title']).agg({
                    'transaction_value': 'sum',
                    'shares': 'sum',
                    'transaction_date': 'max'
                }).reset_index()
                
                sellers = sellers.sort_values('transaction_value', ascending=False).head(10)
                sellers.columns = ['Insider', 'Title', 'Total Value', 'Total Shares', 'Last Transaction']
                
                # Format
                sellers['Total Value'] = sellers['Total Value'].apply(lambda x: f"${x:,.0f}")
                sellers['Total Shares'] = sellers['Total Shares'].apply(lambda x: f"{x:,.0f}")
                
                st.dataframe(sellers, use_container_width=True)
            else:
                st.info("No sales found")

# ============================================================================
# Tab 2: Sentiment Analysis
# ============================================================================
with tab2:
    st.subheader("💹 Insider Sentiment Score")
    
    with st.spinner("Calculating insider sentiment..."):
        sentiment = tracker.calculate_insider_sentiment(transactions_df, days=sentiment_period)
    
    # Display sentiment score
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = sentiment['sentiment_score']
        delta_color = "normal" if score > 0 else "inverse"
        st.metric(
            "Sentiment Score",
            f"{score:.1f}",
            delta=sentiment['signal'],
            delta_color=delta_color
        )
    
    with col2:
        st.metric(
            "Buy Value",
            f"${sentiment['buy_value']:,.0f}",
            delta=f"{sentiment['num_buyers']} buyers"
        )
    
    with col3:
        st.metric(
            "Sell Value",
            f"${sentiment['sell_value']:,.0f}",
            delta=f"{sentiment['num_sellers']} sellers"
        )
    
    with col4:
        st.metric(
            "Confidence",
            sentiment['confidence'],
            delta=f"{sentiment['total_transactions']} transactions"
        )
    
    st.divider()
    
    # Sentiment gauge
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Insider Sentiment ({sentiment_period}-day)", 'font': {'size': 24}},
            delta={'reference': 0, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
            gauge={
                'axis': {'range': [-100, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [-100, -30], 'color': '#ffcccc'},
                    {'range': [-30, -10], 'color': '#ffe6cc'},
                    {'range': [-10, 10], 'color': '#ffffcc'},
                    {'range': [10, 30], 'color': '#ccffcc'},
                    {'range': [30, 100], 'color': '#99ff99'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Signal Interpretation")
        
        if score > 30:
            st.success("**🚀 Strong Buy Signal**")
            st.markdown("Heavy insider buying indicates strong confidence in future performance.")
        elif score > 10:
            st.info("**📈 Buy Signal**")
            st.markdown("Positive insider activity suggests potential upside.")
        elif score < -30:
            st.error("**⚠️ Strong Sell Signal**")
            st.markdown("Heavy insider selling may indicate concerns.")
        elif score < -10:
            st.warning("**📉 Sell Signal**")
            st.markdown("Negative insider sentiment suggests caution.")
        else:
            st.info("**➡️ Neutral**")
            st.markdown("Mixed or minimal insider activity.")
        
        st.divider()
        
        st.markdown("### 📈 Key Metrics")
        st.markdown(f"**Net Value:** ${sentiment['net_value']:,.0f}")
        st.markdown(f"**Buy/Sell Ratio:** {sentiment['buy_value']/(sentiment['sell_value']+1):.2f}x")
        st.markdown(f"**Active Insiders:** {sentiment['num_buyers'] + sentiment['num_sellers']}")
    
    # Breakdown by transaction type
    st.divider()
    st.subheader("🔍 Sentiment Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Buy vs Sell comparison
        comparison_data = pd.DataFrame({
            'Type': ['Buys', 'Sells'],
            'Value': [sentiment['buy_value'], sentiment['sell_value']],
            'Count': [sentiment['num_buyers'], sentiment['num_sellers']]
        })
        
        fig = px.bar(
            comparison_data,
            x='Type',
            y='Value',
            title="Buy vs Sell Value Comparison",
            color='Type',
            color_discrete_map={'Buys': 'green', 'Sells': 'red'},
            text='Value'
        )
        fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Insider count comparison
        fig = px.bar(
            comparison_data,
            x='Type',
            y='Count',
            title="Number of Buyers vs Sellers",
            color='Type',
            color_discrete_map={'Buys': 'green', 'Sells': 'red'},
            text='Count'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# Tab 3: Unusual Activity Detection
# ============================================================================
with tab3:
    st.subheader("⚠️ Unusual Insider Activity Detection")
    
    with st.spinner("Analyzing for unusual patterns..."):
        unusual = tracker.detect_unusual_activity(
            transactions_df,
            lookback_days=sentiment_period,
            baseline_days=lookback_days
        )
    
    # Alert banner
    if unusual['is_unusual']:
        st.error("🚨 **UNUSUAL INSIDER ACTIVITY DETECTED!**")
    else:
        st.success("✅ No unusual insider activity detected")
    
    st.divider()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Volume Ratio",
            f"{unusual['volume_ratio']:.2f}x",
            delta="vs baseline",
            delta_color="off"
        )
    
    with col2:
        st.metric(
            "Value Ratio",
            f"{unusual['value_ratio']:.2f}x",
            delta="vs baseline",
            delta_color="off"
        )
    
    with col3:
        st.metric(
            "Recent Transactions",
            unusual['recent_transactions'],
            delta=f"vs {unusual['baseline_avg_transactions']:.1f} avg"
        )
    
    with col4:
        st.metric(
            "Unique Buyers",
            unusual['unique_buyers'],
            delta="active buyers"
        )
    
    # Alert details
    if unusual['alerts']:
        st.divider()
        st.subheader("🔔 Activity Alerts")
        
        for alert in unusual['alerts']:
            if "🚨" in alert or "📈" in alert:
                st.warning(alert)
            elif "💰" in alert or "💵" in alert:
                st.info(alert)
            else:
                st.info(alert)
    
    # Visualization
    st.divider()
    st.subheader("📊 Activity Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Volume comparison
        volume_data = pd.DataFrame({
            'Period': ['Recent', 'Baseline Average'],
            'Transactions': [unusual['recent_transactions'], unusual['baseline_avg_transactions']]
        })
        
        fig = px.bar(
            volume_data,
            x='Period',
            y='Transactions',
            title="Transaction Volume: Recent vs Baseline",
            color='Period',
            text='Transactions'
        )
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Value comparison
        if 'recent_value' in unusual:
            baseline_value = unusual['recent_value'] / max(unusual['value_ratio'], 0.01)
            
            value_data = pd.DataFrame({
                'Period': ['Recent', 'Baseline Average'],
                'Value': [unusual['recent_value'], baseline_value]
            })
            
            fig = px.bar(
                value_data,
                x='Period',
                y='Value',
                title="Transaction Value: Recent vs Baseline",
                color='Period',
                text='Value'
            )
            fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# Tab 4: Backtest Results
# ============================================================================
with tab4:
    st.subheader("📈 Insider Signal Backtest")
    
    st.markdown(f"""
    **Methodology:**
    - Signal Threshold: {signal_threshold} (sentiment score)
    - Holding Period: {holding_period} days
    - Data Period: Last {lookback_days} days
    """)
    
    with st.spinner(f"Backtesting insider signals for {ticker}..."):
        backtest = tracker.backtest_insider_signals(
            ticker,
            transactions_df,
            signal_threshold=signal_threshold,
            holding_period_days=holding_period
        )
    
    if 'error' in backtest:
        st.error(f"Backtest Error: {backtest['error']}")
        st.stop()
    
    if backtest['total_signals'] == 0:
        st.warning(f"No signals generated with threshold {signal_threshold}. Try lowering the threshold.")
        st.stop()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Signals",
            backtest['total_signals'],
            delta=f"{backtest['valid_trades']} valid trades"
        )
    
    with col2:
        win_rate = backtest['win_rate']
        st.metric(
            "Win Rate",
            f"{win_rate:.1f}%",
            delta="of trades profitable",
            delta_color="normal" if win_rate > 50 else "inverse"
        )
    
    with col3:
        avg_return = backtest['avg_return']
        st.metric(
            "Avg Return",
            f"{avg_return:+.2f}%",
            delta=f"{holding_period}d holding",
            delta_color="normal" if avg_return > 0 else "inverse"
        )
    
    with col4:
        alpha = backtest.get('alpha', 0)
        st.metric(
            "Alpha",
            f"{alpha:+.2f}%",
            delta="annualized vs benchmark",
            delta_color="normal" if alpha > 0 else "inverse"
        )
    
    st.divider()
    
    # Performance comparison
    st.subheader("📊 Performance Comparison")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Returns comparison
        returns_data = pd.DataFrame({
            'Strategy': ['Insider Signals', 'Buy & Hold'],
            'Annualized Return': [
                backtest.get('annualized_signal_return', 0),
                backtest.get('annualized_benchmark', 0)
            ]
        })
        
        fig = px.bar(
            returns_data,
            x='Strategy',
            y='Annualized Return',
            title="Annualized Returns: Insider Signals vs Buy & Hold",
            color='Strategy',
            text='Annualized Return',
            color_discrete_sequence=['#2E86AB', '#A23B72']
        )
        fig.update_traces(texttemplate='%{text:+.2f}%', textposition='outside')
        fig.update_layout(height=350, showlegend=False)
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Return distribution
        return_stats = pd.DataFrame({
            'Metric': ['Best', 'Median', 'Average', 'Worst'],
            'Return': [
                backtest.get('best_return', 0),
                backtest.get('median_return', 0),
                backtest.get('avg_return', 0),
                backtest.get('worst_return', 0)
            ]
        })
        
        fig = px.bar(
            return_stats,
            x='Metric',
            y='Return',
            title=f"Return Distribution ({holding_period}-day holding)",
            color='Return',
            text='Return',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0
        )
        fig.update_traces(texttemplate='%{text:+.2f}%', textposition='outside')
        fig.update_layout(height=350, showlegend=False, coloraxis_showscale=False)
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed stats
    st.divider()
    st.subheader("📋 Detailed Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Signal Performance")
        st.markdown(f"**Valid Trades:** {backtest['valid_trades']}")
        st.markdown(f"**Win Rate:** {backtest['win_rate']:.2f}%")
        st.markdown(f"**Average Return:** {backtest['avg_return']:+.2f}%")
        st.markdown(f"**Median Return:** {backtest.get('median_return', 0):+.2f}%")
        st.markdown(f"**Best Trade:** {backtest.get('best_return', 0):+.2f}%")
        st.markdown(f"**Worst Trade:** {backtest.get('worst_return', 0):+.2f}%")
    
    with col2:
        st.markdown("### Benchmark Comparison")
        st.markdown(f"**Buy & Hold Return:** {backtest.get('benchmark_return', 0):+.2f}%")
        st.markdown(f"**Signal Annualized:** {backtest.get('annualized_signal_return', 0):+.2f}%")
        st.markdown(f"**Benchmark Annualized:** {backtest.get('annualized_benchmark', 0):+.2f}%")
        st.markdown(f"**Alpha:** {backtest.get('alpha', 0):+.2f}%")
        st.markdown(f"**Signal Threshold:** {backtest['signal_threshold']}")
        st.markdown(f"**Holding Period:** {backtest['holding_period_days']} days")
    
    # Interpretation
    st.divider()
    st.subheader("💡 Interpretation")
    
    alpha = backtest.get('alpha', 0)
    win_rate = backtest['win_rate']
    
    if alpha > 5 and win_rate > 60:
        st.success("""
        **🎯 Strong Performance!**
        
        The insider trading signal demonstrates significant alpha over buy-and-hold strategy 
        with high win rate. Consider following insider activity for this ticker.
        """)
    elif alpha > 0 and win_rate > 50:
        st.info("""
        **📈 Positive Results**
        
        Insider signals show modest outperformance vs benchmark. Combining with other 
        indicators may improve results.
        """)
    elif alpha > 0:
        st.warning("""
        **⚠️ Mixed Results**
        
        While generating positive alpha, the win rate suggests inconsistent performance. 
        Use caution and consider additional confirmation.
        """)
    else:
        st.error("""
        **❌ Underperformance**
        
        Insider signals underperformed buy-and-hold for this ticker and timeframe. 
        Results may vary with different parameters or market conditions.
        """)

# Footer
st.divider()
st.markdown("""
---
**Data Source:** SEC EDGAR Form 4 filings  
**Methodology:** Transaction-weighted insider sentiment with position-adjusted weighting  
**Disclaimer:** Past performance does not guarantee future results. This is for informational purposes only.
""")
