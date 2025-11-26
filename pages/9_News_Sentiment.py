"""
News & Sentiment Analysis Dashboard
Visualize news sentiment for stocks using data from news sources and Google Trends.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

from modules.news_data import fetch_news_for_stock, fetch_google_trends_data
from modules.sentiment_analysis import (
    analyze_news_sentiment,
    get_sentiment_summary,
    get_aggregated_sentiment
)
from config_settings import is_offline_mode

# Page configuration
st.set_page_config(
    page_title="News & Sentiment Analysis",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and Header
st.title("📰 News & Sentiment Analysis")
st.markdown("### Analyze market sentiment from news articles and trends")

st.divider()

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Analysis Settings")
    
    # Stock symbol input
    symbol = st.text_input(
        "Stock Symbol",
        value="AAPL",
        max_chars=10,
        help="Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
    ).upper()
    
    # Company name (optional)
    company_name = st.text_input(
        "Company Name (optional)",
        value="",
        help="Enter company name for better search results"
    )
    
    # Days to analyze
    days_back = st.slider(
        "Days to Analyze",
        min_value=1,
        max_value=30,
        value=7,
        help="Number of days to look back for news"
    )
    
    # Include trends
    include_trends = st.checkbox(
        "Include Google Trends",
        value=True,
        help="Include Google Trends data in analysis"
    )
    
    # Analyze button
    analyze_button = st.button("🔍 Analyze Sentiment", type="primary", use_container_width=True)
    
    st.divider()
    
    # Mode indicator
    if is_offline_mode():
        st.info("🔌 **Offline Mode**: Using sample data")
    else:
        st.success("🌐 **Online Mode**: Fetching live data")
    
    # Quick symbols
    st.markdown("### 🔥 Quick Access")
    quick_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM']
    cols = st.columns(4)
    for i, sym in enumerate(quick_symbols):
        with cols[i % 4]:
            if st.button(sym, key=f"quick_{sym}"):
                st.session_state['symbol'] = sym


# Main content
def display_sentiment_gauge(score: float, title: str = "Sentiment Score"):
    """Display a sentiment gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [-1, 1], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'steps': [
                {'range': [-1, -0.3], 'color': '#ff6b6b'},
                {'range': [-0.3, 0.3], 'color': '#ffeaa7'},
                {'range': [0.3, 1], 'color': '#55efc4'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig


def display_sentiment_trend(news_df: pd.DataFrame):
    """Display sentiment trend over time."""
    if news_df.empty or 'published_at' not in news_df.columns:
        return None
    
    df = news_df.copy()
    df['published_at'] = pd.to_datetime(df['published_at'])
    df = df.sort_values('published_at')
    
    # Group by date and calculate average sentiment
    daily_sentiment = df.groupby(df['published_at'].dt.date).agg({
        'sentiment_score': 'mean',
        'title': 'count'
    }).reset_index()
    daily_sentiment.columns = ['date', 'avg_sentiment', 'article_count']
    
    fig = px.bar(
        daily_sentiment,
        x='date',
        y='avg_sentiment',
        color='avg_sentiment',
        color_continuous_scale=['red', 'yellow', 'green'],
        range_color=[-1, 1],
        labels={'avg_sentiment': 'Average Sentiment', 'date': 'Date'},
        title='Daily Sentiment Trend'
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        height=300,
        showlegend=False
    )
    
    return fig


def display_sentiment_distribution(news_df: pd.DataFrame):
    """Display distribution of sentiment labels."""
    if news_df.empty or 'sentiment_label' not in news_df.columns:
        return None
    
    distribution = news_df['sentiment_label'].value_counts()
    
    colors = {
        'positive': '#55efc4',
        'neutral': '#ffeaa7',
        'negative': '#ff6b6b'
    }
    
    fig = px.pie(
        values=distribution.values,
        names=distribution.index,
        title='Sentiment Distribution',
        color=distribution.index,
        color_discrete_map=colors
    )
    
    fig.update_layout(height=300)
    
    return fig


def display_news_table(news_df: pd.DataFrame, max_rows: int = 20):
    """Display news articles with sentiment in a table."""
    if news_df.empty:
        st.info("No news articles found")
        return
    
    # Prepare display dataframe
    display_df = news_df.head(max_rows).copy()
    
    if 'sentiment_label' in display_df.columns:
        # Add emoji based on sentiment
        emoji_map = {'positive': '🟢', 'neutral': '🟡', 'negative': '🔴'}
        display_df['Sentiment'] = display_df['sentiment_label'].map(emoji_map)
    
    # Select columns to display
    columns = ['Sentiment', 'title', 'source', 'published_at']
    if 'sentiment_score' in display_df.columns:
        display_df['Score'] = display_df['sentiment_score'].round(3)
        columns.insert(1, 'Score')
    
    display_df = display_df[[c for c in columns if c in display_df.columns]]
    display_df.columns = [c.title().replace('_', ' ') for c in display_df.columns]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# Main analysis logic
if analyze_button or 'analyzed_data' in st.session_state:
    # Update symbol if changed from quick access
    if 'symbol' in st.session_state:
        symbol = st.session_state['symbol']
    
    with st.spinner(f'Analyzing sentiment for {symbol}...'):
        try:
            # Fetch news
            news_df = fetch_news_for_stock(
                symbol=symbol,
                company_name=company_name if company_name else None,
                days_back=days_back
            )
            
            if news_df.empty:
                st.warning(f"No news articles found for {symbol}")
            else:
                # Analyze sentiment
                analyzed_df = analyze_news_sentiment(news_df)
                
                # Get summary
                summary = get_sentiment_summary(symbol, analyzed_df)
                aggregated = get_aggregated_sentiment(analyzed_df)
                
                # Store in session state
                st.session_state['analyzed_data'] = analyzed_df
                st.session_state['summary'] = summary
                
                # Display results
                st.subheader(f"📊 Sentiment Analysis for {symbol}")
                
                # Top metrics row
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Articles Analyzed",
                        summary['article_count'],
                        help="Total number of articles analyzed"
                    )
                
                with col2:
                    sentiment_emoji = "🟢" if summary['average_sentiment'] > 0.1 else "🔴" if summary['average_sentiment'] < -0.1 else "🟡"
                    st.metric(
                        "Average Sentiment",
                        f"{sentiment_emoji} {summary['average_sentiment']:.3f}",
                        help="Average sentiment score (-1 to 1)"
                    )
                
                with col3:
                    st.metric(
                        "Trend",
                        summary['sentiment_trend'].replace('_', ' ').title(),
                        help="Overall sentiment trend"
                    )
                
                with col4:
                    momentum_delta = f"{'+' if summary['momentum'] > 0 else ''}{summary['momentum']:.3f}"
                    st.metric(
                        "Momentum",
                        momentum_delta,
                        delta=momentum_delta,
                        help="Change in sentiment over time"
                    )
                
                st.divider()
                
                # Charts row
                col_left, col_right = st.columns(2)
                
                with col_left:
                    # Sentiment gauge
                    gauge_fig = display_sentiment_gauge(
                        summary['average_sentiment'],
                        f"{symbol} Sentiment"
                    )
                    st.plotly_chart(gauge_fig, use_container_width=True)
                
                with col_right:
                    # Distribution pie chart
                    dist_fig = display_sentiment_distribution(analyzed_df)
                    if dist_fig:
                        st.plotly_chart(dist_fig, use_container_width=True)
                
                # Sentiment trend
                st.subheader("📈 Sentiment Over Time")
                trend_fig = display_sentiment_trend(analyzed_df)
                if trend_fig:
                    st.plotly_chart(trend_fig, use_container_width=True)
                else:
                    st.info("Not enough data to display trend")
                
                # Google Trends
                if include_trends:
                    st.subheader("🔍 Google Trends")
                    trends_df = fetch_google_trends_data([symbol])
                    
                    if not trends_df.empty and symbol in trends_df.columns:
                        fig = px.line(
                            trends_df,
                            x='date',
                            y=symbol,
                            title=f'Search Interest for {symbol}',
                            labels={'date': 'Date', symbol: 'Search Interest'}
                        )
                        fig.update_traces(line_color='#0068c9', line_width=2)
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Trends data not available")
                
                # News articles table
                st.subheader("📰 Recent News Articles")
                display_news_table(analyzed_df)
                
                # Recommendation box
                st.subheader("💡 Analysis Summary")
                
                rec_color = {
                    'positive_momentum': 'green',
                    'negative_momentum': 'red',
                    'wait_and_see': 'orange',
                    'mixed_signals': 'gray'
                }.get(summary['recommendation'], 'gray')
                
                rec_text = {
                    'positive_momentum': 'Positive sentiment with improving momentum. Market appears optimistic.',
                    'negative_momentum': 'Negative sentiment with declining momentum. Market appears pessimistic.',
                    'wait_and_see': 'Neutral sentiment. No clear directional signal from news.',
                    'mixed_signals': 'Mixed sentiment signals. Exercise caution and monitor closely.'
                }.get(summary['recommendation'], 'Unable to determine clear signal.')
                
                st.markdown(f"""
                <div style="padding: 1rem; border-radius: 0.5rem; background-color: rgba(255,255,255,0.05); border-left: 4px solid {rec_color};">
                    <h4 style="margin:0; color: {rec_color};">
                        {summary['recommendation'].replace('_', ' ').title()}
                    </h4>
                    <p style="margin-top: 0.5rem;">{rec_text}</p>
                    <p style="margin-bottom: 0; font-size: 0.8rem; color: gray;">
                        Confidence: {summary['confidence']:.2%} | Based on {summary['article_count']} articles
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error analyzing sentiment: {str(e)}")
            import traceback
            st.text(traceback.format_exc())

else:
    # Show instructions when no analysis has been run
    st.info("""
    👋 **Welcome to the News & Sentiment Analysis Dashboard!**
    
    This tool analyzes news articles and market trends to provide sentiment insights for stocks.
    
    **How to use:**
    1. Enter a stock symbol in the sidebar (e.g., AAPL, MSFT, GOOGL)
    2. Optionally enter the company name for better search results
    3. Adjust the number of days to analyze
    4. Click "Analyze Sentiment" to see results
    
    **What you'll get:**
    - 📊 Overall sentiment score and trend
    - 📈 Sentiment momentum analysis
    - 🔍 Google Trends data
    - 📰 List of analyzed news articles
    - 💡 Analysis summary with recommendation
    """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.8rem;">
    <p>
        Data sources: News APIs, Google Trends | 
        Sentiment analysis powered by TextBlob/NLP |
        <a href="https://github.com/moshesham/Economic-Dashboard" target="_blank">View on GitHub</a>
    </p>
    <p>
        ⚠️ This analysis is for informational purposes only and should not be considered financial advice.
    </p>
</div>
""", unsafe_allow_html=True)
