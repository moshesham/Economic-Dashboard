#!/usr/bin/env python3
"""
Fetch news and sentiment data for stock symbols.
This script is called by the GitHub Actions workflow.
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.news_data import fetch_news_for_stock, fetch_google_trends_data
from modules.sentiment_analysis import analyze_news_sentiment, get_sentiment_summary


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Fetch news and sentiment data for stock symbols'
    )
    parser.add_argument(
        '--symbols',
        type=str,
        default='AAPL,MSFT,GOOGL',
        help='Comma-separated list of stock symbols'
    )
    parser.add_argument(
        '--days-back',
        type=int,
        default=7,
        help='Number of days to look back for news'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/sentiment',
        help='Directory to save output files'
    )
    parser.add_argument(
        '--include-trends',
        action='store_true',
        default=True,
        help='Include Google Trends data'
    )
    return parser.parse_args()


def main():
    """Main function to fetch and analyze sentiment data."""
    args = parse_args()
    
    print("=" * 60)
    print("News & Sentiment Analysis Pipeline")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    # Parse symbols
    symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
    
    if not symbols:
        print("Error: No valid symbols provided")
        return 1
    
    print(f"Symbols to analyze: {symbols}")
    print(f"Days back: {args.days_back}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    all_summaries = []
    all_news = []
    
    for symbol in symbols:
        print(f"\n{'='*40}")
        print(f"Processing: {symbol}")
        print(f"{'='*40}")
        
        try:
            # Fetch news
            print(f"  Fetching news for {symbol}...", end=' ')
            news_df = fetch_news_for_stock(
                symbol=symbol,
                days_back=args.days_back
            )
            print(f"✓ ({len(news_df)} articles)")
            
            if news_df.empty:
                print(f"  ⚠ No news found for {symbol}")
                continue
            
            # Analyze sentiment
            print(f"  Analyzing sentiment...", end=' ')
            analyzed_df = analyze_news_sentiment(news_df)
            print("✓")
            
            # Get summary
            summary = get_sentiment_summary(symbol, analyzed_df)
            all_summaries.append(summary)
            
            # Add symbol to news dataframe
            analyzed_df['symbol'] = symbol
            all_news.append(analyzed_df)
            
            # Print summary
            print(f"  Results for {symbol}:")
            print(f"    - Average Sentiment: {summary['average_sentiment']:.4f}")
            print(f"    - Trend: {summary['sentiment_trend']}")
            print(f"    - Momentum: {summary['momentum']:.4f}")
            print(f"    - Positive: {summary['positive_articles']}, Negative: {summary['negative_articles']}, Neutral: {summary['neutral_articles']}")
            
            # Fetch trends if requested
            if args.include_trends:
                print(f"  Fetching trends data...", end=' ')
                trends_df = fetch_google_trends_data([symbol])
                if not trends_df.empty:
                    print(f"✓ ({len(trends_df)} data points)")
                    # Save trends data
                    trends_file = os.path.join(args.output_dir, f'trends_{symbol.lower()}.csv')
                    trends_df.to_csv(trends_file, index=False)
                else:
                    print("⚠ No trends data available")
            
        except Exception as e:
            print(f"  ✗ Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Save combined results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if all_summaries:
        # Save summaries
        summaries_df = pd.DataFrame(all_summaries)
        summaries_file = os.path.join(args.output_dir, f'sentiment_summary_{timestamp}.csv')
        summaries_df.to_csv(summaries_file, index=False)
        print(f"\n✓ Saved summaries to: {summaries_file}")
        
        # Save latest summary (overwrite)
        latest_file = os.path.join(args.output_dir, 'sentiment_summary_latest.csv')
        summaries_df.to_csv(latest_file, index=False)
        print(f"✓ Saved latest summary to: {latest_file}")
        
        # Also save as JSON for easy API consumption
        json_file = os.path.join(args.output_dir, 'sentiment_summary_latest.json')
        with open(json_file, 'w') as f:
            json.dump(all_summaries, f, indent=2, default=str)
        print(f"✓ Saved JSON summary to: {json_file}")
    
    if all_news:
        # Combine all news
        combined_news = pd.concat(all_news, ignore_index=True)
        news_file = os.path.join(args.output_dir, f'news_analyzed_{timestamp}.csv')
        combined_news.to_csv(news_file, index=False)
        print(f"✓ Saved analyzed news to: {news_file}")
        
        # Save latest news
        latest_news_file = os.path.join(args.output_dir, 'news_analyzed_latest.csv')
        combined_news.to_csv(latest_news_file, index=False)
        print(f"✓ Saved latest news to: {latest_news_file}")
    
    # Print final summary
    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)
    print(f"Symbols processed: {len(all_summaries)}/{len(symbols)}")
    print(f"Total articles analyzed: {sum(s['article_count'] for s in all_summaries)}")
    
    if all_summaries:
        avg_sentiment = sum(s['average_sentiment'] for s in all_summaries) / len(all_summaries)
        print(f"Overall average sentiment: {avg_sentiment:.4f}")
        
        # Market sentiment summary
        bullish = sum(1 for s in all_summaries if s['sentiment_trend'] in ['bullish', 'slightly_bullish'])
        bearish = sum(1 for s in all_summaries if s['sentiment_trend'] in ['bearish', 'slightly_bearish'])
        neutral = sum(1 for s in all_summaries if s['sentiment_trend'] == 'neutral')
        
        print(f"Market sentiment: Bullish: {bullish}, Bearish: {bearish}, Neutral: {neutral}")
    
    print(f"\nCompleted at: {datetime.now()}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
