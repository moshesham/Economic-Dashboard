# News & Sentiment Analysis Feature

This document describes the News & Sentiment Analysis feature of the Economic Dashboard.

## Overview

The News & Sentiment Analysis feature provides:
- Automated news fetching for stock symbols
- Sentiment analysis using NLP (TextBlob)
- Google Trends data integration
- GitHub Actions webhook for automated data refresh

## Components

### 1. News Data Fetcher (`modules/news_data.py`)

Fetches news articles from various sources:
- Supports NewsAPI with API key configuration
- Falls back to sample data for demonstration
- Includes caching for performance
- Google Trends data fetching

**Key Functions:**
- `fetch_news_for_stock(symbol, company_name, days_back, max_articles)` - Fetch news for a stock
- `fetch_google_trends_data(keywords, timeframe, geo)` - Fetch Google Trends data
- `get_market_sentiment_indicators(symbols, include_trends)` - Get aggregated sentiment indicators

### 2. Sentiment Analysis (`modules/sentiment_analysis.py`)

Analyzes text sentiment using TextBlob or keyword-based fallback:

**Key Functions:**
- `analyze_text_sentiment(text)` - Analyze a single text string
- `analyze_news_sentiment(news_df)` - Batch analyze news articles
- `get_aggregated_sentiment(news_df)` - Get aggregated metrics
- `get_sentiment_summary(symbol, news_df)` - Get comprehensive summary

### 3. Streamlit Dashboard (`pages/9_News_Sentiment.py`)

Interactive dashboard for analyzing stock sentiment:
- Stock symbol input
- Sentiment gauge visualization
- Distribution charts
- Trend analysis
- News article table
- Recommendation summary

### 4. GitHub Webhook Workflow (`.github/workflows/news-sentiment-refresh.yml`)

Automated sentiment data refresh:
- Scheduled runs (4 times daily on weekdays)
- Manual trigger support
- Webhook trigger via `repository_dispatch`
- Commits updated data to repository

## Usage

### Manual Analysis via Dashboard

1. Navigate to the "News Sentiment" page in the dashboard
2. Enter a stock symbol (e.g., AAPL, MSFT, GOOGL)
3. Optionally enter the company name for better search results
4. Adjust the number of days to analyze
5. Click "Analyze Sentiment"

### Triggering Webhook

You can trigger the sentiment analysis workflow via the GitHub API:

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/moshesham/Economic-Dashboard/dispatches \
  -d '{"event_type": "analyze-sentiment", "client_payload": {"symbols": "AAPL,MSFT,GOOGL", "days_back": 7}}'
```

### Command Line Script

Run sentiment analysis manually:

```bash
python scripts/fetch_sentiment_data.py \
  --symbols "AAPL,MSFT,GOOGL" \
  --days-back 7 \
  --output-dir "data/sentiment"
```

## Configuration

### Environment Variables

- `NEWS_API_KEY` - Optional API key for NewsAPI.org premium access
- `ECONOMIC_DASHBOARD_OFFLINE` - Set to "true" to use sample data only

### GitHub Secrets

For the webhook workflow to function optimally:
- `NEWS_API_KEY` (optional) - For premium news access

## Data Schema

### Sentiment Summary Table (`sentiment_summary`)

| Column | Type | Description |
|--------|------|-------------|
| ticker | VARCHAR | Stock symbol |
| analysis_date | DATE | Date of analysis |
| article_count | INTEGER | Number of articles analyzed |
| avg_sentiment | DOUBLE | Average sentiment score (-1 to 1) |
| sentiment_trend | VARCHAR | Overall trend (bullish/bearish/neutral) |
| momentum | DOUBLE | Sentiment change over time |
| confidence | DOUBLE | Analysis confidence score |
| recommendation | VARCHAR | Trading recommendation |

### News Sentiment Table (`news_sentiment`)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| ticker | VARCHAR | Stock symbol |
| title | VARCHAR | Article title |
| description | VARCHAR | Article description |
| source | VARCHAR | News source |
| published_at | TIMESTAMP | Publication date |
| sentiment_score | DOUBLE | Sentiment score |
| sentiment_label | VARCHAR | positive/negative/neutral |

## Output Files

The workflow generates:
- `sentiment_summary_latest.csv` - Latest summary for all analyzed symbols
- `sentiment_summary_latest.json` - JSON format summary
- `news_analyzed_latest.csv` - Analyzed news articles
- `trends_*.csv` - Google Trends data per symbol

## Testing

Run sentiment analysis tests:

```bash
python -m pytest tests/test_sentiment_analysis.py -v
```

## Limitations

1. **Sample Data Mode**: Without API keys, the system uses sample/generated data for demonstration
2. **Rate Limiting**: News and trends APIs have rate limits
3. **Sentiment Accuracy**: NLP sentiment analysis has inherent limitations
4. **Historical Data**: Limited to recent news articles

## Future Enhancements

- Integration with additional news sources (Bloomberg, Reuters API)
- Real-time Google Trends API integration
- Advanced NLP models (BERT, FinBERT)
- Correlation with stock price movements
- Alert system for significant sentiment changes
