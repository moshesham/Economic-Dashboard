"""
Feature Pipeline

Orchestrates the entire feature engineering process:
1. Technical indicators calculation
2. Options metrics calculation
3. Derived features calculation
4. Data validation and quality checks
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from modules.features.technical_indicators import TechnicalIndicatorCalculator
from modules.features.options_metrics import OptionsMetricsCalculator
from modules.features.derived_features import DerivedFeaturesCalculator
from modules.database import get_db_connection


class FeaturePipeline:
    """End-to-end feature engineering pipeline."""
    
    def __init__(self):
        self.tech_calc = TechnicalIndicatorCalculator()
        self.options_calc = OptionsMetricsCalculator()
        self.derived_calc = DerivedFeaturesCalculator()
        self.db = get_db_connection()
    
    def run_full_pipeline(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_options: bool = True
    ) -> dict:
        """
        Run the complete feature engineering pipeline for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            include_options: Whether to fetch options data (slower)
            
        Returns:
            Dictionary with status and results
        """
        results = {
            'ticker': ticker,
            'start_date': start_date,
            'end_date': end_date,
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'steps': {}
        }
        
        try:
            # Step 1: Calculate technical indicators
            print(f"\n📊 Step 1: Calculating technical indicators for {ticker}...")
            tech_features = self.tech_calc.calculate_and_store(ticker, start_date, end_date)
            results['steps']['technical'] = {
                'status': 'success',
                'records': len(tech_features)
            }
            print(f"  ✅ {len(tech_features)} technical indicator records")
            
            # Step 2: Calculate options metrics (if requested)
            if include_options:
                print(f"\n📈 Step 2: Calculating options metrics for {ticker}...")
                try:
                    options_features = self.options_calc.calculate_and_store(ticker, end_date)
                    results['steps']['options'] = {
                        'status': 'success',
                        'records': len(options_features)
                    }
                    print(f"  ✅ {len(options_features)} options metric records")
                except Exception as e:
                    results['steps']['options'] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    print(f"  ⚠️  Options data not available: {e}")
            else:
                results['steps']['options'] = {'status': 'skipped'}
            
            # Step 3: Calculate derived features
            print(f"\n🔀 Step 3: Calculating derived features for {ticker}...")
            derived_features = self.derived_calc.calculate_and_store(ticker, start_date, end_date)
            results['steps']['derived'] = {
                'status': 'success',
                'records': len(derived_features)
            }
            print(f"  ✅ {len(derived_features)} derived feature records")
            
            # Step 4: Data quality check
            print(f"\n✓ Step 4: Running data quality checks...")
            quality_report = self.validate_features(ticker, start_date, end_date)
            results['quality'] = quality_report
            
            if quality_report['issues']:
                print(f"  ⚠️  Found {len(quality_report['issues'])} data quality issues")
                for issue in quality_report['issues']:
                    print(f"    - {issue}")
            else:
                print(f"  ✅ No data quality issues found")
            
            print(f"\n🎉 Pipeline complete for {ticker}")
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
            print(f"\n❌ Pipeline failed for {ticker}: {e}")
        
        return results
    
    def run_batch_pipeline(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_options: bool = True
    ) -> dict:
        """
        Run the feature pipeline for multiple tickers.
        
        Args:
            tickers: List of stock ticker symbols
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            include_options: Whether to fetch options data
            
        Returns:
            Dictionary with results for each ticker
        """
        results = {}
        success_count = 0
        
        print(f"\n{'='*60}")
        print(f"RUNNING FEATURE PIPELINE FOR {len(tickers)} TICKERS")
        print(f"{'='*60}")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Processing {ticker}...")
            
            result = self.run_full_pipeline(ticker, start_date, end_date, include_options)
            results[ticker] = result
            
            if result['status'] == 'success':
                success_count += 1
        
        # Summary
        print(f"\n{'='*60}")
        print(f"PIPELINE SUMMARY")
        print(f"{'='*60}")
        print(f"Total tickers: {len(tickers)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {len(tickers) - success_count}")
        
        return results
    
    def validate_features(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        Validate feature data quality.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            Dictionary with validation results
        """
        issues = []
        
        # Check technical features
        tech_sql = """
            SELECT COUNT(*) as count,
                   COUNT(DISTINCT date) as dates,
                   SUM(CASE WHEN rsi_14 IS NULL THEN 1 ELSE 0 END) as null_rsi,
                   SUM(CASE WHEN macd IS NULL THEN 1 ELSE 0 END) as null_macd
            FROM technical_features
            WHERE ticker = ?
        """
        
        params = [ticker]
        if start_date:
            tech_sql += " AND date >= ?"
            params.append(start_date)
        if end_date:
            tech_sql += " AND date <= ?"
            params.append(end_date)
        
        tech_result = self.db.query(tech_sql, tuple(params))
        
        if tech_result['count'].iloc[0] == 0:
            issues.append("No technical features found")
        elif tech_result['null_rsi'].iloc[0] > tech_result['count'].iloc[0] * 0.1:
            issues.append(f"High null rate in RSI: {tech_result['null_rsi'].iloc[0]} records")
        
        # Check for duplicate dates
        dup_sql = """
            SELECT date, COUNT(*) as count
            FROM technical_features
            WHERE ticker = ?
            GROUP BY date
            HAVING COUNT(*) > 1
        """
        
        duplicates = self.db.query(dup_sql, (ticker,))
        if not duplicates.empty:
            issues.append(f"{len(duplicates)} duplicate dates found in technical features")
        
        # Check date range continuity
        if start_date and end_date:
            expected_days = (
                pd.to_datetime(end_date) - pd.to_datetime(start_date)
            ).days
            actual_dates = tech_result['dates'].iloc[0]
            
            # Allow for weekends/holidays (roughly 70% of calendar days)
            if actual_dates < expected_days * 0.5:
                issues.append(
                    f"Date range coverage low: {actual_dates} dates "
                    f"vs {expected_days} calendar days"
                )
        
        return {
            'ticker': ticker,
            'total_records': int(tech_result['count'].iloc[0]),
            'unique_dates': int(tech_result['dates'].iloc[0]),
            'null_counts': {
                'rsi_14': int(tech_result['null_rsi'].iloc[0]),
                'macd': int(tech_result['null_macd'].iloc[0])
            },
            'duplicates': len(duplicates),
            'issues': issues,
            'status': 'pass' if not issues else 'warning'
        }
    
    def backfill_features(
        self,
        ticker: str,
        days_back: int = 365
    ) -> dict:
        """
        Backfill features for historical data.
        
        Args:
            ticker: Stock ticker symbol
            days_back: Number of days to backfill
            
        Returns:
            Pipeline execution results
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        print(f"\n🔄 Backfilling features for {ticker}")
        print(f"  Date range: {start_date} to {end_date}")
        
        return self.run_full_pipeline(ticker, start_date, end_date, include_options=False)
    
    def get_feature_summary(self, ticker: str) -> pd.DataFrame:
        """
        Get a summary of available features for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            DataFrame with feature summary
        """
        summary_sql = """
            SELECT 
                'technical' as feature_type,
                COUNT(*) as record_count,
                MIN(date) as min_date,
                MAX(date) as max_date,
                COUNT(DISTINCT date) as unique_dates
            FROM technical_features
            WHERE ticker = ?
            
            UNION ALL
            
            SELECT 
                'derived' as feature_type,
                COUNT(*) as record_count,
                MIN(date) as min_date,
                MAX(date) as max_date,
                COUNT(DISTINCT date) as unique_dates
            FROM derived_features
            WHERE ticker = ?
            
            UNION ALL
            
            SELECT 
                'options' as feature_type,
                COUNT(*) as record_count,
                MIN(date) as min_date,
                MAX(date) as max_date,
                COUNT(DISTINCT date) as unique_dates
            FROM options_data
            WHERE ticker = ?
        """
        
        summary = self.db.query(summary_sql, (ticker, ticker, ticker))
        return summary
