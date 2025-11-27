"""
Create optimized database snapshots with partitioned Parquet exports.

This script creates:
1. Daily snapshots of hot tables (frequently queried, <90 days data)
2. Parquet archives of cold tables (historical data >90 days)
3. Incremental exports (only new/changed data)
4. Compressed snapshots with ZSTD compression
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import get_db_connection

# Paths
DB_PATH = Path("data/duckdb/economic_dashboard.duckdb")
SNAPSHOT_DIR = Path("data/duckdb/snapshots")
MONTHLY_DIR = Path("data/duckdb/monthly")
PARQUET_DIR = Path("data/duckdb/archives")

# Tables that are frequently queried (hot data)
HOT_TABLES = [
    'fred_data',
    'yfinance_ohlcv',
    'market_indicators',
    'cboe_vix_history',
    'ici_etf_weekly_flows',
]

# Tables with large historical data (cold data - best for Parquet)
COLD_TABLES = [
    'sec_submissions',
    'sec_financial_statements',
    'sec_company_facts',
    'sec_filings',
    'options_data',
    'technical_features',
    'derived_features',
]


def create_full_snapshot(snapshot_type: str = 'daily'):
    """
    Create a full database snapshot.
    
    Args:
        snapshot_type: 'daily' or 'monthly'
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    
    # Create directories
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    MONTHLY_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now()
    date_str = timestamp.strftime('%Y%m%d')
    
    if snapshot_type == 'daily':
        output_dir = SNAPSHOT_DIR
        snapshot_file = output_dir / f"economic_dashboard_{date_str}.duckdb"
    else:  # monthly
        output_dir = MONTHLY_DIR
        snapshot_file = output_dir / f"economic_dashboard_{timestamp.strftime('%Y%m')}.duckdb"
    
    print(f"Creating {snapshot_type} snapshot: {snapshot_file.name}")
    
    # Copy database file
    shutil.copy2(DB_PATH, snapshot_file)
    
    # Also copy WAL file if it exists
    wal_file = Path(str(DB_PATH) + ".wal")
    if wal_file.exists():
        shutil.copy2(wal_file, Path(str(snapshot_file) + ".wal"))
    
    file_size_mb = snapshot_file.stat().st_size / (1024 * 1024)
    print(f"✓ Snapshot created: {snapshot_file} ({file_size_mb:.2f} MB)")
    
    return snapshot_file


def export_table_to_parquet(table_name: str, date_column: str = 'date',
                            days_to_export: int = None, incremental: bool = False):
    """
    Export table to compressed Parquet file.
    
    Args:
        table_name: Name of table to export
        date_column: Column to use for date filtering
        days_to_export: If specified, only export recent N days
        incremental: If True, only export data since last export
    """
    db = get_db_connection()
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Build export query
    if days_to_export:
        cutoff_date = datetime.now() - timedelta(days=days_to_export)
        where_clause = f"WHERE {date_column} >= DATE '{cutoff_date.strftime('%Y-%m-%d')}'"
        suffix = f"_recent_{days_to_export}d"
    elif incremental:
        # Find last export date
        existing_files = list(PARQUET_DIR.glob(f"{table_name}_*.parquet"))
        if existing_files:
            # Get most recent file date from filename
            last_export_date = max([
                datetime.strptime(f.stem.split('_')[-1], '%Y%m%d')
                for f in existing_files
                if f.stem.split('_')[-1].isdigit()
            ])
            where_clause = f"WHERE {date_column} > DATE '{last_export_date.strftime('%Y-%m-%d')}'"
            suffix = f"_incremental"
        else:
            where_clause = ""
            suffix = "_full"
    else:
        where_clause = ""
        suffix = "_full"
    
    parquet_file = PARQUET_DIR / f"{table_name}_{date_str}{suffix}.parquet"
    
    # Check if table has data
    count_query = f"SELECT COUNT(*) as count FROM {table_name} {where_clause}"
    count_result = db.query(count_query)
    record_count = int(count_result['count'].iloc[0])
    
    if record_count == 0:
        print(f"  • Skipping {table_name} (no data to export)")
        return None
    
    # DuckDB native Parquet export with maximum compression
    export_query = f"""
        COPY (
            SELECT * FROM {table_name}
            {where_clause}
        ) TO '{parquet_file}' (
            FORMAT PARQUET, 
            COMPRESSION ZSTD,
            ROW_GROUP_SIZE 100000
        )
    """
    
    db.execute(export_query)
    
    file_size_mb = parquet_file.stat().st_size / (1024 * 1024)
    print(f"  ✓ {table_name}: {record_count:,} records → {parquet_file.name} ({file_size_mb:.2f} MB)")
    
    return parquet_file


