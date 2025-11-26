"""
Airflow DAG for CPI Inflation Tracker data refresh.

This DAG runs daily/weekly to fetch CPI basket data from FRED,
calculates inflation metrics, and stores them in DuckDB.

Schedule:
    - Daily: Quick incremental refresh of recent data
    - Weekly (Sunday): Full historical refresh with extended history

Requirements:
    - Apache Airflow 2.x
    - pip install pandas-datareader pandas duckdb
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Default arguments for all tasks
default_args = {
    'owner': 'economic-dashboard',
    'depends_on_past': False,
    'email': ['your-email@example.com'],  # Update this
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}


def run_cpi_incremental_refresh():
    """Execute incremental CPI data refresh."""
    from scripts.refresh_cpi_data import run_incremental_refresh
    
    result = run_incremental_refresh()
    if result != 0:
        raise Exception("CPI incremental refresh failed")
    
    return "CPI incremental refresh completed successfully"


def run_cpi_full_refresh():
    """Execute full CPI data refresh with extended history."""
    from scripts.refresh_cpi_data import run_full_refresh
    
    result = run_full_refresh(years_back=20)
    if result != 0:
        raise Exception("CPI full refresh failed")
    
    return "CPI full refresh completed successfully"


def validate_cpi_data_quality():
    """Validate that the refreshed CPI data meets quality standards."""
    from modules.database import get_db_connection
    from modules.database.queries import get_cpi_data_freshness, get_latest_cpi_values
    
    issues = []
    
    try:
        # Check data freshness
        freshness = get_cpi_data_freshness()
        
        if freshness.empty:
            issues.append("No CPI data found in database")
        else:
            for _, row in freshness.iterrows():
                if row['total_records'] == 0:
                    issues.append(f"{row['source']} has no records")
                elif row['latest_date'] is not None:
                    latest = row['latest_date']
                    # CPI data is released monthly, so data should be within ~45 days
                    if isinstance(latest, str):
                        latest = datetime.strptime(latest, '%Y-%m-%d')
                    if latest < datetime.now() - timedelta(days=45):
                        issues.append(f"{row['source']} data is stale (latest: {latest})")
        
        # Check latest values
        latest_values = get_latest_cpi_values()
        if latest_values.empty:
            issues.append("No latest CPI values available")
        elif len(latest_values) < 5:
            issues.append(f"Only {len(latest_values)} CPI series have data (expected >= 5)")
        
    except Exception as e:
        issues.append(f"Error validating data: {e}")
    
    if issues:
        raise Exception(f"CPI data quality validation failed: {'; '.join(issues)}")
    
    return "CPI data quality validation passed"


def generate_cpi_report():
    """Generate a summary report of CPI data."""
    from modules.database.queries import get_cpi_inflation_summary, get_cpi_category_breakdown
    
    try:
        # Get latest summary
        summary = get_cpi_inflation_summary()
        
        if not summary.empty:
            latest = summary.iloc[0]
            report = f"""
CPI Inflation Report - {latest['date']}
========================================
Headline CPI (YoY): {latest.get('headline_yoy', 'N/A'):.2f}%
Core CPI (YoY): {latest.get('core_yoy', 'N/A'):.2f}%
Food CPI (YoY): {latest.get('food_yoy', 'N/A'):.2f}%
Energy CPI (YoY): {latest.get('energy_yoy', 'N/A'):.2f}%
"""
            print(report)
            return report
        else:
            return "No summary data available"
            
    except Exception as e:
        print(f"Error generating report: {e}")
        return f"Error: {e}"


def send_cpi_notification():
    """Send notification about CPI data refresh completion."""
    # Implement your notification logic here (Slack, Email, etc.)
    print("✅ CPI data refresh completed successfully!")
    return "Notification sent"


# =============================================================================
# DAILY DAG - Incremental Refresh
# =============================================================================

with DAG(
    'cpi_inflation_tracker_daily',
    default_args=default_args,
    description='Daily CPI inflation data refresh',
    schedule_interval='0 7 * * *',  # Daily at 7 AM UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['cpi', 'inflation', 'economic-dashboard'],
) as daily_dag:
    
    # Task 1: Create necessary directories
    create_dirs = BashOperator(
        task_id='create_directories',
        bash_command='mkdir -p data/cache data/backups data/duckdb',
    )
    
    # Task 2: Run incremental CPI refresh
    refresh_cpi = PythonOperator(
        task_id='refresh_cpi_data',
        python_callable=run_cpi_incremental_refresh,
    )
    
    # Task 3: Validate data quality
    validate_data = PythonOperator(
        task_id='validate_cpi_data_quality',
        python_callable=validate_cpi_data_quality,
    )
    
    # Task 4: Generate report
    generate_report = PythonOperator(
        task_id='generate_cpi_report',
        python_callable=generate_cpi_report,
    )
    
    # Task 5: Clean old backups (keep last 30 days)
    cleanup_backups = BashOperator(
        task_id='cleanup_old_backups',
        bash_command='find data/backups -name "*cpi*.csv" -mtime +30 -delete',
    )
    
    # Task 6: Send notification
    notify = PythonOperator(
        task_id='notify_completion',
        python_callable=send_cpi_notification,
    )
    
    # Define task dependencies
    create_dirs >> refresh_cpi >> validate_data >> generate_report >> cleanup_backups >> notify


# =============================================================================
# WEEKLY DAG - Full Historical Refresh
# =============================================================================

with DAG(
    'cpi_inflation_tracker_weekly',
    default_args=default_args,
    description='Weekly full CPI historical data refresh',
    schedule_interval='0 4 * * 0',  # Sundays at 4 AM UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['cpi', 'inflation', 'economic-dashboard', 'weekly'],
) as weekly_dag:
    
    # Task 1: Create directories
    weekly_create_dirs = BashOperator(
        task_id='create_directories',
        bash_command='mkdir -p data/cache data/backups data/duckdb',
    )
    
    # Task 2: Run full CPI refresh
    weekly_refresh = PythonOperator(
        task_id='full_cpi_refresh',
        python_callable=run_cpi_full_refresh,
    )
    
    # Task 3: Validate data
    weekly_validate = PythonOperator(
        task_id='validate_cpi_data',
        python_callable=validate_cpi_data_quality,
    )
    
    # Task 4: Generate report
    weekly_report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_cpi_report,
    )
    
    # Task 5: Notify
    weekly_notify = PythonOperator(
        task_id='notify_completion',
        python_callable=send_cpi_notification,
    )
    
    # Define dependencies
    weekly_create_dirs >> weekly_refresh >> weekly_validate >> weekly_report >> weekly_notify
