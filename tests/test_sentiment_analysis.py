"""
Unit tests for news_data and sentiment_analysis modules.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestSentimentAnalysis:
    """Test cases for sentiment analysis functions."""
    
    def test_analyze_text_sentiment_positive(self):
        """Test sentiment analysis with positive text."""
        from modules.sentiment_analysis import analyze_text_sentiment
        
        text = "The company reported strong growth and record profits."
        result = analyze_text_sentiment(text)
        
        assert 'sentiment_score' in result
        assert 'sentiment_label' in result
        assert 'subjectivity' in result
        # Positive text should have positive score or label
        assert result['sentiment_score'] >= 0 or result['sentiment_label'] == 'positive'
    
    def test_analyze_text_sentiment_negative(self):
        """Test sentiment analysis with negative text."""
        from modules.sentiment_analysis import analyze_text_sentiment
        
        text = "The stock crashed after major losses and failure of the company with terrible performance and declining sales."
        result = analyze_text_sentiment(text)
        
        assert 'sentiment_score' in result
        assert 'sentiment_label' in result
        # Negative text should have negative score or label
        assert result['sentiment_score'] <= 0.1 or result['sentiment_label'] in ['negative', 'neutral']
    
    def test_analyze_text_sentiment_empty(self):
        """Test sentiment analysis with empty text."""
        from modules.sentiment_analysis import analyze_text_sentiment
        
        result = analyze_text_sentiment("")
        
        assert result['sentiment_score'] == 0.0
        assert result['sentiment_label'] == 'neutral'
    
    def test_analyze_text_sentiment_none(self):
        """Test sentiment analysis with None input."""
        from modules.sentiment_analysis import analyze_text_sentiment
        
        result = analyze_text_sentiment(None)
        
        assert result['sentiment_score'] == 0.0
        assert result['sentiment_label'] == 'neutral'
    
    def test_analyze_news_sentiment(self):
        """Test batch sentiment analysis on news DataFrame."""
        from modules.sentiment_analysis import analyze_news_sentiment
        
        news_df = pd.DataFrame({
            'title': ['Great earnings report!', 'Stock falls on bad news'],
            'description': ['Profits exceed expectations', 'Major losses reported'],
            'source': ['Reuters', 'Bloomberg'],
            'published_at': [datetime.now(), datetime.now() - timedelta(hours=2)]
        })
        
        result = analyze_news_sentiment(news_df)
        
        assert 'sentiment_score' in result.columns
        assert 'sentiment_label' in result.columns
        assert len(result) == 2
    
    def test_analyze_news_sentiment_empty(self):
        """Test sentiment analysis with empty DataFrame."""
        from modules.sentiment_analysis import analyze_news_sentiment
        
        result = analyze_news_sentiment(pd.DataFrame())
        
        assert result.empty
    
    def test_get_aggregated_sentiment(self):
        """Test aggregated sentiment calculation."""
        from modules.sentiment_analysis import get_aggregated_sentiment
        
        news_df = pd.DataFrame({
            'sentiment_score': [0.5, -0.3, 0.1, 0.2],
            'sentiment_label': ['positive', 'negative', 'neutral', 'positive'],
            'subjectivity': [0.6, 0.7, 0.3, 0.5]
        })
        
        result = get_aggregated_sentiment(news_df)
        
        assert 'avg_sentiment' in result
        assert 'positive_count' in result
        assert 'negative_count' in result
        assert 'neutral_count' in result
        assert result['total_count'] == 4
        assert result['positive_count'] == 2
        assert result['negative_count'] == 1
        assert result['neutral_count'] == 1
    
    def test_get_sentiment_summary(self):
        """Test comprehensive sentiment summary."""
        from modules.sentiment_analysis import get_sentiment_summary
        
        news_df = pd.DataFrame({
            'title': ['Good news', 'Bad news', 'Neutral update'],
            'description': ['Positive outlook', 'Negative trend', 'Regular update'],
            'published_at': [
                datetime.now(),
                datetime.now() - timedelta(days=1),
                datetime.now() - timedelta(days=2)
            ]
        })
        
        result = get_sentiment_summary('AAPL', news_df)
        
        assert result['symbol'] == 'AAPL'
        assert 'average_sentiment' in result
        assert 'sentiment_trend' in result
        assert 'momentum' in result
        assert 'recommendation' in result


class TestNewsData:
    """Test cases for news data fetching functions."""
    
    def test_generate_sample_news(self):
        """Test sample news generation."""
        from modules.news_data import _generate_sample_news
        
        articles = _generate_sample_news('AAPL', 'Apple Inc', 7, 10)
        
        assert len(articles) == 10
        assert all('title' in a for a in articles)
        assert all('description' in a for a in articles)
        assert all('source' in a for a in articles)
        assert all('published_at' in a for a in articles)
    
    def test_generate_sample_trends(self):
        """Test sample trends generation."""
        from modules.news_data import _generate_sample_trends
        
        df = _generate_sample_trends(['AAPL', 'MSFT'], 'today 3-m')
        
        assert 'date' in df.columns
        assert 'AAPL' in df.columns
        assert 'MSFT' in df.columns
        assert len(df) == 90  # 3 months
    
    @patch('modules.news_data._load_cached_news', return_value=None)
    def test_fetch_news_for_stock_sample(self, mock_cache):
        """Test fetching news uses sample data when no API key."""
        from modules.news_data import fetch_news_for_stock
        
        # Ensure no API key in environment
        import os
        original_key = os.environ.get('NEWS_API_KEY')
        if 'NEWS_API_KEY' in os.environ:
            del os.environ['NEWS_API_KEY']
        
        try:
            result = fetch_news_for_stock('AAPL', days_back=7)
            
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert 'title' in result.columns
        finally:
            if original_key:
                os.environ['NEWS_API_KEY'] = original_key
    
    @patch('modules.news_data._load_cached_news', return_value=None)
    def test_fetch_google_trends_sample(self, mock_cache):
        """Test fetching Google Trends uses sample data."""
        from modules.news_data import fetch_google_trends_data
        
        result = fetch_google_trends_data(['AAPL'])
        
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'date' in result.columns


class TestIntegration:
    """Integration tests for the sentiment analysis pipeline."""
    
    def test_full_sentiment_pipeline(self):
        """Test the complete sentiment analysis pipeline."""
        from modules.news_data import fetch_news_for_stock
        from modules.sentiment_analysis import analyze_news_sentiment, get_sentiment_summary
        
        # Fetch news (will use sample data)
        news_df = fetch_news_for_stock('MSFT', days_back=7)
        
        assert not news_df.empty
        
        # Analyze sentiment
        analyzed_df = analyze_news_sentiment(news_df)
        
        assert 'sentiment_score' in analyzed_df.columns
        assert 'sentiment_label' in analyzed_df.columns
        
        # Get summary
        summary = get_sentiment_summary('MSFT', analyzed_df)
        
        assert summary['symbol'] == 'MSFT'
        assert summary['article_count'] > 0
        assert 'recommendation' in summary
    
    @patch('modules.news_data._load_cached_news', return_value=None)
    def test_market_sentiment_indicators(self, mock_cache):
        """Test market sentiment indicators for multiple stocks."""
        from modules.news_data import get_market_sentiment_indicators
        
        symbols = ['AAPL', 'MSFT']
        result = get_market_sentiment_indicators(symbols, include_trends=False)
        
        assert 'AAPL' in result
        assert 'MSFT' in result
        assert 'avg_sentiment' in result['AAPL']
        assert 'article_count' in result['MSFT']


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
