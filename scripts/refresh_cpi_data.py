"""
CPI Inflation Tracker Data Refresh Script

Fetches CPI basket data from FRED and stores it in DuckDB database.
This script can be run daily/weekly via GitHub Actions or Airflow.

Usage:
    python scripts/refresh_cpi_data.py

Features:
    - Fetches all CPI basket components from FRED API
    - Calculates YoY and MoM inflation rates
    - Stores data in DuckDB for fast querying
    - Supports incremental updates (only fetches new data)
    - Creates category-level breakdowns with contribution analysis
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import time
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pandas_datareader import data as pdr
from config_settings import ensure_cache_dir, get_cache_dir

# Import CPI basket configuration
from modules.cpi_basket_config import (
    CPI_BASKET,
    CPI_HEADLINE_INDICES,
    get_all_fred_series,
    get_primary_series,
    get_headline_series,
    get_all_cpi_items,
    CPIItem
)

# Import database functions
try:
    from modules.database import get_db_connection
    from modules.database.schema import (
        create_cpi_basket_items_table,
        create_cpi_price_data_table,
        create_cpi_inflation_summary_table,
        create_cpi_category_breakdown_table
    )
    from modules.database.queries import (
        insert_cpi_price_data,
        insert_cpi_inflation_summary,
        insert_cpi_category_breakdown,
        get_cpi_price_data,
        log_data_refresh
    )
    DUCKDB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: DuckDB not available: {e}")
    DUCKDB_AVAILABLE = False


def ensure_cpi_tables_exist():
    """Create CPI tables if they don't exist."""
    if not DUCKDB_AVAILABLE:
        print("DuckDB not available, skipping table creation")
        return False
    
    try:
        create_cpi_basket_items_table()
        create_cpi_price_data_table()
        create_cpi_inflation_summary_table()
        create_cpi_category_breakdown_table()
        print("✓ CPI tables created/verified")
        return True
    except Exception as e:
        print(f"Error creating CPI tables: {e}")
        return False


def get_last_data_date() -> Optional[datetime]:
    """Get the most recent date in the CPI price data table."""
    if not DUCKDB_AVAILABLE:
        return None
    
    try:
        db = get_db_connection()
        result = db.query("SELECT MAX(date) as max_date FROM cpi_price_data")
        if not result.empty and result['max_date'].iloc[0] is not None:
            return pd.to_datetime(result['max_date'].iloc[0])
    except Exception as e:
        print(f"Could not get last data date: {e}")
    
    return None


def fetch_cpi_series_data(series_dict: Dict[str, str], 
                          start_date: Optional[datetime] = None,
                          years_back: int = 10) -> pd.DataFrame:
    """
    Fetch CPI data from FRED for specified series.
    
    Args:
        series_dict: Dictionary mapping names to FRED series IDs
        start_date: Start date for data fetch (optional)
        years_back: Number of years to fetch if start_date not specified
        
    Returns:
        DataFrame with CPI data in long format
    """
    if start_date is None:
        start_date = datetime.now() - pd.DateOffset(years=years_back)
    
    print(f"Fetching {len(series_dict)} CPI series from FRED...")
    print(f"  Start date: {start_date.strftime('%Y-%m-%d')}")
    
    all_data = []
    successful = 0
    failed = 0
    
    for i, (name, series_id) in enumerate(series_dict.items(), 1):
        try:
            print(f"  [{i}/{len(series_dict)}] Fetching {name} ({series_id})...", end=' ')
            
            df = pdr.DataReader(series_id, 'fred', start=start_date)
            
            if not df.empty:
                # Convert to long format for database storage
                df = df.reset_index()
                df.columns = ['date', 'value']
                df['series_id'] = series_id
                df['name'] = name
                
                # Calculate YoY change (12-month change for monthly data)
                df['yoy_change'] = df['value'].pct_change(periods=12) * 100
                
                # Calculate MoM change
                df['mom_change'] = df['value'].pct_change(periods=1) * 100
                
                all_data.append(df)
                successful += 1
                print("✓")
            else:
                print("✗ No data")
                failed += 1
            
            # Rate limiting: FRED allows ~120 requests/minute
            if i % 20 == 0:
                time.sleep(1)
                
        except Exception as e:
            print(f"✗ Error: {e}")
            failed += 1
            continue
    
    if not all_data:
        print("No CPI data was successfully fetched")
        return pd.DataFrame()
    
    # Combine all series
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print(f"\nFetch Summary:")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total records: {len(combined_df)}")
    
    return combined_df