def create_partitioned_snapshot():
    """
    Create optimized snapshot using partitioning strategy:
    - Hot tables: Full snapshot
    - Cold tables: Parquet archives
    """
    print("=" * 70)
    print("CREATING PARTITIONED SNAPSHOT")
    print("=" * 70)
    
    db = get_db_connection()
    timestamp = datetime.now()
    
    # Get current database size
    db_size_before = db.get_database_size()
    print(f"\nCurrent database size: {db_size_before['database_file_mb']:.2f} MB")
    
    # Export hot tables (recent data only - last 90 days)
    print("\n📊 Exporting HOT tables (last 90 days)...")
    hot_exports = []
    
    for table in HOT_TABLES:
        if db.table_exists(table):
            result = export_table_to_parquet(table, date_column='date', days_to_export=90)
            if result:
                hot_exports.append(result)
    
    # Export cold tables (incremental - only new data)
    print("\n❄️  Exporting COLD tables (incremental)...")
    cold_exports = []
    
    for table in COLD_TABLES:
        if db.table_exists(table):
            # Determine date column
            date_col = 'date'
            if 'sec_' in table:
                if 'submissions' in table:
                    date_col = 'filed'
                elif 'financial_statements' in table:
                    date_col = 'ddate'
                elif 'filings' in table:
                    date_col = 'filing_date'
                elif 'company_facts' in table:
                    date_col = 'end_date'
            
            result = export_table_to_parquet(table, date_column=date_col, incremental=True)
            if result:
                cold_exports.append(result)
    
    # Calculate total exported size
    total_size_mb = sum([f.stat().st_size / (1024 * 1024) for f in hot_exports + cold_exports])
    
    print("\n" + "=" * 70)
    print("SNAPSHOT SUMMARY")
    print("=" * 70)
    print(f"Hot table exports: {len(hot_exports)}")
    print(f"Cold table exports: {len(cold_exports)}")
    print(f"Total Parquet size: {total_size_mb:.2f} MB")
    print(f"Compression ratio: {(db_size_before['database_file_mb'] / total_size_mb):.1f}x")
    print("=" * 70)
    
    return {
        'hot_exports': hot_exports,
        'cold_exports': cold_exports,
        'total_size_mb': total_size_mb,
        'timestamp': timestamp
    }


def cleanup_old_snapshots(retention_days: int = 14):
    """
    Remove snapshots older than retention period.
    
    Args:
        retention_days: Number of days to keep daily snapshots
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0
    
    print(f"\nCleaning up snapshots older than {retention_days} days...")
    
    for snapshot_file in SNAPSHOT_DIR.glob("economic_dashboard_*.duckdb"):
        # Extract date from filename (format: economic_dashboard_YYYYMMDD.duckdb)
        try:
            date_str = snapshot_file.stem.split('_')[-1]  # Gets YYYYMMDD
            file_date = datetime.strptime(date_str, '%Y%m%d')
            
            if file_date < cutoff_date:
                print(f"  Deleting old snapshot: {snapshot_file.name}")
                snapshot_file.unlink()
                
                # Also delete WAL file if exists
                wal_file = Path(str(snapshot_file) + ".wal")
                if wal_file.exists():
                    wal_file.unlink()
                
                deleted_count += 1
        except (ValueError, IndexError):
            print(f"  ⚠️  Could not parse date from {snapshot_file.name}")
    
    if deleted_count > 0:
        print(f"✓ Cleaned up {deleted_count} old snapshots (>{retention_days} days)")
    else:
        print(f"✓ No snapshots older than {retention_days} days")


def cleanup_old_parquet_exports(retention_days: int = 90):
    """
    Remove old Parquet exports (keep recent incremental, delete old full exports).
    
    Args:
        retention_days: Days to keep Parquet exports
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0
    
    print(f"\nCleaning up Parquet exports older than {retention_days} days...")
    
    for parquet_file in PARQUET_DIR.glob("*.parquet"):
        try:
            # Extract date from filename
            parts = parquet_file.stem.split('_')
            date_str = parts[-1] if parts[-1].isdigit() else parts[-2]
            file_date = datetime.strptime(date_str, '%Y%m%d')
            
            if file_date < cutoff_date:
                # Keep full exports, delete incrementals
                if 'incremental' in parquet_file.stem or 'recent' in parquet_file.stem:
                    print(f"  Deleting old export: {parquet_file.name}")
                    parquet_file.unlink()
                    deleted_count += 1
        except (ValueError, IndexError):
            continue
    
    if deleted_count > 0:
        print(f"✓ Cleaned up {deleted_count} old Parquet exports")
    else:
        print(f"✓ No old Parquet exports to clean")


def main():
    """Main execution for snapshot workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create database snapshot')
    parser.add_argument('--type', choices=['daily', 'monthly', 'partitioned'], default='partitioned',
                       help='Type of snapshot to create')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up old snapshots')
    parser.add_argument('--retention-days', type=int, default=14,
                       help='Days to retain snapshots (default: 14)')
    
    args = parser.parse_args()
    
    try:
        if args.type == 'partitioned':
            # Optimized partitioned snapshot
            create_partitioned_snapshot()
        else:
            # Traditional full snapshot
            create_full_snapshot(args.type)
        
        # Cleanup old snapshots
        if args.cleanup:
            cleanup_old_snapshots(args.retention_days)
            cleanup_old_parquet_exports(retention_days=90)
        
        print("\n✅ Snapshot workflow completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error creating snapshot: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
