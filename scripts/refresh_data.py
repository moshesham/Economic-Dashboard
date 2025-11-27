"""
Daily data refresh script for Economic Dashboard.
Fetches all economic data from FRED and Yahoo Finance and stores in cache.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import pickle
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pandas_datareader import data as pdr
import yfinance as yf
from config_settings import ensure_cache_dir, get_cache_dir


# All FRED series used across the dashboard
FRED_SERIES = {
    # GDP and Growth (Page 1)
    'GDP': 'GDP',
    'Real GDP': 'GDPC1',
    'GDP Growth Rate': 'A191RL1Q225SBEA',
    'Real GDP per Capita': 'A939RX0Q048SBEA',
    'Personal Consumption': 'PCE',
    'Private Investment': 'GPDIC1',
    'Government Spending': 'GCEC1',
    'Labor Productivity': 'OPHNFB',
    'Non-Farm Productivity': 'PNFI',
    
    # Inflation and Prices (Page 2)
    'CPI All Items': 'CPIAUCSL',
    'Core CPI': 'CPILFESL',
    'PCE Price Index': 'PCEPI',
    'Core PCE': 'PCEPILFE',
    'PPI Final Demand': 'PPIFGS',
    'Import Price Index': 'IR',
    '5Y Inflation Expectations': 'T5YIE',
    'Food CPI': 'CPIUFDSL',
    
    # Employment and Wages (Page 3)
    'Unemployment Rate': 'UNRATE',
    'Nonfarm Payrolls': 'PAYEMS',
    'Labor Force Participation': 'CIVPART',
    'Employment-Population Ratio': 'EMRATIO',
    'Average Hourly Earnings': 'CES0500000003',
    'Initial Jobless Claims': 'ICSA',
    '4-Week MA Claims': 'IC4WSA',
    'Job Openings': 'JTSJOL',
    
    # Consumer and Housing (Page 4)
    'Personal Consumption Expenditures': 'PCE',
    'Real PCE': 'PCEC96',
    'Personal Saving Rate': 'PSAVERT',
    'Retail Sales': 'RSXFS',
    'Housing Starts': 'HOUST',
    'Home Prices (Case-Shiller)': 'CSUSHPISA',
    '30Y Mortgage Rate': 'MORTGAGE30US',
    'New Home Sales': 'HSN1F',
    
    # Markets and Rates (Page 5)
    'Federal Funds Rate': 'FEDFUNDS',
    '10Y Treasury': 'DGS10',
    '2Y Treasury': 'DGS2',
    '5Y Treasury': 'DGS5',
    '30Y Treasury': 'DGS30',
    '10Y-2Y Spread': 'T10Y2Y',
    'M2 Money Supply': 'M2SL',
    'Prime Rate': 'DPRIME',
}

# Yahoo Finance tickers
YFINANCE_TICKERS = {
    'S&P 500': '^GSPC',
    'VIX': '^VIX',
    'USD Index': 'DX-Y.NYB',
    'Gold': 'GC=F',
    'Crude Oil': 'CL=F',
}


def fetch_fred_data(series_dict: dict, years_back: int = 20) -> pd.DataFrame:
    """Fetch all FRED data series."""
    print(f"Fetching {len(series_dict)} FRED series...")
    
    start_date = datetime.now() - pd.DateOffset(years=years_back)
    all_data = {}
    
    for i, (name, series_id) in enumerate(series_dict.items(), 1):
        try:
            print(f"  Fetching {name} ({series_id})...", end=' ')
            df = pdr.DataReader(series_id, 'fred', start=start_date)
            all_data[name] = df[series_id]
            print("✓")
            
            # Add small delay to avoid rate limiting (FRED allows ~120 calls/min)
            if i % 20 == 0:  # Pause every 20 requests
                time.sleep(1)
                
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    if not all_data:
        raise ValueError("No FRED data was successfully fetched")
    
    # Combine all series into single DataFrame
    combined_df = pd.DataFrame(all_data)
    print(f"Successfully fetched {len(all_data)} series with {len(combined_df)} rows")
    
    return combined_df


def fetch_yfinance_data(tickers_dict: dict, years_back: int = 10, max_retries: int = 3) -> dict:
    """Fetch Yahoo Finance data for market indicators with retry logic."""
    print(f"\nFetching {len(tickers_dict)} Yahoo Finance tickers...")
    
    start_date = datetime.now() - pd.DateOffset(years=years_back)
    all_data = {}
    
    for name, ticker in tickers_dict.items():
        success = False
        for attempt in range(max_retries):
            try:
                print(f"  Fetching {name} ({ticker})...", end=' ')
                
                # Add delay between requests to avoid rate limiting
                if attempt > 0:
                    wait_time = 5 * (attempt + 1)  # Exponential backoff: 10s, 15s
                    print(f"retry {attempt + 1}/{max_retries} (waiting {wait_time}s)...", end=' ')
                    time.sleep(wait_time)
                else:
                    time.sleep(1)  # Small delay between tickers
                
                # Use Ticker object for more reliable fetching
                ticker_obj = yf.Ticker(ticker)
                data = ticker_obj.history(start=start_date, auto_adjust=True)
                
                if not data.empty and len(data) > 0:
                    all_data[name] = data
                    print("✓")
                    success = True
                    break
                else:
                    print("✗ No data returned")
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"✗ Error: {str(e)[:50]}...")
                else:
                    print(f"✗ Failed after {max_retries} attempts: {str(e)[:50]}")
                continue
        
        if not success and name not in all_data:
            print(f"    ⚠️  Skipping {name} after all retries failed")
    
    print(f"Successfully fetched {len(all_data)} tickers")
    return all_data


def save_to_cache(data, cache_filename: str):
    """Save data to pickle cache with timestamp."""
    ensure_cache_dir()
    cache_file = os.path.join(get_cache_dir(), cache_filename)
    
    cache_data = {
        'timestamp': datetime.now(),
        'data': data
    }
    
    with open(cache_file, 'wb') as f:
        pickle.dump(cache_data, f)
    
    print(f"Saved to {cache_file}")


def save_to_csv_backup(data, csv_filename: str):
    """Save data to CSV for backup and inspection."""
    backup_dir = 'data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = os.path.join(backup_dir, f"{timestamp}_{csv_filename}")
    
    if isinstance(data, pd.DataFrame):
        data.to_csv(csv_file)
    elif isinstance(data, dict):
        # For Yahoo Finance data, save each ticker separately
        for name, df in data.items():
            ticker_file = csv_file.replace('.csv', f'_{name}.csv')
            df.to_csv(ticker_file)
    
    print(f"Backup saved to {csv_file}")


def main():
    """Main data refresh pipeline."""
    print("=" * 60)
    print("Economic Dashboard - Daily Data Refresh")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    try:
        # Fetch FRED data
        fred_data = fetch_fred_data(FRED_SERIES, years_back=20)
        save_to_cache(fred_data, 'fred_all_series.pkl')
        save_to_csv_backup(fred_data, 'fred_data.csv')
        
        # Fetch Yahoo Finance data
        yf_data = fetch_yfinance_data(YFINANCE_TICKERS, years_back=10)
        save_to_cache(yf_data, 'yfinance_all_tickers.pkl')
        save_to_csv_backup(yf_data, 'yfinance_data.csv')
        
        # Create summary report
        print("\n" + "=" * 60)
        print("Data Refresh Summary")
        print("=" * 60)
        print(f"FRED Series: {len(fred_data.columns)} series")
        print(f"  Date range: {fred_data.index.min()} to {fred_data.index.max()}")
        print(f"  Total rows: {len(fred_data)}")
        print(f"\nYahoo Finance: {len(yf_data)} tickers")
        for name, df in yf_data.items():
            print(f"  {name}: {len(df)} rows ({df.index.min()} to {df.index.max()})")
        print(f"\nCompleted at: {datetime.now()}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
