"""
Sentiment Analysis Module for Economic Dashboard.
Analyzes text sentiment from news articles and other sources.
"""

import logging
from typing import Optional
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import TextBlob, fall back to simple analysis if not available
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available. Using simple sentiment analysis.")


def analyze_text_sentiment(text: str) -> dict:
    """
    Analyze sentiment of a single text string.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with sentiment_score (-1 to 1), sentiment_label, and subjectivity
    """
    if not text or not isinstance(text, str):
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'subjectivity': 0.0
        }
    
    text = text.strip()
    if not text:
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'subjectivity': 0.0
        }
    
    if TEXTBLOB_AVAILABLE:
        return _analyze_with_textblob(text)
    else:
        return _analyze_simple(text)


def _analyze_with_textblob(text: str) -> dict:
    """Analyze sentiment using TextBlob."""
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 to 1
    subjectivity = blob.sentiment.subjectivity  # 0 to 1
    
    if polarity > 0.1:
        label = 'positive'
    elif polarity < -0.1:
        label = 'negative'
    else:
        label = 'neutral'
    
    return {
        'sentiment_score': polarity,
        'sentiment_label': label,
        'subjectivity': subjectivity
    }


def _analyze_simple(text: str) -> dict:
    """Simple keyword-based sentiment analysis as fallback."""
    text_lower = text.lower()
    
    positive_words = [
        'gain', 'gains', 'rise', 'rises', 'rising', 'growth', 'growing', 'grew',
        'profit', 'profits', 'profitable', 'positive', 'success', 'successful',
        'strong', 'stronger', 'strength', 'beat', 'beats', 'exceed', 'exceeds',
        'exceeded', 'record', 'high', 'higher', 'up', 'increase', 'increased',
        'upgrade', 'upgraded', 'outperform', 'buy', 'bullish', 'rally', 'surge',
        'surges', 'surging', 'optimistic', 'opportunity', 'opportunities',
        'innovative', 'innovation', 'breakthrough', 'expand', 'expansion'
    ]
    
    negative_words = [
        'loss', 'losses', 'fall', 'falls', 'falling', 'decline', 'declining',
        'declined', 'drop', 'drops', 'dropping', 'dropped', 'negative', 'weak',
        'weaker', 'weakness', 'miss', 'missed', 'misses', 'below', 'down',
        'decrease', 'decreased', 'downgrade', 'downgraded', 'underperform',
        'sell', 'bearish', 'crash', 'plunge', 'plunges', 'plunging', 'slump',
        'pessimistic', 'risk', 'risks', 'risky', 'concern', 'concerns',
        'worried', 'worry', 'trouble', 'troubled', 'problem', 'problems',
        'crisis', 'fail', 'failed', 'failure', 'lawsuit', 'investigation'
    ]
    
    # Count sentiment words
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total = positive_count + negative_count
    if total == 0:
        score = 0.0
        label = 'neutral'
    else:
        score = (positive_count - negative_count) / total
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
    
    return {
        'sentiment_score': score,
        'sentiment_label': label,
        'subjectivity': 0.5  # Default for simple analysis
    }


