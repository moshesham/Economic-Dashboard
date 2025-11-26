"""
News Data Fetching Module for Economic Dashboard.
Fetches news articles from various sources for sentiment analysis.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
import requests
import pandas as pd

from config_settings import ensure_cache_dir, get_cache_dir

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting settings
NEWS_RATE_LIMIT_DELAY = 0.5  # Seconds between requests
NEWS_CACHE_HOURS = 1  # Cache news for 1 hour


def _load_cached_news(cache_file: str, max_age_hours: int = NEWS_CACHE_HOURS) -> Optional[pd.DataFrame]:
    """Load cached news data if available and not expired."""
    import pickle
    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)

        cache_time = cache_data.get('timestamp')
        if cache_time and datetime.now() - cache_time > timedelta(hours=max_age_hours):
            return None

        return cache_data.get('data')
    except Exception as e:
        logger.warning(f"Could not load cached news: {e}")
        return None


def _save_cached_news(cache_file: str, data: pd.DataFrame):
    """Save news data to cache."""
    import pickle
    ensure_cache_dir()
    cache_data = {
        'timestamp': datetime.now(),
        'data': data
    }

    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
    except Exception as e:
        logger.warning(f"Could not save news cache: {e}")


def fetch_news_for_stock(
    symbol: str,
    company_name: Optional[str] = None,
    days_back: int = 7,
    max_articles: int = 50,
    api_key: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch news articles for a given stock symbol.
    
    Uses a tiered approach:
    1. Try NewsAPI if API key is provided
    2. Fall back to sample data for demonstration
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        company_name: Full company name for better search (e.g., 'Apple Inc')
        days_back: Number of days to look back for news
        max_articles: Maximum number of articles to fetch
        api_key: Optional API key for premium news services
        
    Returns:
        DataFrame with columns: title, description, source, published_at, url, content
    """
    cache_file = f"{get_cache_dir()}/news_{symbol.lower()}.pkl"
    
    # Check cache first
    cached_data = _load_cached_news(cache_file)
    if cached_data is not None and not cached_data.empty:
        logger.info(f"Using cached news for {symbol}")
        return cached_data
    
    # Build search query
    search_terms = [symbol]
    if company_name:
        search_terms.append(company_name)
    
    articles = []
    
    # Try NewsAPI if key is available
    news_api_key = api_key or os.environ.get('NEWS_API_KEY')
    if news_api_key:
        articles = _fetch_from_newsapi(search_terms, days_back, max_articles, news_api_key)
    
    # If no articles found, use sample data for demonstration
    if not articles:
        logger.info(f"Using sample news data for {symbol}")
        articles = _generate_sample_news(symbol, company_name, days_back, max_articles)
    
    # Convert to DataFrame
    df = pd.DataFrame(articles)
    
    if not df.empty:
        df['published_at'] = pd.to_datetime(df['published_at'])
        df = df.sort_values('published_at', ascending=False)
        _save_cached_news(cache_file, df)
    
    return df


def _fetch_from_newsapi(
    search_terms: list,
    days_back: int,
    max_articles: int,
    api_key: str
) -> list:
    """Fetch news from NewsAPI."""
    articles = []
    from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    for term in search_terms[:2]:  # Limit search terms
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': term,
                'from': from_date,
                'sortBy': 'relevancy',
                'pageSize': min(max_articles // len(search_terms), 100),
                'language': 'en',
                'apiKey': api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                for article in data.get('articles', []):
                    articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'published_at': article.get('publishedAt', ''),
                        'url': article.get('url', ''),
                        'content': article.get('content', '')
                    })
            
            time.sleep(NEWS_RATE_LIMIT_DELAY)
            
        except requests.RequestException as e:
            logger.warning(f"Error fetching news for {term}: {e}")
            continue
    
    return articles


def _generate_sample_news(
    symbol: str,
    company_name: Optional[str],
    days_back: int,
    max_articles: int
) -> list:
    """Generate sample news data for demonstration purposes."""
    import random
    
    company = company_name or symbol
    
    templates = [
        {
            'title': f"{company} Reports Strong Quarterly Earnings",
            'description': f"{company} exceeded analyst expectations with robust revenue growth.",
            'sentiment_hint': 'positive'
        },
        {
            'title': f"{company} Announces New Product Line",
            'description': f"{company} unveiled innovative products expected to drive future growth.",
            'sentiment_hint': 'positive'
        },
        {
            'title': f"Analysts Upgrade {company} Stock Rating",
            'description': f"Major investment banks have raised their price targets for {symbol}.",
            'sentiment_hint': 'positive'
        },
        {
            'title': f"{company} Faces Regulatory Scrutiny",
            'description': f"Regulators are investigating {company}'s business practices.",
            'sentiment_hint': 'negative'
        },
        {
            'title': f"{company} Stock Drops Amid Market Concerns",
            'description': f"{symbol} shares fell following broader market uncertainty.",
            'sentiment_hint': 'negative'
        },
        {
            'title': f"{company} Announces Restructuring Plan",
            'description': f"{company} is implementing cost-cutting measures to improve margins.",
            'sentiment_hint': 'neutral'
        },
        {
            'title': f"Market Watch: {symbol} Trading Volumes Surge",
            'description': f"Trading activity in {symbol} has increased significantly this week.",
            'sentiment_hint': 'neutral'
        },
        {
            'title': f"{company} Expands into New Markets",
            'description': f"{company} announces strategic expansion into emerging markets.",
            'sentiment_hint': 'positive'
        },
        {
            'title': f"{company} CEO Discusses Future Strategy",
            'description': f"Leadership outlines growth plans and strategic priorities.",
            'sentiment_hint': 'neutral'
        },
        {
            'title': f"Industry Report: {company} Leads Sector",
            'description': f"{company} maintains market leadership position in its industry.",
            'sentiment_hint': 'positive'
        }
    ]
    
    sources = ['Reuters', 'Bloomberg', 'CNBC', 'MarketWatch', 'The Wall Street Journal', 
               'Financial Times', 'Yahoo Finance', 'Seeking Alpha', 'Barron\'s']
    
    articles = []
    num_articles = min(max_articles, len(templates) * 2)
    
    for i in range(num_articles):
        template = templates[i % len(templates)]
        days_ago = random.randint(0, days_back)
        hours_ago = random.randint(0, 23)
        
        published_at = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        
        articles.append({
            'title': template['title'],
            'description': template['description'],
            'source': random.choice(sources),
            'published_at': published_at.isoformat(),
            'url': f"https://example.com/news/{symbol.lower()}-{i}",
            'content': template['description'] + f" Full analysis of {company}'s market position and outlook."
        })
    
    return articles


