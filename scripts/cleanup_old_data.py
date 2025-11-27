"""
Clean up old data based on retention policies.

This script:
1. Archives data older than retention period to Parquet files
2. Deletes old data from main tables to reduce database size
3. Maintains data_retention_policy table with cleanup status
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import get_db_connection


# Default retention policies (in days)
DEFAULT_RETENTION_POLICIES = {
    'fred_data': {'days': -1, 'archive': True, 'description': 'FRED data - keep all (historical analysis)'},
    'yfinance_ohlcv': {'days': 730, 'archive': True, 'description': 'Stock OHLCV - keep 2 years'},
    'options_data': {'days': 90, 'archive': True, 'description': 'Options data - keep 90 days'},
    'market_indicators': {'days': 730, 'archive': True, 'description': 'Market indicators - keep 2 years'},
    'technical_features': {'days': 365, 'archive': True, 'description': 'Technical features - keep 1 year'},
    'derived_features': {'days': 365, 'archive': True, 'description': 'Derived features - keep 1 year'},
    'news_sentiment': {'days': 180, 'archive': True, 'description': 'News sentiment - keep 6 months'},
    'sentiment_summary': {'days': 365, 'archive': True, 'description': 'Sentiment summary - keep 1 year'},
    'sec_submissions': {'days': 1825, 'archive': True, 'description': 'SEC submissions - keep 5 years'},
    'sec_financial_statements': {'days': 1825, 'archive': True, 'description': 'SEC financials - keep 5 years'},
    'sec_company_facts': {'days': 730, 'archive': True, 'description': 'SEC company facts - keep 2 years'},
    'sec_filings': {'days': 1825, 'archive': True, 'description': 'SEC filings - keep 5 years'},
    'sec_fails_to_deliver': {'days': 365, 'archive': True, 'description': 'FTD data - keep 1 year'},
    'sec_13f_holdings': {'days': 730, 'archive': True, 'description': '13F holdings - keep 2 years'},
    'ml_predictions': {'days': 180, 'archive': False, 'description': 'ML predictions - keep 6 months'},
    'ml_training_data': {'days': 365, 'archive': True, 'description': 'ML training - keep 1 year'},
    'leverage_metrics': {'days': 365, 'archive': True, 'description': 'Leverage metrics - keep 1 year'},
    'margin_call_risk': {'days': 365, 'archive': True, 'description': 'Margin risk - keep 1 year'},
    'ici_etf_weekly_flows': {'days': 730, 'archive': True, 'description': 'ICI ETF flows - keep 2 years'},
    'ici_etf_flows': {'days': 730, 'archive': True, 'description': 'ICI ETF monthly - keep 2 years'},
    'cboe_vix_history': {'days': -1, 'archive': True, 'description': 'VIX history - keep all'},
    'cboe_vix_term_structure': {'days': 365, 'archive': True, 'description': 'VIX term structure - keep 1 year'},
    'insider_transactions': {'days': 730, 'archive': True, 'description': 'Insider trades - keep 2 years'},
    'insider_sentiment_scores': {'days': 365, 'archive': True, 'description': 'Insider sentiment - keep 1 year'},
    'insider_backtest_results': {'days': 365, 'archive': True, 'description': 'Backtest results - keep 1 year'},
}


def initialize_retention_policies():
    """Initialize data_retention_policy table with default policies."""
    db = get_db_connection()
    
    print("Initializing retention policies...")
    
    for table_name, policy in DEFAULT_RETENTION_POLICIES.items():
        # Check if policy already exists
        existing = db.query(f"""
            SELECT * FROM data_retention_policy 
            WHERE table_name = '{table_name}'
        """)
        
        if existing.empty:
            db.execute(f"""
                INSERT INTO data_retention_policy 
                (table_name, retention_days, archive_to_parquet, description)
                VALUES ('{table_name}', {policy['days']}, {policy['archive']}, '{policy['description']}')
            """)
            print(f"  ✓ Added policy for {table_name}: {policy['days']} days")
        else:
            print(f"  • Policy for {table_name} already exists")
    
    print("\n✓ Retention policies initialized")


def get_table_date_column(table_name: str) -> str:
    """Determine the date column for a given table."""
    # Map tables to their date columns
    date_columns = {
        'fred_data': 'date',
        'yfinance_ohlcv': 'date',
        'options_data': 'date',
        'market_indicators': 'date',
        'technical_features': 'date',
        'derived_features': 'date',
        'news_sentiment': 'published_date',
        'sentiment_summary': 'date',
        'sec_submissions': 'filed',
        'sec_financial_statements': 'ddate',
        'sec_company_facts': 'end_date',
        'sec_filings': 'filing_date',
        'sec_fails_to_deliver': 'settlement_date',
        'sec_13f_holdings': 'filing_date',
        'ml_predictions': 'prediction_date',
        'ml_training_data': 'as_of_date',
        'leverage_metrics': 'date',
        'margin_call_risk': 'date',
        'ici_etf_weekly_flows': 'week_ending',
        'ici_etf_flows': 'date',
        'cboe_vix_history': 'date',
        'cboe_vix_term_structure': 'date',
        'insider_transactions': 'transaction_date',
        'insider_sentiment_scores': 'analysis_date',
        'insider_backtest_results': 'backtest_date',
    }
    
    return date_columns.get(table_name, 'date')


def archive_old_data(table_name: str, cutoff_date: datetime, archive_dir: Path) -> int:
    """Archive old data to Parquet file."""
    db = get_db_connection()
    date_col = get_table_date_column(table_name)
    
    # Query old data
    query = f"""
        SELECT * FROM {table_name}
        WHERE {date_col} < DATE '{cutoff_date.strftime('%Y-%m-%d')}'
    """
    
    old_data = db.query(query)
    
    if old_data.empty:
        return 0
    
    # Create archive directory if needed
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # Export to Parquet with compression
    archive_file = archive_dir / f"{table_name}_archived_{datetime.now().strftime('%Y%m%d')}.parquet"
    
    # Use DuckDB's native Parquet export for best compression
    export_query = f"""
        COPY (
            SELECT * FROM {table_name}
            WHERE {date_col} < DATE '{cutoff_date.strftime('%Y-%m-%d')}'
        ) TO '{archive_file}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """
    
    db.execute(export_query)
    
    # Get file size
    file_size_mb = archive_file.stat().st_size / (1024 * 1024)
    
    print(f"  ✓ Archived {len(old_data):,} records to {archive_file.name} ({file_size_mb:.2f} MB)")
    
    return len(old_data)


