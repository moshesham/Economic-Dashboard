"""
ICI ETF Flows Data Loader

Fetches ETF flow data from the Investment Company Institute (ICI):
https://www.ici.org/research/stats/etf_flows

ICI provides weekly and monthly ETF flow statistics including:
- Net new cash flows by fund category
- Total net assets
- Weekly estimated flows
"""

import pandas as pd
import requests
from datetime import datetime
from typing import Optional
import io
import time


# ICI ETF flows data URLs
ICI_WEEKLY_FLOWS_URL = "https://www.ici.org/system/files/stats/weekly_combined_efdata.csv"
ICI_MONTHLY_FLOWS_URL = "https://www.ici.org/system/files/stats/monthly_combined_efdata.csv"

# HTTP headers to mimic browser requests
ICI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}


def fetch_ici_weekly_etf_flows() -> pd.DataFrame:
    """
    Fetch weekly ETF flows data from ICI.
    
    Returns:
        DataFrame with weekly ETF flow data including:
        - week_ending: End date of the week
        - fund_type: Type of fund (Equity, Bond, Hybrid, etc.)
        - estimated_flows: Estimated weekly flows in millions
        - total_net_assets: Total net assets in millions
    """
    print("Fetching ICI weekly ETF flows data...")
    
    try:
        response = requests.get(
            ICI_WEEKLY_FLOWS_URL,
            headers=ICI_HEADERS,
            timeout=30
        )
        response.raise_for_status()
        
        # Parse CSV data
        df = pd.read_csv(io.StringIO(response.text))
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Rename columns to match our schema
        column_mapping = {
            'date': 'week_ending',
            'week_ending_date': 'week_ending',
            'fund_category': 'fund_type',
            'category': 'fund_type',
            'estimated_flow': 'estimated_flows',
            'flows': 'estimated_flows',
            'net_flow': 'estimated_flows',
            'tna': 'total_net_assets',
            'total_assets': 'total_net_assets',
            'assets': 'total_net_assets'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert date column
        if 'week_ending' in df.columns:
            df['week_ending'] = pd.to_datetime(df['week_ending'], errors='coerce')
        
        # Ensure required columns exist
        required_cols = ['week_ending', 'fund_type', 'estimated_flows', 'total_net_assets']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # Select and order columns
        df = df[required_cols].dropna(subset=['week_ending'])
        
        print(f"Successfully fetched {len(df)} weekly ETF flow records")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ICI weekly data: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing ICI weekly data: {e}")
        return pd.DataFrame()


def fetch_ici_monthly_etf_flows() -> pd.DataFrame:
    """
    Fetch monthly ETF flows data from ICI.
    
    Returns:
        DataFrame with monthly ETF flow data including:
        - date: Month end date
        - fund_category: Category of the fund
        - net_new_cash_flow: Net new cash flows
        - net_issuance: Net issuance
        - redemptions: Redemptions
        - reinvested_dividends: Reinvested dividends
        - total_net_assets: Total net assets
    """
    print("Fetching ICI monthly ETF flows data...")
    
    try:
        response = requests.get(
            ICI_MONTHLY_FLOWS_URL,
            headers=ICI_HEADERS,
            timeout=30
        )
        response.raise_for_status()
        
        # Parse CSV data
        df = pd.read_csv(io.StringIO(response.text))
        
        # Clean and standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Rename columns to match our schema
        column_mapping = {
            'month': 'date',
            'month_end': 'date',
            'period': 'date',
            'category': 'fund_category',
            'fund_type': 'fund_category',
            'net_cash_flow': 'net_new_cash_flow',
            'new_cash_flow': 'net_new_cash_flow',
            'cash_flow': 'net_new_cash_flow',
            'issuance': 'net_issuance',
            'net_issuance': 'net_issuance',
            'tna': 'total_net_assets',
            'total_assets': 'total_net_assets'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Ensure required columns exist
        required_cols = ['date', 'fund_category', 'net_new_cash_flow', 'net_issuance',
                        'redemptions', 'reinvested_dividends', 'total_net_assets']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # Select and order columns
        df = df[required_cols].dropna(subset=['date'])
        
        print(f"Successfully fetched {len(df)} monthly ETF flow records")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ICI monthly data: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error processing ICI monthly data: {e}")
        return pd.DataFrame()


def save_ici_etf_flows_to_duckdb(weekly_df: Optional[pd.DataFrame] = None,
                                  monthly_df: Optional[pd.DataFrame] = None) -> dict:
    """
    Save ICI ETF flows data to DuckDB database.
    
    Args:
        weekly_df: DataFrame with weekly flows data (or None to fetch)
        monthly_df: DataFrame with monthly flows data (or None to fetch)
        
    Returns:
        Dictionary with counts of records saved
    """
    from modules.database.connection import get_db_connection
    from modules.database.queries import log_data_refresh
    
    results = {'weekly_records': 0, 'monthly_records': 0}
    
    # Fetch data if not provided
    if weekly_df is None:
        weekly_df = fetch_ici_weekly_etf_flows()
    if monthly_df is None:
        monthly_df = fetch_ici_monthly_etf_flows()
    
    db = get_db_connection()
    
    # Save weekly flows
    if not weekly_df.empty:
        try:
            # Clean data for insertion
            weekly_clean = weekly_df.copy()
            weekly_clean['week_ending'] = pd.to_datetime(weekly_clean['week_ending'])
            
            db.insert_df(weekly_clean, 'ici_etf_weekly_flows', if_exists='append')
            results['weekly_records'] = len(weekly_clean)
            print(f"Saved {len(weekly_clean)} weekly ETF flow records to DuckDB")
        except Exception as e:
            print(f"Error saving weekly flows to DuckDB: {e}")
            log_data_refresh('ici_etf_weekly_flows', 0, 'failed', str(e))
    
    # Save monthly flows
    if not monthly_df.empty:
        try:
            # Clean data for insertion
            monthly_clean = monthly_df.copy()
            monthly_clean['date'] = pd.to_datetime(monthly_clean['date'])
            
            db.insert_df(monthly_clean, 'ici_etf_flows', if_exists='append')
            results['monthly_records'] = len(monthly_clean)
            print(f"Saved {len(monthly_clean)} monthly ETF flow records to DuckDB")
        except Exception as e:
            print(f"Error saving monthly flows to DuckDB: {e}")
            log_data_refresh('ici_etf_flows', 0, 'failed', str(e))
    
    # Log successful refresh
    total_records = results['weekly_records'] + results['monthly_records']
    if total_records > 0:
        log_data_refresh('ici_etf_data', total_records, 'completed')
    
    return results


def get_latest_etf_flows(fund_type: Optional[str] = None,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get latest ETF flows data from DuckDB.
    
    Args:
        fund_type: Optional fund type to filter by
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        DataFrame with ETF flow data
    """
    from modules.database.connection import get_db_connection
    
    db = get_db_connection()
    
    query = "SELECT * FROM ici_etf_weekly_flows WHERE 1=1"
    params = []
    
    if fund_type:
        query += " AND fund_type = ?"
        params.append(fund_type)
    
    if start_date:
        query += " AND week_ending >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND week_ending <= ?"
        params.append(end_date)
    
    query += " ORDER BY week_ending DESC"
    
    if params:
        return db.query(query, tuple(params))
    return db.query(query)


def refresh_ici_etf_data() -> dict:
    """
    Main function to refresh all ICI ETF data.
    Fetches both weekly and monthly data and saves to DuckDB.
    
    Returns:
        Dictionary with refresh statistics
    """
    print("=" * 60)
    print("ICI ETF Data Refresh")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    results = save_ici_etf_flows_to_duckdb()
    
    print("\n" + "=" * 60)
    print("ICI ETF Data Refresh Summary")
    print("=" * 60)
    print(f"Weekly records: {results['weekly_records']}")
    print(f"Monthly records: {results['monthly_records']}")
    print(f"Completed at: {datetime.now()}")
    
    return results


if __name__ == "__main__":
    refresh_ici_etf_data()
