"""
Migrate Pickle Cache to DuckDB

Migrates existing pickle cache files to the new DuckDB database.
Handles FRED data and yfinance OHLCV data.
"""

import sys
from pathlib import Path
import pickle
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import get_db_connection, insert_fred_data, insert_stock_data


def load_pickle_file(file_path: Path):
    """Load a pickle file safely"""
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None


def migrate_fred_data():
    """Migrate FRED data from pickle to DuckDB"""
    print("\n" + "=" * 60)
    print("Migrating FRED Data")
    print("=" * 60)
    
    pickle_path = Path('data/cache/fred_all_series.pkl')
    
    if not pickle_path.exists():
        print(f"⚠️  No pickle file found at {pickle_path}")
        print("   Skipping FRED data migration")
        return 0
    
    print(f"Loading FRED data from {pickle_path}...")
    cached_data = load_pickle_file(pickle_path)
    
    if cached_data is None:
        return 0
    
    # Handle the cached format with 'timestamp' and 'data' keys
    if isinstance(cached_data, dict) and 'data' in cached_data:
        fred_data = cached_data['data']
        print(f"Loaded cached FRED data (timestamp: {cached_data.get('timestamp', 'unknown')})")
    else:
        fred_data = cached_data
    
    if isinstance(fred_data, pd.DataFrame):
        print(f"Found FRED DataFrame with shape {fred_data.shape}")
        print(f"Columns: {fred_data.columns.tolist()}")
        
        # Check if already in long format
        if 'series_id' in fred_data.columns and 'date' in fred_data.columns:
            records_inserted = insert_fred_data(fred_data)
            print(f"✓ Inserted {records_inserted} FRED records")
            return records_inserted
        else:
            # Convert from wide to long format
            # Reset index to get date column
            fred_long = fred_data.reset_index()
            
            # Get the date column name (could be 'index', 'DATE', 'date', etc.)
            date_col = fred_long.columns[0]
            
            # Melt to long format
            fred_long = fred_long.melt(
                id_vars=[date_col], 
                var_name='series_id', 
                value_name='value'
            )
            fred_long.rename(columns={date_col: 'date'}, inplace=True)
            
            # Drop NaN values
            fred_long = fred_long.dropna(subset=['value'])
            
            # Select final columns
            fred_long = fred_long[['series_id', 'date', 'value']]
            
            print(f"Converted to long format: {len(fred_long)} records")
            print(f"Series: {fred_long['series_id'].unique().tolist()}")
            
            records_inserted = insert_fred_data(fred_long)
            print(f"✓ Inserted {records_inserted} FRED records")
            return records_inserted
    
    elif isinstance(fred_data, dict):
        print(f"Found {len(fred_data)} FRED series in dict format")
        
        # Convert dict to long format DataFrame
        all_records = []
        
        for series_id, series_data in fred_data.items():
            if isinstance(series_data, pd.Series):
                df = series_data.reset_index()
                df.columns = ['date', 'value']
                df['series_id'] = series_id
                all_records.append(df)
            elif isinstance(series_data, pd.DataFrame):
                # Assume first column is date, second is value
                df = series_data.reset_index()
                if len(df.columns) >= 2:
                    df = df.iloc[:, :2]
                    df.columns = ['date', 'value']
                    df['series_id'] = series_id
                    all_records.append(df)
        
        if all_records:
            combined_df = pd.concat(all_records, ignore_index=True)
            combined_df = combined_df[['series_id', 'date', 'value']]
            combined_df = combined_df.dropna(subset=['value'])
            
            print(f"Inserting {len(combined_df)} FRED records...")
            records_inserted = insert_fred_data(combined_df)
            print(f"✓ Inserted {records_inserted} FRED records")
            return records_inserted
    
    return 0


