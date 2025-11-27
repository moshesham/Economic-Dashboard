"""
CBOE VIX Historical Data Loader

Fetches VIX historical data from the Chicago Board Options Exchange (CBOE):
https://www.cboe.com/tradable_products/vix/vix_historical_data/

CBOE provides:
- Daily VIX index values (OHLC)
- VIX futures term structure data
- Historical volatility data
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional
import io


# CBOE VIX data URLs
CBOE_VIX_HISTORICAL_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
CBOE_VIX9D_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv"
CBOE_VIX3M_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv"
CBOE_VIX6M_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX6M_History.csv"

# HTTP headers
CBOE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/csv,application/csv,text/plain,*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.cboe.com/',
}


def fetch_cboe_vix_history() -> pd.DataFrame:
    """
    Fetch historical VIX data from CBOE.
    
    Returns:
        DataFrame with columns:
        - date: Trading date
        - open: Opening VIX value
        - high: High VIX value
        - low: Low VIX value
        - close: Closing VIX value
    """
    print("Fetching CBOE VIX historical data...")
    
    try:
        response = requests.get(
            CBOE_VIX_HISTORICAL_URL,
            headers=CBOE_HEADERS,
            timeout=30
        )
        response.raise_for_status()
        
        # Parse CSV data
        df = pd.read_csv(io.StringIO(response.text))
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Rename columns to match our schema
        column_mapping = {
            'trade date': 'date',
            'trade_date': 'date',
            'vix open': 'open',
            'vix high': 'high',
            'vix low': 'low',
            'vix close': 'close'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Ensure required columns exist
        required_cols = ['date', 'open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                # Try alternate column names
                if col == 'date':
                    date_cols = [c for c in df.columns if 'date' in c.lower()]
                    if date_cols:
                        df['date'] = df[date_cols[0]]
                elif col in ['open', 'high', 'low', 'close']:
                    matching_cols = [c for c in df.columns if col in c.lower()]
                    if matching_cols:
                        df[col] = df[matching_cols[0]]
                    else:
                        df[col] = None
        
        # Select columns
        df = df[['date', 'open', 'high', 'low', 'close']].dropna(subset=['date'])
        
        # Convert numeric columns
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"Successfully fetched {len(df)} VIX historical records")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching CBOE VIX data: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing CBOE VIX data: {e}")
        return pd.DataFrame()


def fetch_cboe_vix_variants() -> dict:
    """
    Fetch variant VIX indices (9-day, 3-month, 6-month) from CBOE.
    
    Returns:
        Dictionary with DataFrames for each VIX variant
    """
    variants = {
        'VIX9D': CBOE_VIX9D_URL,
        'VIX3M': CBOE_VIX3M_URL,
        'VIX6M': CBOE_VIX6M_URL,
    }
    
    results = {}
    
    for name, url in variants.items():
        print(f"Fetching {name} data...")
        try:
            response = requests.get(url, headers=CBOE_HEADERS, timeout=30)
            response.raise_for_status()
            
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = df.columns.str.strip().str.lower()
            
            # Standardize date column
            date_cols = [c for c in df.columns if 'date' in c.lower()]
            if date_cols:
                df['date'] = pd.to_datetime(df[date_cols[0]], errors='coerce')
            
            # Get close price column
            close_cols = [c for c in df.columns if 'close' in c.lower()]
            if close_cols:
                df['close'] = pd.to_numeric(df[close_cols[0]], errors='coerce')
            
            if 'date' in df.columns and 'close' in df.columns:
                results[name] = df[['date', 'close']].dropna().sort_values('date')
                print(f"  {name}: {len(results[name])} records")
            
        except Exception as e:
            print(f"  Error fetching {name}: {e}")
    
    return results


def save_cboe_vix_to_duckdb(vix_df: Optional[pd.DataFrame] = None) -> dict:
    """
    Save CBOE VIX data to DuckDB database.
    
    Args:
        vix_df: DataFrame with VIX data (or None to fetch)
        
    Returns:
        Dictionary with count of records saved
    """
    from modules.database.connection import get_db_connection
    from modules.database.queries import log_data_refresh
    
    results = {'vix_records': 0}
    
    # Fetch data if not provided
    if vix_df is None:
        vix_df = fetch_cboe_vix_history()
    
    if vix_df.empty:
        print("No VIX data to save")
        return results
    
    db = get_db_connection()
    
    try:
        # Clean data for insertion
        vix_clean = vix_df.copy()
        vix_clean['date'] = pd.to_datetime(vix_clean['date'])
        
        # Ensure numeric columns
        for col in ['open', 'high', 'low', 'close']:
            vix_clean[col] = pd.to_numeric(vix_clean[col], errors='coerce')
        
        db.insert_df(vix_clean, 'cboe_vix_history', if_exists='append')
        results['vix_records'] = len(vix_clean)
        print(f"Saved {len(vix_clean)} VIX records to DuckDB")
        
        # Log successful refresh
        log_data_refresh('cboe_vix_history', len(vix_clean), 'completed')
        
    except Exception as e:
        print(f"Error saving VIX data to DuckDB: {e}")
        log_data_refresh('cboe_vix_history', 0, 'failed', str(e))
    
    return results


def get_vix_history(start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get VIX historical data from DuckDB.
    
    Args:
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        DataFrame with VIX history
    """
    from modules.database.connection import get_db_connection
    
    db = get_db_connection()
    
    query = "SELECT * FROM cboe_vix_history WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " ORDER BY date"
    
    if params:
        return db.query(query, tuple(params))
    return db.query(query)


