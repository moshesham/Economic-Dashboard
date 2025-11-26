"""
Initialize DuckDB Database

Creates all tables and indexes for the Economic Dashboard.
Run this script once before using the database.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import init_database, get_db_connection


def main():
    print("=" * 60)
    print("Economic Dashboard - Database Initialization")
    print("=" * 60)
    print()
    
    try:
        # Initialize database schema
        init_database()
        
        # Verify tables were created
        print("\nVerifying database setup...")
        db = get_db_connection()
        
        tables = db.query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            ORDER BY table_name
        """)
        
        print(f"\nFound {len(tables)} tables:")
        for table in tables['table_name']:
            count = db.get_row_count(table)
            print(f"  • {table}: {count} records")
        
        print("\n" + "=" * 60)
        print("Database initialization completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run 'python scripts/migrate_pickle_to_duckdb.py' to migrate existing data")
        print("2. Run your Streamlit app: 'streamlit run app.py'")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
