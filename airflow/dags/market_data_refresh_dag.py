"""
Airflow DAG for ICI ETF Flows and CBOE VIX data refresh.

This DAG runs daily to fetch:
- ICI ETF flows data from ici.org
- CBOE VIX historical data from cboe.com

The data is stored in DuckDB for use by the Economic Dashboard.

Requirements:
    - Apache Airflow 2.x
    - pip install pandas requests
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Default arguments - email configured via environment variable
default_args = {
    'owner': 'economic-dashboard',
    'depends_on_past': False,
    'email': os.environ.get('AIRFLOW_ALERT_EMAIL', '').split(',') or [],
    'email_on_failure': bool(os.environ.get('AIRFLOW_ALERT_EMAIL')),
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}


def refresh_ici_etf_data():
    """Execute the ICI ETF data refresh."""
    from modules.ici_etf_data import refresh_ici_etf_data as ici_refresh
    
    result = ici_refresh()
    
    if result['weekly_records'] == 0 and result['monthly_records'] == 0:
        raise Exception("ICI ETF data refresh failed: No data fetched")
    
    return f"ICI ETF refresh completed: {result['weekly_records']} weekly, {result['monthly_records']} monthly records"


def refresh_cboe_vix_data():
    """Execute the CBOE VIX data refresh."""
    from modules.cboe_vix_data import refresh_cboe_vix_data as vix_refresh
    
    result = vix_refresh()
    
    if result['vix_records'] == 0:
        raise Exception("CBOE VIX data refresh failed: No data fetched")
    
    return f"CBOE VIX refresh completed: {result['vix_records']} records"


def validate_market_data_quality():
    """Validate that the refreshed market data meets quality standards."""
    from modules.database.queries import get_extended_data_freshness
    
    freshness = get_extended_data_freshness()
    issues = []
    
    # Check ICI ETF weekly flows
    ici_weekly = freshness[freshness['source'] == 'ici_etf_weekly_flows']
    if ici_weekly.empty or ici_weekly['total_records'].iloc[0] == 0:
        issues.append("ICI weekly ETF flows table is empty")
    elif ici_weekly['latest_date'].iloc[0] is not None:
        latest = ici_weekly['latest_date'].iloc[0]
        if isinstance(latest, str):
            latest = datetime.strptime(latest, '%Y-%m-%d')
        if latest < datetime.now() - timedelta(days=14):
            issues.append(f"ICI weekly data is stale (latest: {latest})")
    
    # Check CBOE VIX data
    vix_data = freshness[freshness['source'] == 'cboe_vix_history']
    if vix_data.empty or vix_data['total_records'].iloc[0] == 0:
        issues.append("CBOE VIX history table is empty")
    elif vix_data['latest_date'].iloc[0] is not None:
        latest = vix_data['latest_date'].iloc[0]
        if isinstance(latest, str):
            latest = datetime.strptime(latest, '%Y-%m-%d')
        if latest < datetime.now() - timedelta(days=7):
            issues.append(f"CBOE VIX data is stale (latest: {latest})")
    
    if issues:
        raise Exception(f"Market data quality validation failed: {'; '.join(issues)}")
    
    return "Market data quality validation passed"


def send_market_data_notification():
    """Send notification about successful market data refresh."""
    # Implement your notification logic here
    # Examples: Slack, Email, Teams, etc.
    print("✅ ICI ETF and CBOE VIX data refresh completed successfully!")
    return "Notification sent"


# Define the DAG for daily market data refresh
with DAG(
    'market_data_refresh_dag',
    default_args=default_args,
    description='Daily refresh of ICI ETF flows and CBOE VIX data',
    schedule_interval='0 7 * * 1-5',  # Weekdays at 7 AM UTC (after market close)
    start_date=days_ago(1),
    catchup=False,
    tags=['economic-dashboard', 'market-data', 'etf-flows', 'vix'],
) as dag:
    
    # Task 1: Initialize database schema
    init_schema = PythonOperator(
        task_id='init_database_schema',
        python_callable=lambda: __import__('modules.database.connection', fromlist=['init_database']).init_database(),
    )
    
    # Task 2: Refresh ICI ETF flows data
    refresh_ici = PythonOperator(
        task_id='refresh_ici_etf_flows',
        python_callable=refresh_ici_etf_data,
    )
    
    # Task 3: Refresh CBOE VIX data
    refresh_vix = PythonOperator(
        task_id='refresh_cboe_vix_data',
        python_callable=refresh_cboe_vix_data,
    )
    
    # Task 4: Validate data quality
    validate_data = PythonOperator(
        task_id='validate_market_data_quality',
        python_callable=validate_market_data_quality,
    )
    
    # Task 5: Send success notification
    notify_success = PythonOperator(
        task_id='notify_market_data_success',
        python_callable=send_market_data_notification,
    )
    
    # Define task dependencies
    # Initialize schema first, then fetch data in parallel, validate, then notify
    init_schema >> [refresh_ici, refresh_vix] >> validate_data >> notify_success


# Optional: Create a standalone DAG for ICI ETF data only
with DAG(
    'ici_etf_flows_refresh',
    default_args=default_args,
    description='Standalone refresh of ICI ETF flows data',
    schedule_interval='0 8 * * 3',  # Weekly on Wednesday at 8 AM UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['economic-dashboard', 'etf-flows', 'ici'],
) as ici_dag:
    
    ici_refresh_task = PythonOperator(
        task_id='refresh_ici_etf_flows',
        python_callable=refresh_ici_etf_data,
    )


# Optional: Create a standalone DAG for CBOE VIX data only
with DAG(
    'cboe_vix_refresh',
    default_args=default_args,
    description='Standalone refresh of CBOE VIX historical data',
    schedule_interval='0 22 * * 1-5',  # Weekdays at 10 PM UTC (after market close)
    start_date=days_ago(1),
    catchup=False,
    tags=['economic-dashboard', 'vix', 'cboe'],
) as vix_dag:
    
    vix_refresh_task = PythonOperator(
        task_id='refresh_cboe_vix_data',
        python_callable=refresh_cboe_vix_data,
    )
