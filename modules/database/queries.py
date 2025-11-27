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


# ============================================================================
# SEC DATA QUERIES
# ============================================================================

def get_sec_company_facts(cik: str, concepts: Optional[List[str]] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve SEC company facts for a specific company
    
    Args:
        cik: Company CIK number
        concepts: Optional list of concepts to filter by
        start_date: Optional start date
        end_date: Optional end date
        
    Returns:
        DataFrame with company facts
    """
    db = get_db_connection()
    
    # Build parameterized query to prevent SQL injection
    params = [cik]
    query = "SELECT * FROM sec_company_facts WHERE cik = ?"
    
    if concepts:
        placeholders = ','.join(['?' for _ in concepts])
        query += f" AND concept IN ({placeholders})"
        params.extend(concepts)
    
    if start_date:
        query += " AND end_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND end_date <= ?"
        params.append(end_date)
    
    query += " ORDER BY end_date DESC, concept"
    
    return db.query(query, tuple(params))


def get_sec_filings(cik: Optional[str] = None, 
                    form_types: Optional[List[str]] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None,
                    limit: int = 100) -> pd.DataFrame:
    """
    Retrieve SEC filings from database
    
    Args:
        cik: Optional company CIK to filter by
        form_types: Optional list of form types (e.g., ['10-K', '10-Q'])
        start_date: Optional start date for filing_date
        end_date: Optional end date for filing_date
        limit: Maximum records to return
        
    Returns:
        DataFrame with filing records
    """
    db = get_db_connection()
    
    # Build parameterized query to prevent SQL injection
    params = []
    query = "SELECT * FROM sec_filings WHERE 1=1"
    
    if cik:
        query += " AND cik = ?"
        params.append(cik)
    
    if form_types:
        placeholders = ','.join(['?' for _ in form_types])
        query += f" AND form IN ({placeholders})"
        params.extend(form_types)
    
    if start_date:
        query += " AND filing_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND filing_date <= ?"
        params.append(end_date)
    
    # Limit is safe as it's an integer
    query += f" ORDER BY filing_date DESC LIMIT {int(limit)}"
    
    if params:
        return db.query(query, tuple(params))
    return db.query(query)


def get_sec_financial_statements(adsh: Optional[str] = None,
                                  cik: Optional[str] = None,
                                  tags: Optional[List[str]] = None,
                                  year: Optional[int] = None,
                                  quarter: Optional[int] = None) -> pd.DataFrame:
    """
    Retrieve SEC financial statement data
    
    Args:
        adsh: Optional accession number to filter by
        cik: Optional CIK (requires joining with submissions)
        tags: Optional list of XBRL tags to filter by
        year: Optional data year to filter by
        quarter: Optional data quarter to filter by
        
    Returns:
        DataFrame with financial statement data
    """
    db = get_db_connection()
    
    if cik:
        # Need to join with submissions table
        query = """
            SELECT fs.*, sub.cik, sub.name, sub.form 
            FROM sec_financial_statements fs
            JOIN sec_submissions sub ON fs.adsh = sub.adsh
            WHERE sub.cik = ?
        """
        params = [int(cik)]
    else:
        query = "SELECT * FROM sec_financial_statements WHERE 1=1"
        params = []
    
    if adsh and not cik:
        query += " AND adsh = ?"
        params.append(adsh)
    
    if tags:
        tags_list = "','".join(tags)
        query += f" AND tag IN ('{tags_list}')"
    
    if year:
        query += f" AND data_year = {year}"
    
    if quarter:
        query += f" AND data_quarter = {quarter}"
    
    query += " ORDER BY ddate DESC, tag"
    
    if params:
        return db.query(query, tuple(params))
    return db.query(query)


def get_sec_fails_to_deliver(symbol: Optional[str] = None,
                              cusip: Optional[str] = None,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None,
                              min_quantity: Optional[int] = None) -> pd.DataFrame:
    """
    Retrieve SEC fails-to-deliver data
    
    Args:
        symbol: Optional stock symbol to filter by
        cusip: Optional CUSIP to filter by
        start_date: Optional start date
        end_date: Optional end date
        min_quantity: Optional minimum quantity threshold
        
    Returns:
        DataFrame with FTD records
    """
    db = get_db_connection()
    
    # Build parameterized query to prevent SQL injection
    params = []
    query = "SELECT * FROM sec_fails_to_deliver WHERE 1=1"
    
    if symbol:
        query += " AND symbol = ?"
        params.append(symbol.upper())
    
    if cusip:
        query += " AND cusip = ?"
        params.append(cusip)
    
    if start_date:
        query += " AND settlement_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND settlement_date <= ?"
        params.append(end_date)
    
    if min_quantity:
        # Integer is safe to embed directly
        query += f" AND quantity >= {int(min_quantity)}"
    
    query += " ORDER BY settlement_date DESC, quantity DESC"
    
    if params:
        return db.query(query, tuple(params))
    return db.query(query)


def get_sec_13f_holdings(cik: Optional[str] = None,
                          cusip: Optional[str] = None,
                          filing_date: Optional[str] = None,
                          min_value: Optional[int] = None) -> pd.DataFrame:
    """
    Retrieve SEC Form 13F institutional holdings data
    
    Args:
        cik: Optional institution CIK to filter by
        cusip: Optional CUSIP to filter by
        filing_date: Optional specific filing date
        min_value: Optional minimum position value in USD
        
    Returns:
        DataFrame with 13F holdings
    """
    db = get_db_connection()
    
    # Build parameterized query to prevent SQL injection
    params = []
    query = "SELECT * FROM sec_13f_holdings WHERE 1=1"
    
    if cik:
        query += " AND cik = ?"
        params.append(cik)
    
    if cusip:
        query += " AND cusip = ?"
        params.append(cusip)
    
    if filing_date:
        query += " AND filing_date = ?"
        params.append(filing_date)
    
    if min_value:
        # Integer is safe to embed directly
        query += f" AND value_usd >= {int(min_value)}"
    
    query += " ORDER BY filing_date DESC, value_usd DESC"
    
    if params:
        return db.query(query, tuple(params))
    return db.query(query)


def insert_sec_filings(df: pd.DataFrame) -> int:
    """
    Insert SEC filing records into database
    
    Args:
        df: DataFrame with filing data
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    df = df.copy()
    if 'filing_date' in df.columns:
        df['filing_date'] = pd.to_datetime(df['filing_date'])
    if 'report_date' in df.columns:
        df['report_date'] = pd.to_datetime(df['report_date'])
    
    db.insert_df(df, 'sec_filings', if_exists='append')
    
    return len(df)


def insert_sec_company_facts(df: pd.DataFrame) -> int:
    """
    Insert SEC company facts into database
    
    Args:
        df: DataFrame with company facts
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    df = df.copy()
    if 'end_date' in df.columns:
        df['end_date'] = pd.to_datetime(df['end_date'])
    if 'filed' in df.columns:
        df['filed'] = pd.to_datetime(df['filed'])
    
    db.insert_df(df, 'sec_company_facts', if_exists='append')
    
    return len(df)


def insert_sec_fails_to_deliver(df: pd.DataFrame) -> int:
    """
    Insert SEC fails-to-deliver data into database
    
    Args:
        df: DataFrame with FTD data
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    df = df.copy()
    if 'settlement_date' in df.columns:
        df['settlement_date'] = pd.to_datetime(df['settlement_date'])
    
    db.insert_df(df, 'sec_fails_to_deliver', if_exists='append')
    
    return len(df)


def get_sec_data_freshness() -> pd.DataFrame:
    """
    Get the latest date for each SEC data source
    
    Returns:
        DataFrame showing SEC data freshness by source
    """
    db = get_db_connection()
    
    query = """
        SELECT 'sec_submissions' as source, MAX(filed) as latest_date, COUNT(*) as total_records
        FROM sec_submissions
        UNION ALL
        SELECT 'sec_financial_statements', MAX(ddate), COUNT(*)
        FROM sec_financial_statements
        UNION ALL
        SELECT 'sec_company_facts', MAX(end_date), COUNT(*)
        FROM sec_company_facts
        UNION ALL
        SELECT 'sec_filings', MAX(filing_date), COUNT(*)
        FROM sec_filings
        UNION ALL
        SELECT 'sec_fails_to_deliver', MAX(settlement_date), COUNT(*)
        FROM sec_fails_to_deliver
        UNION ALL
        SELECT 'sec_13f_holdings', MAX(filing_date), COUNT(*)
        FROM sec_13f_holdings
        ORDER BY source
    """
    
    return db.query(query)


# ============================================================================
# ICI ETF FLOWS QUERIES
# ============================================================================

def get_ici_weekly_etf_flows(fund_type: Optional[str] = None,
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve ICI weekly ETF flows data
    
    Args:
        fund_type: Optional fund type to filter by
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        DataFrame with weekly ETF flow data
    """
    db = get_db_connection()
    
    # Build parameterized query
    params = []
    query = "SELECT * FROM ici_etf_weekly_flows WHERE 1=1"
    
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


def get_ici_monthly_etf_flows(fund_category: Optional[str] = None,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve ICI monthly ETF flows data
    
    Args:
        fund_category: Optional fund category to filter by
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        DataFrame with monthly ETF flow data
    """
    db = get_db_connection()
    
    # Build parameterized query
    params = []
    query = "SELECT * FROM ici_etf_flows WHERE 1=1"
    
    if fund_category:
        query += " AND fund_category = ?"
        params.append(fund_category)
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    query += " ORDER BY date DESC"
    
    if params:
        return db.query(query, tuple(params))
    return db.query(query)


def insert_ici_weekly_flows(df: pd.DataFrame) -> int:
    """
    Insert ICI weekly ETF flows data into database
    
    Args:
        df: DataFrame with weekly flows data
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    df = df.copy()
    df['week_ending'] = pd.to_datetime(df['week_ending'])
    
    db.insert_df(df, 'ici_etf_weekly_flows', if_exists='append')
    
    return len(df)


def insert_ici_monthly_flows(df: pd.DataFrame) -> int:
    """
    Insert ICI monthly ETF flows data into database
    
    Args:
        df: DataFrame with monthly flows data
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    db.insert_df(df, 'ici_etf_flows', if_exists='append')
    
    return len(df)


# ============================================================================
# CBOE VIX QUERIES
# ============================================================================

def get_cboe_vix_history(start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Retrieve CBOE VIX historical data
    
    Args:
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        DataFrame with VIX OHLC data
    """
    db = get_db_connection()
    
    # Build parameterized query
    params = []
    query = "SELECT * FROM cboe_vix_history WHERE 1=1"
    
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


def get_latest_vix_data(days: int = 30) -> pd.DataFrame:
    """
    Get the most recent VIX data
    
    Args:
        days: Number of days to retrieve
        
    Returns:
        DataFrame with recent VIX data
    """
    db = get_db_connection()
    
    # Use integer cast for safety, as LIMIT doesn't support parameterized queries in DuckDB
    safe_days = int(days)
    query = f"""
        SELECT * FROM cboe_vix_history 
        ORDER BY date DESC 
        LIMIT {safe_days}
    """
    
    return db.query(query)


def insert_cboe_vix_data(df: pd.DataFrame) -> int:
    """
    Insert CBOE VIX data into database
    
    Args:
        df: DataFrame with VIX OHLC data
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Ensure numeric columns
    for col in ['open', 'high', 'low', 'close']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    db.insert_df(df, 'cboe_vix_history', if_exists='append')
    
    return len(df)


def insert_cboe_vix_term_structure(df: pd.DataFrame) -> int:
    """
    Insert CBOE VIX term structure data into database
    
    Args:
        df: DataFrame with VIX term structure data
        
    Returns:
        Number of records inserted
    """
    db = get_db_connection()
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    if 'expiration_date' in df.columns:
        df['expiration_date'] = pd.to_datetime(df['expiration_date'])
    
    db.insert_df(df, 'cboe_vix_term_structure', if_exists='append')
    
    return len(df)


def get_extended_data_freshness() -> pd.DataFrame:
    """
    Get the latest date for all data sources including ICI and CBOE
    
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
        UNION ALL
        SELECT 'ici_etf_weekly_flows', MAX(week_ending), COUNT(*)
        FROM ici_etf_weekly_flows
        UNION ALL
        SELECT 'ici_etf_flows', MAX(date), COUNT(*)
        FROM ici_etf_flows
        UNION ALL
        SELECT 'cboe_vix_history', MAX(date), COUNT(*)
        FROM cboe_vix_history
        ORDER BY source
    """
    
    return db.query(query)