def migrate_yfinance_data():
    """Migrate yfinance data from pickle to DuckDB"""
    print("\n" + "=" * 60)
    print("Migrating yfinance Data")
    print("=" * 60)
    
    pickle_path = Path('data/cache/yfinance_all_tickers.pkl')
    
    if not pickle_path.exists():
        print(f"⚠️  No pickle file found at {pickle_path}")
        print("   Skipping yfinance data migration")
        return 0
    
    print(f"Loading yfinance data from {pickle_path}...")
    cached_data = load_pickle_file(pickle_path)
    
    if cached_data is None:
        return 0
    
    # Handle the cached format with 'timestamp' and 'data' keys
    if isinstance(cached_data, dict) and 'data' in cached_data:
        yf_data = cached_data['data']
        print(f"Loaded cached yfinance data (timestamp: {cached_data.get('timestamp', 'unknown')})")
    else:
        yf_data = cached_data
    
    if isinstance(yf_data, dict):
        print(f"Found {len(yf_data)} tickers")
        
        all_records = []
        
        for ticker, ticker_data in yf_data.items():
            if isinstance(ticker_data, pd.DataFrame) and len(ticker_data) > 0:
                df = ticker_data.copy()
                
                # Handle MultiIndex columns
                if isinstance(df.columns, pd.MultiIndex):
                    # Flatten MultiIndex columns - take the first level (metric name)
                    df.columns = df.columns.get_level_values(0)
                
                # Reset index to get date column
                df = df.reset_index()
                
                # Standardize column names
                df.columns = df.columns.str.lower()
                
                # Rename date column variants
                date_col_mapping = {'index': 'date', 'datetime': 'date', 'timestamp': 'date'}
                df.rename(columns=date_col_mapping, inplace=True)
                
                # Ensure we have a date column
                if 'date' not in df.columns and len(df.columns) > 0:
                    # Use first column as date if it looks like a date
                    first_col = df.columns[0]
                    if pd.api.types.is_datetime64_any_dtype(df[first_col]) or 'date' in first_col.lower():
                        df.rename(columns={first_col: 'date'}, inplace=True)
                
                # Add ticker column
                df['ticker'] = ticker
                
                # Map common column name variations
                column_mapping = {
                    'adj close': 'adj_close',
                    'adjclose': 'adj_close',
                    'adjusted_close': 'adj_close',
                    'adj_close': 'adj_close'
                }
                df.rename(columns=column_mapping, inplace=True)
                
                # Select required columns (in order expected by database)
                required_cols = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']
                available_cols = [col for col in required_cols if col in df.columns]
                
                # Add adj_close if available
                if 'adj_close' in df.columns:
                    available_cols.append('adj_close')
                
                if 'date' in available_cols and 'ticker' in available_cols:
                    all_records.append(df[available_cols])
                else:
                    print(f"⚠️  Skipping {ticker} - missing required columns")
                    print(f"   Available: {df.columns.tolist()}")
        
        if all_records:
            combined_df = pd.concat(all_records, ignore_index=True)
            
            # Drop rows with missing required values
            combined_df = combined_df.dropna(subset=['date', 'close'])
            
            print(f"Inserting {len(combined_df)} yfinance records for {combined_df['ticker'].nunique()} tickers...")
            records_inserted = insert_stock_data(combined_df)
            print(f"✓ Inserted {records_inserted} yfinance records")
            return records_inserted
    
    elif isinstance(yf_data, pd.DataFrame):
        print(f"Found yfinance DataFrame with {len(yf_data)} records")
        
        if 'ticker' in yf_data.columns:
            records_inserted = insert_stock_data(yf_data)
            print(f"✓ Inserted {records_inserted} yfinance records")
            return records_inserted
    
    return 0


def verify_migration():
    """Verify the migration was successful"""
    print("\n" + "=" * 60)
    print("Verifying Migration")
    print("=" * 60)
    
    db = get_db_connection()
    
    # Check FRED data
    fred_count = db.get_row_count('fred_data')
    print(f"\nFRED data:")
    print(f"  • Total records: {fred_count}")
    
    if fred_count > 0:
        fred_stats = db.query("""
            SELECT 
                COUNT(DISTINCT series_id) as num_series,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM fred_data
        """)
        print(f"  • Unique series: {fred_stats['num_series'].iloc[0]}")
        print(f"  • Date range: {fred_stats['earliest_date'].iloc[0]} to {fred_stats['latest_date'].iloc[0]}")
    
    # Check yfinance data
    yf_count = db.get_row_count('yfinance_ohlcv')
    print(f"\nyfinance data:")
    print(f"  • Total records: {yf_count}")
    
    if yf_count > 0:
        yf_stats = db.query("""
            SELECT 
                COUNT(DISTINCT ticker) as num_tickers,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM yfinance_ohlcv
        """)
        print(f"  • Unique tickers: {yf_stats['num_tickers'].iloc[0]}")
        print(f"  • Date range: {yf_stats['earliest_date'].iloc[0]} to {yf_stats['latest_date'].iloc[0]}")
    
    return fred_count + yf_count


def main():
    print("=" * 60)
    print("Economic Dashboard - Pickle to DuckDB Migration")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    
    try:
        # Migrate FRED data
        fred_records = migrate_fred_data()
        
        # Migrate yfinance data
        yf_records = migrate_yfinance_data()
        
        # Verify migration
        total_records = verify_migration()
        
        print("\n" + "=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"FRED records migrated: {fred_records}")
        print(f"yfinance records migrated: {yf_records}")
        print(f"Total records in database: {total_records}")
        print("\n✅ Migration completed successfully!")
        print("=" * 60)
        
        print("\nNext steps:")
        print("1. Update data_loader.py to use DuckDB instead of pickle")
        print("2. Test the dashboard with the new database")
        print("3. Once verified, you can delete the pickle cache files")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
