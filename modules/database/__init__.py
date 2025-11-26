"""
DuckDB Database Module

Provides connection management, schema creation, and query interface for the Economic Dashboard.
"""

from .connection import get_db_connection, close_db_connection, init_database
from .queries import (
    get_fred_series,
    get_stock_ohlcv,
    get_options_data,
    get_technical_features,
    get_latest_predictions,
    get_model_performance,
    get_feature_importance,
    insert_fred_data,
    insert_stock_data,
    insert_options_data,
    insert_predictions,
    insert_technical_features,
    # SEC Data Queries
    get_sec_company_facts,
    get_sec_filings,
    get_sec_financial_statements,
    get_sec_fails_to_deliver,
    get_sec_13f_holdings,
    insert_sec_filings,
    insert_sec_company_facts,
    insert_sec_fails_to_deliver,
    get_sec_data_freshness,
)

__all__ = [
    'get_db_connection',
    'close_db_connection',
    'init_database',
    'get_fred_series',
    'get_stock_ohlcv',
    'get_options_data',
    'get_technical_features',
    'get_latest_predictions',
    'get_model_performance',
    'get_feature_importance',
    'insert_fred_data',
    'insert_stock_data',
    'insert_options_data',
    'insert_predictions',
    'insert_technical_features',
    # SEC Data Exports
    'get_sec_company_facts',
    'get_sec_filings',
    'get_sec_financial_statements',
    'get_sec_fails_to_deliver',
    'get_sec_13f_holdings',
    'insert_sec_filings',
    'insert_sec_company_facts',
    'insert_sec_fails_to_deliver',
    'get_sec_data_freshness',
]