def fetch_google_trends_data(
    keywords: list,
    timeframe: str = 'today 3-m',
    geo: str = 'US'
) -> pd.DataFrame:
    """
    Fetch Google Trends data for given keywords.
    
    Note: This uses a simplified approach. For production use, 
    consider using the pytrends library with proper rate limiting.
    
    Args:
        keywords: List of search terms
        timeframe: Time range (e.g., 'today 3-m', 'today 12-m', 'all')
        geo: Geographic region code
        
    Returns:
        DataFrame with trend data over time
    """
    cache_file = f"{get_cache_dir()}/trends_{'_'.join(keywords[:3])}.pkl"
    
    # Check cache first
    cached_data = _load_cached_news(cache_file, max_age_hours=6)
    if cached_data is not None and not cached_data.empty:
        logger.info(f"Using cached trends data for {keywords}")
        return cached_data
    
    # Generate sample trends data for demonstration
    logger.info(f"Generating sample trends data for {keywords}")
    df = _generate_sample_trends(keywords, timeframe)
    
    if not df.empty:
        _save_cached_news(cache_file, df)
    
    return df


def _generate_sample_trends(keywords: list, timeframe: str) -> pd.DataFrame:
    """Generate sample Google Trends data for demonstration."""
    import numpy as np
    
    # Parse timeframe to determine date range
    if 'today 3-m' in timeframe:
        days = 90
    elif 'today 12-m' in timeframe:
        days = 365
    elif 'today 1-m' in timeframe:
        days = 30
    else:
        days = 90
    
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    data = {'date': dates}
    
    for keyword in keywords[:5]:  # Limit to 5 keywords
        # Generate trend with some randomness and patterns
        base_trend = 50 + np.sin(np.linspace(0, 4 * np.pi, days)) * 20
        noise = np.random.normal(0, 10, days)
        spikes = np.random.choice([0, 30], days, p=[0.95, 0.05])  # Occasional spikes
        
        trend_values = np.clip(base_trend + noise + spikes, 0, 100)
        data[keyword] = trend_values
    
    return pd.DataFrame(data)


def get_market_sentiment_indicators(
    symbols: list,
    include_trends: bool = True
) -> dict:
    """
    Get aggregated sentiment indicators for a list of stocks.
    
    Args:
        symbols: List of stock symbols
        include_trends: Whether to include Google Trends data
        
    Returns:
        Dictionary with sentiment metrics per symbol
    """
    from modules.sentiment_analysis import analyze_news_sentiment
    
    results = {}
    
    for symbol in symbols:
        # Fetch news
        news_df = fetch_news_for_stock(symbol, days_back=7)
        
        if not news_df.empty:
            # Analyze sentiment
            sentiment_df = analyze_news_sentiment(news_df)
            
            results[symbol] = {
                'article_count': len(sentiment_df),
                'avg_sentiment': sentiment_df['sentiment_score'].mean() if 'sentiment_score' in sentiment_df.columns else 0,
                'positive_pct': (sentiment_df['sentiment_label'] == 'positive').mean() * 100 if 'sentiment_label' in sentiment_df.columns else 0,
                'negative_pct': (sentiment_df['sentiment_label'] == 'negative').mean() * 100 if 'sentiment_label' in sentiment_df.columns else 0,
                'neutral_pct': (sentiment_df['sentiment_label'] == 'neutral').mean() * 100 if 'sentiment_label' in sentiment_df.columns else 0,
                'latest_news': sentiment_df.head(5).to_dict('records') if not sentiment_df.empty else []
            }
        else:
            results[symbol] = {
                'article_count': 0,
                'avg_sentiment': 0,
                'positive_pct': 0,
                'negative_pct': 0,
                'neutral_pct': 0,
                'latest_news': []
            }
        
        # Add trends data if requested
        if include_trends:
            trends_df = fetch_google_trends_data([symbol])
            if not trends_df.empty and symbol in trends_df.columns:
                results[symbol]['trend_current'] = trends_df[symbol].iloc[-1]
                results[symbol]['trend_7d_change'] = (
                    (trends_df[symbol].iloc[-1] - trends_df[symbol].iloc[-7]) / trends_df[symbol].iloc[-7] * 100
                    if len(trends_df) >= 7 else 0
                )
    
    return results
