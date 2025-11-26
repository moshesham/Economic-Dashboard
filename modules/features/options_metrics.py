"""
Options Metrics Calculator

Calculates put/call ratios and options-related metrics for ML features.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
import yfinance as yf
from modules.database import get_db_connection


class OptionsMetricsCalculator:
    """Calculate and store options metrics for stocks."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def fetch_options_data(self, ticker: str, date: Optional[str] = None) -> dict:
        """
        Fetch options data from Yahoo Finance for a specific date.
        
        Args:
            ticker: Stock ticker symbol
            date: Optional date (YYYY-MM-DD), defaults to today
            
        Returns:
            Dictionary with options metrics
        """
        try:
            stock = yf.Ticker(ticker)
            
            # Get available expiration dates
            expirations = stock.options
            
            if not expirations:
                return {}
            
            # Use the first available expiration (usually nearest term)
            expiry = expirations[0]
            
            # Get options chain
            opt_chain = stock.option_chain(expiry)
            calls = opt_chain.calls
            puts = opt_chain.puts
            
            # Calculate metrics
            metrics = {
                'date': date or datetime.now().strftime('%Y-%m-%d'),
                'ticker': ticker,
                'expiration': expiry,
                
                # Volume metrics
                'put_volume': int(puts['volume'].sum()) if 'volume' in puts.columns else 0,
                'call_volume': int(calls['volume'].sum()) if 'volume' in calls.columns else 0,
                
                # Open Interest metrics
                'put_oi': int(puts['openInterest'].sum()) if 'openInterest' in puts.columns else 0,
                'call_oi': int(calls['openInterest'].sum()) if 'openInterest' in calls.columns else 0,
            }
            
            # Calculate ratios (avoid division by zero)
            metrics['put_call_ratio'] = (
                metrics['put_volume'] / metrics['call_volume'] 
                if metrics['call_volume'] > 0 else None
            )
            metrics['put_call_oi_ratio'] = (
                metrics['put_oi'] / metrics['call_oi'] 
                if metrics['call_oi'] > 0 else None
            )
            
            # Implied Volatility metrics
            call_iv = calls['impliedVolatility'].dropna()
            put_iv = puts['impliedVolatility'].dropna()
            
            if not call_iv.empty and not put_iv.empty:
                metrics['call_iv_mean'] = float(call_iv.mean())
                metrics['put_iv_mean'] = float(put_iv.mean())
                metrics['iv_skew'] = float(put_iv.mean() - call_iv.mean())
            else:
                metrics['call_iv_mean'] = None
                metrics['put_iv_mean'] = None
                metrics['iv_skew'] = None
            
            return metrics
            
        except Exception as e:
            print(f"Error fetching options data for {ticker}: {e}")
            return {}
    
    def calculate_iv_rank(self, ticker: str, current_iv: float, lookback_days: int = 252) -> float:
        """
        Calculate IV Rank: where current IV sits within the range of IVs over lookback period.
        
        IV Rank = (Current IV - Min IV) / (Max IV - Min IV) * 100
        
        Args:
            ticker: Stock ticker symbol
            current_iv: Current implied volatility
            lookback_days: Number of days to look back (default 252 = 1 year)
            
        Returns:
            IV Rank percentage (0-100)
        """
        try:
            # Query historical IV from database
            sql = """
                SELECT date, 
                       (call_iv_mean + put_iv_mean) / 2 as avg_iv
                FROM options_data
                WHERE ticker = ?
                  AND date >= DATE('now', '-{} days')
                ORDER BY date
            """.format(lookback_days)
            
            df = self.db.query(sql, (ticker,))
            
            if df.empty or len(df) < 10:  # Need some history
                return None
            
            min_iv = df['avg_iv'].min()
            max_iv = df['avg_iv'].max()
            
            if max_iv == min_iv:
                return 50.0  # No range, return midpoint
            
            iv_rank = ((current_iv - min_iv) / (max_iv - min_iv)) * 100
            return float(iv_rank)
            
        except Exception as e:
            print(f"Error calculating IV rank for {ticker}: {e}")
            return None
    
    def calculate_iv_percentile(
        self, 
        ticker: str, 
        current_iv: float, 
        lookback_days: int = 252
    ) -> float:
        """
        Calculate IV Percentile: percentage of days with IV below current IV.
        
        Args:
            ticker: Stock ticker symbol
            current_iv: Current implied volatility
            lookback_days: Number of days to look back
            
        Returns:
            IV Percentile (0-100)
        """
        try:
            sql = """
                SELECT date, 
                       (call_iv_mean + put_iv_mean) / 2 as avg_iv
                FROM options_data
                WHERE ticker = ?
                  AND date >= DATE('now', '-{} days')
            """.format(lookback_days)
            
            df = self.db.query(sql, (ticker,))
            
            if df.empty:
                return None
            
            below_current = (df['avg_iv'] < current_iv).sum()
            total = len(df)
            
            percentile = (below_current / total) * 100
            return float(percentile)
            
        except Exception as e:
            print(f"Error calculating IV percentile for {ticker}: {e}")
            return None
    
    def calculate_options_features(
        self, 
        ticker: str,
        date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate comprehensive options features for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            date: Optional date (YYYY-MM-DD)
            
        Returns:
            DataFrame with options features
        """
        # Fetch current options data
        metrics = self.fetch_options_data(ticker, date)
        
        if not metrics:
            return pd.DataFrame()
        
        # Calculate advanced metrics
        if metrics.get('call_iv_mean') and metrics.get('put_iv_mean'):
            avg_iv = (metrics['call_iv_mean'] + metrics['put_iv_mean']) / 2
            
            metrics['iv_rank'] = self.calculate_iv_rank(ticker, avg_iv)
            metrics['iv_percentile'] = self.calculate_iv_percentile(ticker, avg_iv)
        
        # Convert to DataFrame
        df = pd.DataFrame([metrics])
        
        return df
    
    def store_options_data(self, df: pd.DataFrame) -> None:
        """
        Store options data in the database.
        
        Args:
            df: DataFrame with options metrics
        """
        if df.empty:
            return
        
        try:
            # Prepare data for insertion
            insert_cols = [
                'date', 'ticker', 'put_volume', 'call_volume',
                'put_oi', 'call_oi', 'put_call_ratio', 'put_call_oi_ratio',
                'iv_rank', 'iv_percentile', 'skew'
            ]
            
            # Rename columns to match database schema
            df_insert = df.copy()
            if 'iv_skew' in df_insert.columns:
                df_insert['skew'] = df_insert['iv_skew']
            
            # Select only columns that exist
            available_cols = [col for col in insert_cols if col in df_insert.columns]
            df_insert = df_insert[available_cols]
            
            # Insert into database
            self.db.insert_df(df_insert, 'options_data', if_exists='append')
            
            print(f"✅ Stored options data: {len(df_insert)} records")
            
        except Exception as e:
            print(f"❌ Error storing options data: {e}")
    
    def calculate_and_store(
        self,
        ticker: str,
        date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate options features and store them in the database.
        
        Args:
            ticker: Stock ticker symbol
            date: Optional date (YYYY-MM-DD)
            
        Returns:
            DataFrame with calculated features
        """
        features = self.calculate_options_features(ticker, date)
        
        if not features.empty:
            self.store_options_data(features)
        
        return features
    
    def batch_calculate(
        self,
        tickers: List[str],
        date: Optional[str] = None
    ) -> dict:
        """
        Calculate options features for multiple tickers.
        
        Args:
            tickers: List of stock ticker symbols
            date: Optional date (YYYY-MM-DD)
            
        Returns:
            Dictionary mapping tickers to feature DataFrames
        """
        results = {}
        errors = {}
        
        for ticker in tickers:
            try:
                results[ticker] = self.calculate_and_store(ticker, date)
                print(f"✅ Calculated options metrics for {ticker}")
            except Exception as e:
                errors[ticker] = str(e)
                print(f"❌ Error calculating options for {ticker}: {e}")
        
        if errors:
            print(f"\n⚠️  {len(errors)} tickers failed:")
            for ticker, error in errors.items():
                print(f"  - {ticker}: {error}")
        
        return results
    
    def get_historical_put_call_ratio(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical put/call ratios from the database.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with historical put/call ratios
        """
        sql = """
            SELECT date, ticker, 
                   put_call_ratio, 
                   put_call_oi_ratio,
                   iv_rank,
                   iv_percentile,
                   skew
            FROM options_data
            WHERE ticker = ?
        """
        
        params = [ticker]
        
        if start_date:
            sql += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            sql += " AND date <= ?"
            params.append(end_date)
        
        sql += " ORDER BY date"
        
        df = self.db.query(sql, tuple(params))
        return df