def get_latest_vix_value() -> Optional[float]:
    """
    Get the most recent VIX close value from database.
    
    Returns:
        Latest VIX close value or None if no data
    """
    from modules.database.connection import get_db_connection
    
    db = get_db_connection()
    
    query = "SELECT close FROM cboe_vix_history ORDER BY date DESC LIMIT 1"
    result = db.query(query)
    
    if not result.empty:
        return float(result['close'].iloc[0])
    return None


def calculate_vix_statistics(days: int = 252) -> dict:
    """
    Calculate VIX statistics over a specified period.
    
    Args:
        days: Number of trading days to analyze
        
    Returns:
        Dictionary with VIX statistics
    """
    from modules.database.connection import get_db_connection
    
    db = get_db_connection()
    
    # Use integer cast for safety, as LIMIT doesn't support parameterized queries in DuckDB
    safe_days = int(days)
    query = f"""
        SELECT 
            MIN(close) as min_vix,
            MAX(close) as max_vix,
            AVG(close) as avg_vix,
            STDDEV(close) as std_vix,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY close) as median_vix,
            COUNT(*) as total_days
        FROM (
            SELECT close FROM cboe_vix_history 
            ORDER BY date DESC 
            LIMIT {safe_days}
        )
    """
    
    result = db.query(query)
    
    if not result.empty:
        return {
            'min': float(result['min_vix'].iloc[0]) if result['min_vix'].iloc[0] else None,
            'max': float(result['max_vix'].iloc[0]) if result['max_vix'].iloc[0] else None,
            'avg': float(result['avg_vix'].iloc[0]) if result['avg_vix'].iloc[0] else None,
            'std': float(result['std_vix'].iloc[0]) if result['std_vix'].iloc[0] else None,
            'median': float(result['median_vix'].iloc[0]) if result['median_vix'].iloc[0] else None,
            'days_analyzed': int(result['total_days'].iloc[0])
        }
    
    return {}


def calculate_vix_percentile(current_vix: Optional[float] = None,
                             lookback_days: int = 252) -> Optional[float]:
    """
    Calculate the percentile rank of current VIX compared to historical values.
    
    Args:
        current_vix: Current VIX value (or None to use latest from DB)
        lookback_days: Number of trading days for comparison
        
    Returns:
        Percentile rank (0-100) or None if insufficient data
    """
    from modules.database.connection import get_db_connection
    
    if current_vix is None:
        current_vix = get_latest_vix_value()
        if current_vix is None:
            return None
    
    db = get_db_connection()
    
    # Use parameterized query for safety
    query = """
        SELECT 
            COUNT(*) as below_count,
            (SELECT COUNT(*) FROM (
                SELECT close FROM cboe_vix_history 
                ORDER BY date DESC 
                LIMIT ?
            )) as total_count
        FROM (
            SELECT close FROM cboe_vix_history 
            ORDER BY date DESC 
            LIMIT ?
        ) WHERE close < ?
    """
    
    result = db.query(query, (lookback_days, lookback_days, current_vix))
    
    if not result.empty and result['total_count'].iloc[0] > 0:
        below_count = int(result['below_count'].iloc[0])
        total_count = int(result['total_count'].iloc[0])
        return (below_count / total_count) * 100
    
    return None


def refresh_cboe_vix_data() -> dict:
    """
    Main function to refresh all CBOE VIX data.
    Fetches historical data and saves to DuckDB.
    
    Returns:
        Dictionary with refresh statistics
    """
    print("=" * 60)
    print("CBOE VIX Data Refresh")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    results = save_cboe_vix_to_duckdb()
    
    # Calculate some statistics
    if results['vix_records'] > 0:
        stats = calculate_vix_statistics()
        if stats:
            print(f"\nVIX Statistics (1-year):")
            print(f"  Min: {stats.get('min', 'N/A'):.2f}" if stats.get('min') else "  Min: N/A")
            print(f"  Max: {stats.get('max', 'N/A'):.2f}" if stats.get('max') else "  Max: N/A")
            print(f"  Avg: {stats.get('avg', 'N/A'):.2f}" if stats.get('avg') else "  Avg: N/A")
    
    print("\n" + "=" * 60)
    print("CBOE VIX Data Refresh Summary")
    print("=" * 60)
    print(f"VIX records: {results['vix_records']}")
    print(f"Completed at: {datetime.now()}")
    
    return results


if __name__ == "__main__":
    refresh_cboe_vix_data()
