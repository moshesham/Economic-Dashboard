"""
Database Compaction and Optimization Script

This script:
1. Runs VACUUM to reclaim space from deleted rows
2. Rebuilds indexes with ANALYZE for better query performance
3. Deduplicates records within retention windows
4. Measures compression ratios and reports savings
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import get_db_connection


def get_database_metrics():
    """Get current database size and metrics."""
    db = get_db_connection()
    db_path = Path(__file__).parent.parent / 'data' / 'duckdb' / 'economic_dashboard.duckdb'
    
    metrics = {
        'file_size_mb': db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0,
        'tables': {}
    }
    
    # Get table row counts
    tables = db.query("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'main'
        ORDER BY table_name
    """)
    
    for table_name in tables['table_name']:
        row_count = db.get_row_count(table_name)
        metrics['tables'][table_name] = {
            'rows': row_count
        }
    
    return metrics


def deduplicate_table(table_name: str, unique_columns: list) -> int:
    """
    Remove duplicate records from a table.
    
    Args:
        table_name: Name of table to deduplicate
        unique_columns: Columns that define uniqueness
        
    Returns:
        Number of duplicates removed
    """
    db = get_db_connection()
    
    # Count duplicates
    unique_cols_str = ', '.join(unique_columns)
    
    duplicate_query = f"""
        SELECT COUNT(*) as dup_count
        FROM (
            SELECT {unique_cols_str}, COUNT(*) as cnt
            FROM {table_name}
            GROUP BY {unique_cols_str}
            HAVING COUNT(*) > 1
        )
    """
    
    dup_result = db.query(duplicate_query)
    dup_count = int(dup_result['dup_count'].iloc[0])
    
    if dup_count == 0:
        return 0
    
    print(f"  Found {dup_count} duplicate groups in {table_name}")
    
    # Create temp table with deduplicated data
    # Keep the most recent record (based on created_at if available)
    order_col = 'created_at DESC' if 'created_at' in db.query(f"DESCRIBE {table_name}")['column_name'].values else ''
    
    if order_col:
        # Use ROW_NUMBER to keep most recent
        dedup_query = f"""
            CREATE TEMP TABLE {table_name}_dedup AS
            SELECT * FROM (
                SELECT *, 
                       ROW_NUMBER() OVER (PARTITION BY {unique_cols_str} ORDER BY {order_col}) as rn
                FROM {table_name}
            ) WHERE rn = 1
        """
    else:
        # Just use DISTINCT
        dedup_query = f"""
            CREATE TEMP TABLE {table_name}_dedup AS
            SELECT DISTINCT ON ({unique_cols_str}) *
            FROM {table_name}
        """
    
    db.execute(dedup_query)
    
    # Get count from dedup table
    dedup_count = db.get_row_count(f"{table_name}_dedup")
    records_removed = db.get_row_count(table_name) - dedup_count
    
    # Replace original table
    db.execute(f"DELETE FROM {table_name}")
    db.execute(f"INSERT INTO {table_name} SELECT * FROM {table_name}_dedup")
    db.execute(f"DROP TABLE {table_name}_dedup")
    
    print(f"  ✓ Removed {records_removed} duplicate records from {table_name}")
    
    return records_removed


def deduplicate_all_tables():
    """Deduplicate all tables based on their primary keys."""
    db = get_db_connection()
    
    # Define primary key columns for each table
    table_unique_keys = {
        'fred_data': ['series_id', 'date'],
        'yfinance_ohlcv': ['ticker', 'date'],
        'options_data': ['ticker', 'date', 'expiration_date'],
        'market_indicators': ['date'],
        'technical_features': ['ticker', 'date'],
        'derived_features': ['ticker', 'date'],
        'cboe_vix_history': ['date'],
        'cboe_vix_term_structure': ['date', 'days_to_expiration'],
        'ici_etf_weekly_flows': ['week_ending'],
        'ici_etf_flows': ['date'],
        'news_sentiment': ['article_id'],
        'sec_submissions': ['adsh'],
        'sec_financial_statements': ['adsh', 'tag', 'ddate', 'qtrs', 'coreg'],
        'sec_filings': ['cik', 'accession_number'],
        'insider_transactions': ['accession_number', 'transaction_date', 'insider_name'],
        'insider_sentiment_scores': ['ticker', 'analysis_date'],
    }
    
    print("\n" + "=" * 70)
    print("DEDUPLICATING TABLES")
    print("=" * 70)
    
    total_removed = 0
    
    for table_name, unique_cols in table_unique_keys.items():
        if db.table_exists(table_name):
            try:
                removed = deduplicate_table(table_name, unique_cols)
                total_removed += removed
            except Exception as e:
                print(f"  ⚠️  Error deduplicating {table_name}: {e}")
    
    print(f"\n✓ Total duplicates removed: {total_removed:,}")
    
    return total_removed