def analyze_news_sentiment(news_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze sentiment for all articles in a news DataFrame.
    
    Args:
        news_df: DataFrame with 'title' and 'description' columns
        
    Returns:
        Original DataFrame with sentiment columns added
    """
    if news_df.empty:
        return news_df
    
    result_df = news_df.copy()
    
    # Combine title and description for analysis
    texts = []
    for _, row in result_df.iterrows():
        title = str(row.get('title', '')) if pd.notna(row.get('title')) else ''
        desc = str(row.get('description', '')) if pd.notna(row.get('description')) else ''
        texts.append(f"{title} {desc}".strip())
    
    # Analyze each text
    sentiments = [analyze_text_sentiment(text) for text in texts]
    
    result_df['sentiment_score'] = [s['sentiment_score'] for s in sentiments]
    result_df['sentiment_label'] = [s['sentiment_label'] for s in sentiments]
    result_df['subjectivity'] = [s['subjectivity'] for s in sentiments]
    
    return result_df


def get_aggregated_sentiment(news_df: pd.DataFrame) -> dict:
    """
    Get aggregated sentiment metrics from analyzed news.
    
    Args:
        news_df: DataFrame with sentiment columns
        
    Returns:
        Dictionary with aggregated metrics
    """
    if news_df.empty or 'sentiment_score' not in news_df.columns:
        return {
            'avg_sentiment': 0.0,
            'median_sentiment': 0.0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'total_count': 0,
            'sentiment_trend': 'neutral',
            'confidence': 0.0
        }
    
    scores = news_df['sentiment_score'].dropna()
    labels = news_df['sentiment_label'] if 'sentiment_label' in news_df.columns else []
    
    avg_sentiment = scores.mean() if len(scores) > 0 else 0.0
    median_sentiment = scores.median() if len(scores) > 0 else 0.0
    
    positive_count = (labels == 'positive').sum() if len(labels) > 0 else 0
    negative_count = (labels == 'negative').sum() if len(labels) > 0 else 0
    neutral_count = (labels == 'neutral').sum() if len(labels) > 0 else 0
    
    # Determine overall trend
    if avg_sentiment > 0.15:
        sentiment_trend = 'bullish'
    elif avg_sentiment < -0.15:
        sentiment_trend = 'bearish'
    elif avg_sentiment > 0.05:
        sentiment_trend = 'slightly_bullish'
    elif avg_sentiment < -0.05:
        sentiment_trend = 'slightly_bearish'
    else:
        sentiment_trend = 'neutral'
    
    # Calculate confidence based on subjectivity and article count
    subjectivity_avg = news_df['subjectivity'].mean() if 'subjectivity' in news_df.columns else 0.5
    article_factor = min(len(news_df) / 20, 1.0)  # More articles = higher confidence
    confidence = article_factor * (1 - subjectivity_avg * 0.5)
    
    return {
        'avg_sentiment': round(avg_sentiment, 4),
        'median_sentiment': round(median_sentiment, 4),
        'positive_count': int(positive_count),
        'negative_count': int(negative_count),
        'neutral_count': int(neutral_count),
        'total_count': len(news_df),
        'sentiment_trend': sentiment_trend,
        'confidence': round(confidence, 4)
    }


def calculate_sentiment_momentum(
    news_df: pd.DataFrame,
    window_days: int = 3
) -> float:
    """
    Calculate sentiment momentum (change in sentiment over time).
    
    Args:
        news_df: DataFrame with 'published_at' and 'sentiment_score' columns
        window_days: Number of days to compare
        
    Returns:
        Momentum score (positive = improving sentiment)
    """
    if news_df.empty or 'sentiment_score' not in news_df.columns:
        return 0.0
    
    if 'published_at' not in news_df.columns:
        return 0.0
    
    df = news_df.copy()
    df['published_at'] = pd.to_datetime(df['published_at'])
    df = df.sort_values('published_at')
    
    if len(df) < 2:
        return 0.0
    
    # Split into recent and older periods
    midpoint = len(df) // 2
    recent_sentiment = df.iloc[midpoint:]['sentiment_score'].mean()
    older_sentiment = df.iloc[:midpoint]['sentiment_score'].mean()
    
    momentum = recent_sentiment - older_sentiment
    return round(momentum, 4)


def get_sentiment_summary(
    symbol: str,
    news_df: pd.DataFrame
) -> dict:
    """
    Get a comprehensive sentiment summary for a stock.
    
    Args:
        symbol: Stock ticker symbol
        news_df: DataFrame with analyzed news
        
    Returns:
        Comprehensive sentiment summary
    """
    # Ensure sentiment analysis is done
    if 'sentiment_score' not in news_df.columns:
        news_df = analyze_news_sentiment(news_df)
    
    aggregated = get_aggregated_sentiment(news_df)
    momentum = calculate_sentiment_momentum(news_df)
    
    # Generate recommendation based on sentiment
    if aggregated['sentiment_trend'] in ['bullish', 'slightly_bullish'] and momentum > 0:
        recommendation = 'positive_momentum'
    elif aggregated['sentiment_trend'] in ['bearish', 'slightly_bearish'] and momentum < 0:
        recommendation = 'negative_momentum'
    elif aggregated['sentiment_trend'] == 'neutral':
        recommendation = 'wait_and_see'
    else:
        recommendation = 'mixed_signals'
    
    return {
        'symbol': symbol,
        'analyzed_at': pd.Timestamp.now().isoformat(),
        'article_count': aggregated['total_count'],
        'average_sentiment': aggregated['avg_sentiment'],
        'sentiment_trend': aggregated['sentiment_trend'],
        'momentum': momentum,
        'confidence': aggregated['confidence'],
        'recommendation': recommendation,
        'positive_articles': aggregated['positive_count'],
        'negative_articles': aggregated['negative_count'],
        'neutral_articles': aggregated['neutral_count']
    }
