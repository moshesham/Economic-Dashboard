"""
Database Query Functions

Pre-built queries for common data access patterns.
"""

import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .connection import get_db_connection


# ============================================================================
# READ QUERIES
# ============================================================================

def get_fred_series(series_ids: List[str], start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve FRED economic data for specified series
    
    Args:
        series_ids: List of FRED series IDs
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        DataFrame with columns: series_id, date, value
    """
    db = get_db_connection()
    
    series_list = "','".join(series_ids)
    query = f"SELECT * FROM fred_data WHERE series_id IN ('{series_list}')"
    
    if start_date:
        query += f" AND date >= '{start_date}'"
    if end_date:
        query += f" AND date <= '{end_date}'"
    
    query += " ORDER BY series_id, date"
    
    return db.query(query)


def get_stock_ohlcv(tickers: Optional[List[str]] = None, ticker: Optional[str] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    limit: Optional[int] = None) -> pd.DataFrame:
    """
    Retrieve stock OHLCV data for specified ticker(s)
    
    Args:
        tickers: List of stock tickers (optional if ticker provided)
        ticker: Single stock ticker (optional if tickers provided)
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        limit: Optional limit on number of records
        
    Returns:
        DataFrame with OHLCV data, indexed by date if single ticker
    """
    db = get_db_connection()
    
    # Handle single ticker vs list
    if ticker:
        ticker_list = ticker
        query = f"SELECT * FROM yfinance_ohlcv WHERE ticker = '{ticker}'"
    elif tickers:
        ticker_list = "','".join(tickers)
        query = f"SELECT * FROM yfinance_ohlcv WHERE ticker IN ('{ticker_list}')"
    else:
        raise ValueError("Either 'ticker' or 'tickers' must be provided")
    
    if start_date:
        query += f" AND date >= '{start_date}'"
    if end_date:
        query += f" AND date <= '{end_date}'"
    
    query += " ORDER BY ticker, date"
    
    if limit:
        query += f" LIMIT {limit}"
    
    df = db.query(query)
    
    # If single ticker, set date as index
    if ticker and not df.empty:
        df = df.set_index('date')
    
    return df


def get_options_data(ticker: str, start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve options data for a ticker
    
    Args:
        ticker: Stock ticker
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        DataFrame with options metrics
    """
    db = get_db_connection()
    
    query = f"SELECT * FROM options_data WHERE ticker = '{ticker}'"
    
    if start_date:
        query += f" AND date >= '{start_date}'"
    if end_date:
        query += f" AND date <= '{end_date}'"
    
    query += " ORDER BY date, expiration_date"
    
    return db.query(query)


def get_technical_features(ticker: str, start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve technical analysis features for a ticker
    
    Args:
        ticker: Stock ticker
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        DataFrame with technical indicators
    """
    db = get_db_connection()
    
    query = f"SELECT * FROM technical_features WHERE ticker = '{ticker}'"
    
    if start_date:
        query += f" AND date >= '{start_date}'"
    if end_date:
        query += f" AND date <= '{end_date}'"
    
    query += " ORDER BY date"
    
    return db.query(query)


def get_latest_predictions(ticker: Optional[str] = None, 
                          model_version: Optional[str] = None,
                          limit: int = 100) -> pd.DataFrame:
    """
    Retrieve latest ML predictions
    
    Args:
        ticker: Optional ticker to filter by
        model_version: Optional model version to filter by
        limit: Maximum number of records to return
        
    Returns:
        DataFrame with predictions
    """
    db = get_db_connection()
    
    query = "SELECT * FROM ml_predictions WHERE 1=1"
    
    if ticker:
        query += f" AND ticker = '{ticker}'"
    if model_version:
        query += f" AND model_version = '{model_version}'"
    
    query += f" ORDER BY prediction_date DESC LIMIT {limit}"
    
    return db.query(query)


def get_model_performance(model_version: Optional[str] = None,
                         start_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve model performance metrics
    
    Args:
        model_version: Optional model version to filter by
        start_date: Optional start date for evaluation
        
    Returns:
        DataFrame with performance metrics
    """
    db = get_db_connection()
    
    query = "SELECT * FROM model_performance WHERE 1=1"
    
    if model_version:
        query += f" AND model_version = '{model_version}'"
    if start_date:
        query += f" AND evaluation_date >= '{start_date}'"
    
    query += " ORDER BY evaluation_date DESC"
    
    return db.query(query)


def get_feature_importance(ticker: str, prediction_date: str,
                          model_version: str) -> Dict[str, float]:
    """
    Get top feature importances for a specific prediction
    
    Args:
        ticker: Stock ticker
        prediction_date: Date of prediction
        model_version: Model version
        
    Returns:
        Dictionary of feature names and importance scores
    """
    db = get_db_connection()
    
    query = f"""
        SELECT top_features 
        FROM ml_predictions 
        WHERE ticker = '{ticker}' 
          AND prediction_date = '{prediction_date}'
          AND model_version = '{model_version}'
    """
    
    result = db.query(query)
    
    if len(result) > 0 and result['top_features'].iloc[0]:
        import json
        return json.loads(result['top_features'].iloc[0])
    
    return {}


def get_data_freshness() -> pd.DataFrame:
    """
    Get the latest date for each data source
    
    Returns:
        DataFrame showing data freshness by source
    """
    db = get_db_connection()
    
    query = """
        SELECT 'fred_data' as source, MAX(date) as latest_date, COUNT(*) as total_records
        FROM fred_data
        UNION ALL
        SELECT 'yfinance_ohlcv', MAX(date), COUNT(*)
        FROM yfinance_ohlcv
        UNION ALL
        SELECT 'options_data', MAX(date), COUNT(*)
        FROM options_data
        UNION ALL
        SELECT 'technical_features', MAX(date), COUNT(*)
        FROM technical_features
        UNION ALL
        SELECT 'ml_predictions', MAX(prediction_date), COUNT(*)
        FROM ml_predictions
        ORDER BY source
    """
    
    return db.query(query)


# ============================================================================
# WRITE QUERIES
# ============================================================================

def insert_fred_data(df: pd.DataFrame) -> int:
    """
    Insert FRED data into database
    
    Args:
        df: DataFrame with columns [series_id, date, value]
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    # Ensure correct dtypes
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    
    db.insert_df(df[['series_id', 'date', 'value']], 'fred_data', if_exists='append')
    
    return len(df)


def insert_stock_data(df: pd.DataFrame) -> int:
    """
    Insert stock OHLCV data into database
    
    Args:
        df: DataFrame with columns [ticker, date, open, high, low, close, volume, adj_close]
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    # Ensure correct dtypes
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    numeric_cols = ['open', 'high', 'low', 'close', 'adj_close']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    if 'volume' in df.columns:
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
    
    db.insert_df(df, 'yfinance_ohlcv', if_exists='append')
    
    return len(df)


def insert_options_data(df: pd.DataFrame) -> int:
    """
    Insert options data into database
    
    Args:
        df: DataFrame with options metrics
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    # Ensure correct dtypes
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['expiration_date'] = pd.to_datetime(df['expiration_date'])
    
    db.insert_df(df, 'options_data', if_exists='append')
    
    return len(df)


def insert_predictions(df: pd.DataFrame) -> int:
    """
    Insert ML predictions into database
    
    Args:
        df: DataFrame with prediction data
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    # Ensure correct dtypes
    df = df.copy()
    df['prediction_date'] = pd.to_datetime(df['prediction_date'])
    df['target_date'] = pd.to_datetime(df['target_date'])
    
    # Convert top_features dict to JSON string if needed
    if 'top_features' in df.columns:
        import json
        df['top_features'] = df['top_features'].apply(
            lambda x: json.dumps(x) if isinstance(x, dict) else x
        )
    
    db.insert_df(df, 'ml_predictions', if_exists='append')
    
    return len(df)


def log_data_refresh(data_source: str, records_processed: int, 
                     status: str = 'completed', error_message: Optional[str] = None):
    """
    Log a data refresh operation
    
    Args:
        data_source: Name of the data source
        records_processed: Number of records processed
        status: Status of the refresh ('running', 'completed', 'failed')
        error_message: Optional error message if failed
    """
    db = get_db_connection()
    
    query = """
        INSERT INTO data_refresh_log 
        (refresh_id, data_source, refresh_start, refresh_end, status, records_processed, error_message)
        VALUES (
            nextval('refresh_id_seq'),
            ?, 
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            ?,
            ?,
            ?
        )
    """
    
    db.execute(query, (data_source, status, records_processed, error_message))


# ============================================================================
# ANALYTICS QUERIES
# ============================================================================

def get_ml_features_for_date(ticker: str, as_of_date: str) -> pd.DataFrame:
    """
    Get all features needed for ML prediction on a specific date
    
    Args:
        ticker: Stock ticker
        as_of_date: Date to get features for
        
    Returns:
        DataFrame with all features combined
    """
    db = get_db_connection()
    
    query = f"""
        SELECT 
            o.*,
            t.*,
            d.*,
            m.*
        FROM yfinance_ohlcv o
        LEFT JOIN technical_features t 
            ON o.ticker = t.ticker AND o.date = t.date
        LEFT JOIN derived_features d
            ON o.ticker = d.ticker AND o.date = d.date
        LEFT JOIN market_indicators m
            ON o.date = m.date
        WHERE o.ticker = '{ticker}'
          AND o.date = '{as_of_date}'
    """
    
    return db.query(query)


def get_prediction_accuracy(model_version: str, days_back: int = 30) -> Dict[str, float]:
    """
    Calculate prediction accuracy for recent predictions
    
    Args:
        model_version: Model version to evaluate
        days_back: Number of days to look back
        
    Returns:
        Dictionary with accuracy metrics
    """
    db = get_db_connection()
    
    cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    query = f"""
        SELECT 
            COUNT(*) as total_predictions,
            SUM(CASE 
                WHEN p.predicted_direction = t.target_direction THEN 1 
                ELSE 0 
            END) as correct_predictions,
            AVG(CASE 
                WHEN p.predicted_direction = t.target_direction THEN 1.0 
                ELSE 0.0 
            END) as accuracy
        FROM ml_predictions p
        JOIN ml_training_data t
            ON p.ticker = t.ticker 
            AND p.target_date = t.target_date
        WHERE p.model_version = '{model_version}'
          AND p.prediction_date >= '{cutoff_date}'
          AND t.target_direction IS NOT NULL
    """
    
    result = db.query(query)
    
    if len(result) > 0:
        return {
            'total_predictions': int(result['total_predictions'].iloc[0]),
            'correct_predictions': int(result['correct_predictions'].iloc[0]),
            'accuracy': float(result['accuracy'].iloc[0])
        }
    
    return {'total_predictions': 0, 'correct_predictions': 0, 'accuracy': 0.0}


def insert_technical_features(df: pd.DataFrame) -> int:
    """
    Insert technical features data into database
    
    Args:
        df: DataFrame with technical features
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    # Ensure correct dtypes
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    db.insert_df(df, 'technical_features', if_exists='append')
    
    return len(df)
