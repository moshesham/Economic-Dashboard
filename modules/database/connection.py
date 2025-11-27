"""
DuckDB Connection Manager

Provides singleton connection management for the Economic Dashboard database.
"""

import duckdb
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from contextlib import contextmanager


class DatabaseConnection:
    """Singleton database connection manager"""
    
    _instance: Optional['DatabaseConnection'] = None
    _connection: Optional[duckdb.DuckDBPyConnection] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._connection is None:
            self._connect()
    
    def _connect(self):
        """Establish connection to DuckDB database"""
        db_path = Path(__file__).parent.parent.parent / 'data' / 'duckdb' / 'economic_dashboard.duckdb'
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temp directory
        temp_dir = Path(__file__).parent.parent.parent / 'data' / 'duckdb' / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        self._connection = duckdb.connect(str(db_path))
        
        # Configure DuckDB for optimal performance
        self._connection.execute("SET threads=4")
        self._connection.execute("SET memory_limit='2GB'")
        self._connection.execute(f"SET temp_directory='{temp_dir}'")
        
        # Note: DuckDB automatically optimizes queries and uses compression
        # Additional optimizations are applied at export time via COPY TO PARQUET
        
    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get the active database connection"""
        if self._connection is None:
            self._connect()
        return self._connection
    
    def query(self, sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        Execute a SELECT query and return results as DataFrame
        
        Args:
            sql: SQL query string
            params: Optional tuple of parameters for parameterized queries
            
        Returns:
            pandas DataFrame with query results
        """
        if params:
            return self.connection.execute(sql, params).df()
        return self.connection.execute(sql).df()
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> None:
        """
        Execute a non-SELECT query (INSERT, UPDATE, DELETE, CREATE, etc.)
        
        Args:
            sql: SQL statement
            params: Optional tuple of parameters for parameterized queries
        """
        if params:
            self.connection.execute(sql, params)
        else:
            self.connection.execute(sql)
        self.connection.commit()
    
    def insert_df(self, df: pd.DataFrame, table_name: str, if_exists: str = 'append') -> None:
        """
        Insert a pandas DataFrame into a table
        
        Args:
            df: DataFrame to insert
            table_name: Name of the target table
            if_exists: What to do if table exists ('append', 'replace', 'fail')
        """
        # Register the DataFrame as a temporary view
        self.connection.register('temp_df', df)
        
        if if_exists == 'replace':
            self.execute(f"DELETE FROM {table_name}")
        
        # Get only the columns that exist in both the DataFrame and the table
        # This avoids issues with auto-generated columns like created_at
        columns = ', '.join(df.columns)
        
        # Insert from the temporary view, specifying only the columns we have
        self.execute(f"INSERT INTO {table_name} ({columns}) SELECT {columns} FROM temp_df")
        
        # Unregister the temporary view
        self.connection.unregister('temp_df')
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        result = self.query(
            "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = ?",
            (table_name,)
        )
        return result['count'].iloc[0] > 0
    
    def get_table_info(self, table_name: str) -> pd.DataFrame:
        """Get column information for a table"""
        return self.query(f"DESCRIBE {table_name}")
    
    def get_row_count(self, table_name: str) -> int:
        """Get the number of rows in a table"""
        result = self.query(f"SELECT COUNT(*) as count FROM {table_name}")
        return int(result['count'].iloc[0])
    
    def vacuum(self) -> None:
        """Reclaim space from deleted rows and optimize storage"""
        self.execute("VACUUM")
    
    def checkpoint(self) -> None:
        """Write all changes to disk and compact the database"""
        self.execute("CHECKPOINT")
    
    def analyze(self, table_name: Optional[str] = None) -> None:
        """Update table statistics for query optimization"""
        if table_name:
            self.execute(f"ANALYZE {table_name}")
        else:
            # Analyze all tables
            tables = self.query("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
            """)
            for table in tables['table_name']:
                self.execute(f"ANALYZE {table}")
    
    def get_database_size(self) -> dict:
        """Get database file size and table sizes"""
        db_path = Path(__file__).parent.parent.parent / 'data' / 'duckdb' / 'economic_dashboard.duckdb'
        
        result = {
            'database_file_mb': db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0,
            'tables': {}
        }
        
        # Get table sizes
        tables = self.query("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """)
        
        for table_name in tables['table_name']:
            result['tables'][table_name] = {
                'rows': self.get_row_count(table_name)
            }
        
        return result
    
    def close(self):
        """Close the database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None


# Module-level functions for convenience
_db = DatabaseConnection()


def get_db_connection() -> DatabaseConnection:
    """Get the singleton database connection"""
    return _db


def close_db_connection():
    """Close the database connection"""
    _db.close()


def init_database():
    """Initialize the database schema"""
    from .schema import create_all_tables
    create_all_tables()


@contextmanager
def db_transaction():
    """Context manager for database transactions"""
    conn = get_db_connection()
    try:
        yield conn
        conn.connection.commit()
    except Exception as e:
        conn.connection.rollback()
        raise e
