"""
Data loading module for Economic Dashboard.
Handles all data fetching from FRED and Yahoo Finance with caching.
"""

import streamlit as st
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr
from datetime import datetime, timedelta


@st.cache_data(ttl=3600)
def load_fred_data(series_ids: dict) -> pd.DataFrame:
    """
    Load economic data from FRED database.
    
    Args:
        series_ids: Dictionary with descriptive names as keys and FRED series IDs as values
        
    Returns:
        DataFrame with DatetimeIndex and columns for each series
    """
    try:
        data_frames = {}
        for name, series_id in series_ids.items():
            try:
                df = pdr.DataReader(series_id, 'fred', start='2000-01-01')
                data_frames[name] = df.iloc[:, 0]
            except Exception as e:
                st.warning(f"Could not load {name} ({series_id}): {str(e)}")
                continue
        
        if data_frames:
            result = pd.DataFrame(data_frames)
            return result
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading FRED data: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_yfinance_data(tickers: dict, period: str = "5y") -> dict:
    """
    Load market data from Yahoo Finance.
    
    Args:
        tickers: Dictionary with descriptive names as keys and ticker symbols as values
        period: Time period to fetch (e.g., '1y', '5y', '10y')
        
    Returns:
        Dictionary of DataFrames, one for each ticker
    """
    try:
        result = {}
        for name, ticker in tickers.items():
            try:
                data = yf.download(ticker, period=period, progress=False)
                if not data.empty:
                    result[name] = data
            except Exception as e:
                st.warning(f"Could not load {name} ({ticker}): {str(e)}")
                continue
        return result
    except Exception as e:
        st.error(f"Error loading Yahoo Finance data: {str(e)}")
        return {}


@st.cache_data(ttl=3600)
def get_yield_curve_data() -> pd.DataFrame:
    """
    Fetch US Treasury yield data and calculate spread.
    
    Returns:
        DataFrame with 10-Year yield, 2-Year yield, and spread
    """
    try:
        series_ids = {
            '10-Year': 'DGS10',
            '2-Year': 'DGS2'
        }
        
        df = load_fred_data(series_ids)
        
        if not df.empty and '10-Year' in df.columns and '2-Year' in df.columns:
            df['Spread'] = df['10-Year'] - df['2-Year']
            return df.dropna()
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error calculating yield curve: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_world_bank_gdp() -> pd.DataFrame:
    """
    Load World Bank GDP growth data.
    Note: This is a simplified version. For production, use World Bank API.
    
    Returns:
        DataFrame with GDP growth by country
    """
    try:
        # For now, return a simple dataset
        # In production, integrate with World Bank API or use a CSV file
        countries = ['United States', 'China', 'Germany', 'Japan', 'United Kingdom', 
                     'France', 'India', 'Brazil', 'Canada', 'South Korea']
        gdp_growth = [2.1, 5.2, 0.9, 1.0, 1.3, 1.1, 6.8, 1.2, 1.5, 2.6]
        
        df = pd.DataFrame({
            'Country': countries,
            'GDP Growth (%)': gdp_growth,
            'ISO3': ['USA', 'CHN', 'DEU', 'JPN', 'GBR', 'FRA', 'IND', 'BRA', 'CAN', 'KOR']
        })
        return df
    except Exception as e:
        st.error(f"Error loading World Bank data: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_latest_value(series_id: str) -> float:
    """
    Get the most recent value for a FRED series.
    
    Args:
        series_id: FRED series ID
        
    Returns:
        Latest value as float
    """
    try:
        df = pdr.DataReader(series_id, 'fred', start=(datetime.now() - timedelta(days=365)))
        if not df.empty:
            return df.iloc[-1, 0]
        return None
    except Exception as e:
        st.warning(f"Could not fetch latest value for {series_id}: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def calculate_percentage_change(series_id: str, periods: int = 4) -> float:
    """
    Calculate percentage change over specified periods.
    
    Args:
        series_id: FRED series ID
        periods: Number of periods to look back
        
    Returns:
        Percentage change as float
    """
    try:
        df = pdr.DataReader(series_id, 'fred', start=(datetime.now() - timedelta(days=730)))
        if not df.empty and len(df) >= periods + 1:
            latest = df.iloc[-1, 0]
            previous = df.iloc[-(periods + 1), 0]
            return ((latest - previous) / previous) * 100
        return None
    except Exception as e:
        st.warning(f"Could not calculate change for {series_id}: {str(e)}")
        return None