def calculate_inflation_summary(price_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate headline and core inflation summary.
    
    Args:
        price_data: DataFrame with CPI price data
        
    Returns:
        DataFrame with inflation summary by date
    """
    # Get headline indices
    headline_series = {
        'headline_cpi': 'CPIAUCSL',
        'core_cpi': 'CPILFESL',
        'food_cpi': 'CPIUFDSL',
        'energy_cpi': 'CPIENGSL'
    }
    
    summary_data = []
    
    # Get unique dates
    dates = price_data['date'].unique()
    
    for date in sorted(dates):
        date_data = price_data[price_data['date'] == date]
        
        row = {'date': date}
        
        for name, series_id in headline_series.items():
            series_data = date_data[date_data['series_id'] == series_id]
            if not series_data.empty:
                row[name] = series_data['value'].iloc[0]
                row[f'{name.replace("_cpi", "")}_yoy'] = series_data['yoy_change'].iloc[0]
                row[f'{name.replace("_cpi", "")}_mom'] = series_data['mom_change'].iloc[0]
        
        # Only add if we have at least headline data
        if 'headline_cpi' in row:
            summary_data.append(row)
    
    if not summary_data:
        return pd.DataFrame()
    
    return pd.DataFrame(summary_data)


def calculate_category_breakdown(price_data: pd.DataFrame, 
                                 cpi_items: List[CPIItem]) -> pd.DataFrame:
    """
    Calculate category-level breakdowns with contribution to headline.
    
    Args:
        price_data: DataFrame with CPI price data
        cpi_items: List of CPI basket items
        
    Returns:
        DataFrame with category breakdowns
    """
    # Create mapping of series_id to item info
    item_map = {item.fred_series_id: item for item in cpi_items}
    
    # Get unique dates
    dates = price_data['date'].unique()
    
    breakdown_data = []
    
    for date in sorted(dates):
        date_data = price_data[price_data['date'] == date]
        
        # Group by category
        category_stats = {}
        
        for _, row in date_data.iterrows():
            series_id = row['series_id']
            if series_id in item_map:
                item = item_map[series_id]
                category = item.category
                
                if category not in category_stats:
                    category_stats[category] = {
                        'values': [],
                        'weights': [],
                        'yoy_changes': []
                    }
                
                category_stats[category]['values'].append(row['value'])
                category_stats[category]['weights'].append(item.weight)
                if pd.notna(row['yoy_change']):
                    category_stats[category]['yoy_changes'].append(row['yoy_change'])
        
        # Calculate category-level metrics
        for category, stats in category_stats.items():
            if stats['values']:
                avg_yoy = sum(stats['yoy_changes']) / len(stats['yoy_changes']) if stats['yoy_changes'] else None
                total_weight = sum(stats['weights'])
                contribution = (avg_yoy * total_weight / 100) if avg_yoy and total_weight else None
                
                breakdown_data.append({
                    'date': date,
                    'category': category,
                    'value': sum(stats['values']) / len(stats['values']),
                    'weight': total_weight,
                    'yoy_change': avg_yoy,
                    'contribution_to_headline': contribution
                })
    
    return pd.DataFrame(breakdown_data) if breakdown_data else pd.DataFrame()


def save_to_database(price_data: pd.DataFrame, 
                     summary_data: pd.DataFrame,
                     breakdown_data: pd.DataFrame) -> Tuple[int, int, int]:
    """
    Save CPI data to DuckDB database.
    
    Args:
        price_data: CPI price data
        summary_data: Inflation summary data
        breakdown_data: Category breakdown data
        
    Returns:
        Tuple of (price_records, summary_records, breakdown_records)
    """
    if not DUCKDB_AVAILABLE:
        print("DuckDB not available, skipping database save")
        return (0, 0, 0)
    
    price_count = 0
    summary_count = 0
    breakdown_count = 0
    
    try:
        if not price_data.empty:
            # Prepare price data for insertion
            price_df = price_data[['series_id', 'date', 'value', 'yoy_change', 'mom_change']].copy()
            price_count = insert_cpi_price_data(price_df)
            print(f"✓ Inserted {price_count} CPI price records")
    except Exception as e:
        print(f"Error inserting price data: {e}")
    
    try:
        if not summary_data.empty:
            summary_count = insert_cpi_inflation_summary(summary_data)
            print(f"✓ Inserted {summary_count} inflation summary records")
    except Exception as e:
        print(f"Error inserting summary data: {e}")
    
    try:
        if not breakdown_data.empty:
            breakdown_count = insert_cpi_category_breakdown(breakdown_data)
            print(f"✓ Inserted {breakdown_count} category breakdown records")
    except Exception as e:
        print(f"Error inserting breakdown data: {e}")
    
    return (price_count, summary_count, breakdown_count)


def save_to_csv_backup(data: pd.DataFrame, filename: str):
    """Save data to CSV for backup."""
    backup_dir = 'data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(backup_dir, f"{timestamp}_{filename}")
    
    data.to_csv(filepath, index=False)
    print(f"✓ Backup saved to {filepath}")


def run_full_refresh(years_back: int = 10):
    """
    Run a full CPI data refresh.
    
    Args:
        years_back: Number of years of historical data to fetch
    """
    print("=" * 60)
    print("CPI Inflation Tracker - Full Refresh")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    # Ensure database tables exist
    if DUCKDB_AVAILABLE:
        ensure_cpi_tables_exist()
    
    # Get primary CPI series (main indicators)
    primary_series = get_primary_series()
    
    # Fetch primary series data
    print("\n--- Fetching Primary CPI Series ---")
    price_data = fetch_cpi_series_data(primary_series, years_back=years_back)
    
    if price_data.empty:
        print("No data fetched, aborting")
        return 1
    
    # Calculate inflation summary
    print("\n--- Calculating Inflation Summary ---")
    summary_data = calculate_inflation_summary(price_data)
    print(f"Generated {len(summary_data)} summary records")
    
    # Calculate category breakdown
    print("\n--- Calculating Category Breakdowns ---")
    cpi_items = get_all_cpi_items()
    breakdown_data = calculate_category_breakdown(price_data, cpi_items)
    print(f"Generated {len(breakdown_data)} breakdown records")
    
    # Save to database
    print("\n--- Saving to Database ---")
    price_count, summary_count, breakdown_count = save_to_database(
        price_data, summary_data, breakdown_data
    )
    
    # Save CSV backups
    print("\n--- Creating Backups ---")
    save_to_csv_backup(price_data, 'cpi_price_data.csv')
    if not summary_data.empty:
        save_to_csv_backup(summary_data, 'cpi_inflation_summary.csv')
    if not breakdown_data.empty:
        save_to_csv_backup(breakdown_data, 'cpi_category_breakdown.csv')
    
    # Log the refresh
    if DUCKDB_AVAILABLE:
        try:
            total_records = price_count + summary_count + breakdown_count
            log_data_refresh('cpi_data', total_records, 'completed')
        except Exception as e:
            print(f"Could not log refresh: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("CPI Data Refresh Summary")
    print("=" * 60)
    print(f"Price data records: {len(price_data)}")
    print(f"  Date range: {price_data['date'].min()} to {price_data['date'].max()}")
    print(f"  Series count: {price_data['series_id'].nunique()}")
    print(f"Summary records: {len(summary_data)}")
    print(f"Breakdown records: {len(breakdown_data)}")
    print(f"\nDatabase records inserted:")
    print(f"  Price data: {price_count}")
    print(f"  Summary data: {summary_count}")
    print(f"  Breakdown data: {breakdown_count}")
    print(f"\nCompleted at: {datetime.now()}")
    print("=" * 60)
    
    return 0


def run_incremental_refresh():
    """
    Run an incremental CPI data refresh (only fetch new data).
    """
    print("=" * 60)
    print("CPI Inflation Tracker - Incremental Refresh")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    # Ensure database tables exist
    if DUCKDB_AVAILABLE:
        ensure_cpi_tables_exist()
    
    # Get last data date
    last_date = get_last_data_date()
    
    if last_date is None:
        print("No existing data found, running full refresh...")
        return run_full_refresh()
    
    # Start from last date minus 1 month (to ensure we capture any revisions)
    start_date = last_date - timedelta(days=30)
    print(f"Last data date: {last_date.strftime('%Y-%m-%d')}")
    print(f"Fetching from: {start_date.strftime('%Y-%m-%d')}")
    
    # Get primary CPI series
    primary_series = get_primary_series()
    
    # Fetch data
    print("\n--- Fetching New CPI Data ---")
    price_data = fetch_cpi_series_data(primary_series, start_date=start_date)
    
    if price_data.empty:
        print("No new data fetched")
        return 0
    
    # Calculate summaries
    print("\n--- Calculating Summaries ---")
    summary_data = calculate_inflation_summary(price_data)
    
    cpi_items = get_all_cpi_items()
    breakdown_data = calculate_category_breakdown(price_data, cpi_items)
    
    # Save to database (with upsert logic)
    print("\n--- Saving to Database ---")
    # Note: The current insert functions will add new records
    # For production, consider implementing upsert logic
    price_count, summary_count, breakdown_count = save_to_database(
        price_data, summary_data, breakdown_data
    )
    
    print("\n" + "=" * 60)
    print(f"Incremental refresh completed at: {datetime.now()}")
    print(f"New records: {price_count + summary_count + breakdown_count}")
    print("=" * 60)
    
    return 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CPI Inflation Tracker Data Refresh')
    parser.add_argument('--full', action='store_true', 
                        help='Run full historical refresh (default: incremental)')
    parser.add_argument('--years', type=int, default=10,
                        help='Years of historical data for full refresh (default: 10)')
    
    args = parser.parse_args()
    
    try:
        if args.full:
            return run_full_refresh(years_back=args.years)
        else:
            return run_incremental_refresh()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
