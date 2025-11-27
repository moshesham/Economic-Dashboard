"""Quick test of Insider Trading Tracker functionality"""

from modules.features.insider_trading_tracker import InsiderTradingTracker
import pandas as pd
from datetime import datetime, timedelta

print("Testing Insider Trading Tracker...")
print("=" * 60)

# Initialize tracker
tracker = InsiderTradingTracker()
print("[OK] Tracker initialized")
print(f"     Transaction codes: {len(tracker.transaction_codes)}")

# Create test data
base_date = datetime.now() - timedelta(days=90)
test_data = pd.DataFrame({
    'ticker': ['AAPL'] * 5,
    'transaction_date': [base_date + timedelta(days=i*10) for i in range(5)],
    'filing_date': [base_date] * 5,
    'insider_name': ['CEO', 'CFO', 'Director', 'VP', 'CEO'],
    'insider_title': ['CEO', 'CFO', 'Director', 'VP', 'CEO'],
    'is_director': [False, False, True, False, False],
    'is_officer': [True, True, False, True, True],
    'transaction_code': ['P', 'P', 'S', 'P', 'M'],
    'transaction_type': ['Purchase', 'Purchase', 'Sale', 'Purchase', 'Exercise'],
    'transaction_value': [100000, 50000, 200000, 75000, 120000],
    'shares': [1000] * 5,
    'price_per_share': [100] * 5,
    'acquired_disposed': ['A', 'A', 'D', 'A', 'A'],
    'shares_owned_after': [10000] * 5,
    'security_type': ['Common Stock'] * 5
})

print(f"[OK] Created test data with {len(test_data)} transactions")

# Test sentiment calculation
sentiment = tracker.calculate_insider_sentiment(test_data, days=90)
print("\n[OK] Sentiment Calculation:")
print(f"     Score: {sentiment['sentiment_score']:.2f}")
print(f"     Signal: {sentiment['signal']}")
print(f"     Buy Value: ${sentiment['buy_value']:,.0f}")
print(f"     Sell Value: ${sentiment['sell_value']:,.0f}")
print(f"     Confidence: {sentiment['confidence']}")

# Test unusual activity detection
unusual = tracker.detect_unusual_activity(test_data, lookback_days=90, baseline_days=180)
print("\n[OK] Unusual Activity Detection:")
print(f"     Is Unusual: {unusual['is_unusual']}")
print(f"     Volume Ratio: {unusual['volume_ratio']:.2f}x")
print(f"     Alerts: {len(unusual['alerts'])}")

# Test top buyers
top_buyers = tracker.get_top_insider_buyers(test_data, days=90, top_n=3)
print("\n[OK] Top Buyers:")
print(f"     Found {len(top_buyers)} buyers")
if not top_buyers.empty:
    for idx, row in top_buyers.iterrows():
        print(f"     - {row['Insider']}: ${row['Total Value']:,.0f}")

print("\n" + "=" * 60)
print("All tests passed! Insider Trading Tracker is working.")
print("=" * 60)