def delete_old_data(table_name: str, cutoff_date: datetime) -> int:
    """Delete old data from table."""
    db = get_db_connection()
    date_col = get_table_date_column(table_name)
    
    # Count records to delete
    count_query = f"""
        SELECT COUNT(*) as count FROM {table_name}
        WHERE {date_col} < DATE '{cutoff_date.strftime('%Y-%m-%d')}'
    """
    
    count_result = db.query(count_query)
    records_to_delete = int(count_result['count'].iloc[0])
    
    if records_to_delete == 0:
        return 0
    
    # Delete old records
    delete_query = f"""
        DELETE FROM {table_name}
        WHERE {date_col} < DATE '{cutoff_date.strftime('%Y-%m-%d')}'
    """
    
    db.execute(delete_query)
    
    print(f"  ✓ Deleted {records_to_delete:,} old records from {table_name}")
    
    return records_to_delete


def cleanup_table(table_name: str, retention_days: int, archive: bool, 
                  archive_dir: Path, dry_run: bool = False) -> dict:
    """Clean up a single table based on retention policy."""
    
    if retention_days < 0:
        print(f"  • Skipping {table_name} (keep all data)")
        return {'archived': 0, 'deleted': 0}
    
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    print(f"\n{table_name}:")
    print(f"  Retention: {retention_days} days (cutoff: {cutoff_date.strftime('%Y-%m-%d')})")
    
    archived_count = 0
    deleted_count = 0
    
    if not dry_run:
        # Archive if enabled
        if archive:
            archived_count = archive_old_data(table_name, cutoff_date, archive_dir)
        
        # Delete old data
        if archived_count > 0 or not archive:
            deleted_count = delete_old_data(table_name, cutoff_date)
    else:
        # Dry run - just count
        db = get_db_connection()
        date_col = get_table_date_column(table_name)
        
        count_query = f"""
            SELECT COUNT(*) as count FROM {table_name}
            WHERE {date_col} < DATE '{cutoff_date.strftime('%Y-%m-%d')}'
        """
        
        count_result = db.query(count_query)
        deleted_count = int(count_result['count'].iloc[0])
        
        print(f"  [DRY RUN] Would archive/delete {deleted_count:,} records")
    
    return {'archived': archived_count, 'deleted': deleted_count}


def run_cleanup(dry_run: bool = False, tables: list = None):
    """Run cleanup for all tables or specified tables."""
    db = get_db_connection()
    archive_dir = Path(__file__).parent.parent / 'data' / 'duckdb' / 'archives'
    
    # Get retention policies
    policies = db.query("SELECT * FROM data_retention_policy")
    
    if policies.empty:
        print("No retention policies found. Run with --init to initialize.")
        return
    
    print("=" * 70)
    print("DATA CLEANUP - Retention Policy Enforcement")
    print("=" * 70)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No data will be modified\n")
    
    total_archived = 0
    total_deleted = 0
    
    for _, policy in policies.iterrows():
        table_name = policy['table_name']
        
        # Skip if specific tables requested and this isn't one
        if tables and table_name not in tables:
            continue
        
        # Check if table exists
        if not db.table_exists(table_name):
            print(f"  ⚠️  Table {table_name} does not exist, skipping")
            continue
        
        result = cleanup_table(
            table_name=table_name,
            retention_days=policy['retention_days'],
            archive=policy['archive_to_parquet'],
            archive_dir=archive_dir,
            dry_run=dry_run
        )
        
        total_archived += result['archived']
        total_deleted += result['deleted']
        
        # Update last_cleanup timestamp
        if not dry_run and result['deleted'] > 0:
            db.execute(f"""
                UPDATE data_retention_policy 
                SET last_cleanup = CURRENT_TIMESTAMP
                WHERE table_name = '{table_name}'
            """)
    
    print("\n" + "=" * 70)
    print("CLEANUP SUMMARY")
    print("=" * 70)
    print(f"Total records archived: {total_archived:,}")
    print(f"Total records deleted: {total_deleted:,}")
    
    if not dry_run and total_deleted > 0:
        print("\nRunning VACUUM to reclaim space...")
        db.vacuum()
        print("✓ Database compacted")
        
        # Get final database size
        db_size = db.get_database_size()
        print(f"\nDatabase size: {db_size['database_file_mb']:.2f} MB")
    
    print("=" * 70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up old data based on retention policies')
    parser.add_argument('--init', action='store_true', 
                       help='Initialize retention policies')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--tables', nargs='+',
                       help='Specific tables to clean (default: all)')
    
    args = parser.parse_args()
    
    try:
        if args.init:
            initialize_retention_policies()
        else:
            run_cleanup(dry_run=args.dry_run, tables=args.tables)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