def compact_database(analyze_tables: bool = True):
    """
    Compact the database and rebuild indexes.
    
    Args:
        analyze_tables: Whether to run ANALYZE on all tables
    """
    db = get_db_connection()
    
    print("\n" + "=" * 70)
    print("DATABASE COMPACTION")
    print("=" * 70)
    
    # Get size before compaction
    metrics_before = get_database_metrics()
    size_before = metrics_before['file_size_mb']
    
    print(f"\nDatabase size before: {size_before:.2f} MB")
    
    # Run VACUUM to reclaim space
    print("\nRunning VACUUM...")
    db.vacuum()
    print("✓ VACUUM completed")
    
    # Run CHECKPOINT to write everything to disk
    print("\nRunning CHECKPOINT...")
    db.checkpoint()
    print("✓ CHECKPOINT completed")
    
    # Analyze tables for query optimization
    if analyze_tables:
        print("\nAnalyzing tables...")
        db.analyze()
        print("✓ ANALYZE completed")
    
    # Get size after compaction
    metrics_after = get_database_metrics()
    size_after = metrics_after['file_size_mb']
    
    size_saved = size_before - size_after
    compression_ratio = (size_before / size_after) if size_after > 0 else 1.0
    
    print("\n" + "=" * 70)
    print("COMPACTION RESULTS")
    print("=" * 70)
    print(f"Size before:  {size_before:.2f} MB")
    print(f"Size after:   {size_after:.2f} MB")
    print(f"Space saved:  {size_saved:.2f} MB ({(size_saved/size_before*100):.1f}%)")
    print(f"Compression:  {compression_ratio:.2f}x")
    print("=" * 70)
    
    return {
        'size_before_mb': size_before,
        'size_after_mb': size_after,
        'saved_mb': size_saved,
        'compression_ratio': compression_ratio
    }


def generate_report():
    """Generate a comprehensive database health report."""
    db = get_db_connection()
    
    print("\n" + "=" * 70)
    print("DATABASE HEALTH REPORT")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    metrics = get_database_metrics()
    
    print(f"\nDatabase file: {metrics['file_size_mb']:.2f} MB")
    print(f"\nTable Statistics:")
    print("-" * 70)
    print(f"{'Table Name':<40} {'Records':>15}")
    print("-" * 70)
    
    total_records = 0
    
    for table_name, stats in sorted(metrics['tables'].items()):
        rows = stats['rows']
        total_records += rows
        print(f"{table_name:<40} {rows:>15,}")
    
    print("-" * 70)
    print(f"{'TOTAL':<40} {total_records:>15,}")
    print("=" * 70)


def main():
    """Main execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compact and optimize database')
    parser.add_argument('--deduplicate', action='store_true',
                       help='Remove duplicate records before compaction')
    parser.add_argument('--no-analyze', action='store_true',
                       help='Skip ANALYZE step (faster but less optimal queries)')
    parser.add_argument('--report-only', action='store_true',
                       help='Only generate report, do not compact')
    
    args = parser.parse_args()
    
    try:
        if args.report_only:
            generate_report()
        else:
            # Deduplicate if requested
            if args.deduplicate:
                deduplicate_all_tables()
            
            # Compact database
            results = compact_database(analyze_tables=not args.no_analyze)
            
            # Generate final report
            generate_report()
            
            print("\n✅ Database compaction completed successfully")
            
            # Log results
            log_file = Path(__file__).parent.parent / 'data' / 'duckdb' / 'compaction_log.txt'
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"  Size: {results['size_before_mb']:.2f} MB → {results['size_after_mb']:.2f} MB\n")
                f.write(f"  Saved: {results['saved_mb']:.2f} MB ({(results['saved_mb']/results['size_before_mb']*100):.1f}%)\n")
                f.write(f"  Compression: {results['compression_ratio']:.2f}x\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
