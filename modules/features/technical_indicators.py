"""
Technical Indicators Calculator

Calculates technical indicators for stock price data and stores them in DuckDB.
Uses the 'ta' library for standardized technical analysis calculations.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List
import ta
from modules.database import get_db_connection, get_stock_ohlcv, insert_technical_features


class TechnicalIndicatorCalculator:
    """Calculate and store technical indicators for stocks."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def calculate_all_indicators(
        self, 
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate all technical indicators for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with all technical indicators
        """
        # Get OHLCV data
        df = get_stock_ohlcv(ticker=ticker, start_date=start_date, end_date=end_date)
        
        if df.empty:
            raise ValueError(f"No OHLCV data found for {ticker}")
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Calculate all indicators
        features = pd.DataFrame(index=df.index)
        features['ticker'] = ticker
        features['date'] = df.index
        
        # Momentum Indicators
        features = pd.concat([features, self._calculate_momentum(df)], axis=1)
        
        # Trend Indicators
        features = pd.concat([features, self._calculate_trend(df)], axis=1)
        
        # Volatility Indicators
        features = pd.concat([features, self._calculate_volatility(df)], axis=1)
        
        # Volume Indicators
        features = pd.concat([features, self._calculate_volume(df)], axis=1)
        
        # Custom Indicators
        features = pd.concat([features, self._calculate_custom(df, features)], axis=1)
        
        return features
    
    def _calculate_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum indicators."""
        momentum = pd.DataFrame(index=df.index)
        
        # RSI (Relative Strength Index)
        momentum['rsi_5'] = ta.momentum.RSIIndicator(df['close'], window=5).rsi()
        momentum['rsi_14'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        momentum['rsi_28'] = ta.momentum.RSIIndicator(df['close'], window=28).rsi()
        
        # Stochastic Oscillator
        stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
        momentum['stoch_k'] = stoch.stoch()
        momentum['stoch_d'] = stoch.stoch_signal()
        
        # Williams %R
        momentum['williams_r'] = ta.momentum.WilliamsRIndicator(
            df['high'], df['low'], df['close']
        ).williams_r()
        
        # Rate of Change
        momentum['roc_5'] = ta.momentum.ROCIndicator(df['close'], window=5).roc()
        momentum['roc_10'] = ta.momentum.ROCIndicator(df['close'], window=10).roc()
        momentum['roc_20'] = ta.momentum.ROCIndicator(df['close'], window=20).roc()
        
        # Momentum
        momentum['momentum_10'] = df['close'].diff(10)
        momentum['momentum_20'] = df['close'].diff(20)
        
        return momentum
    
    def _calculate_trend(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trend indicators."""
        trend = pd.DataFrame(index=df.index)
        
        # Simple Moving Averages
        trend['sma_10'] = ta.trend.SMAIndicator(df['close'], window=10).sma_indicator()
        trend['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
        trend['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
        trend['sma_200'] = ta.trend.SMAIndicator(df['close'], window=200).sma_indicator()
        
        # Exponential Moving Averages
        trend['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
        trend['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
        trend['ema_50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        
        # MACD (Moving Average Convergence Divergence)
        macd = ta.trend.MACD(df['close'])
        trend['macd'] = macd.macd()
        trend['macd_signal'] = macd.macd_signal()
        trend['macd_hist'] = macd.macd_diff()
        
        # ADX (Average Directional Index)
        adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
        trend['adx'] = adx.adx()
        trend['adx_pos'] = adx.adx_pos()
        trend['adx_neg'] = adx.adx_neg()
        
        # Parabolic SAR
        trend['psar'] = ta.trend.PSARIndicator(
            df['high'], df['low'], df['close']
        ).psar()
        
        return trend
    
    def _calculate_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility indicators."""
        volatility = pd.DataFrame(index=df.index)
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'])
        volatility['bb_upper'] = bb.bollinger_hband()
        volatility['bb_middle'] = bb.bollinger_mavg()
        volatility['bb_lower'] = bb.bollinger_lband()
        volatility['bb_width'] = (
            (bb.bollinger_hband() - bb.bollinger_lband()) / bb.bollinger_mavg()
        )
        volatility['bb_pct_b'] = bb.bollinger_pband()
        
        # Average True Range
        volatility['atr_14'] = ta.volatility.AverageTrueRange(
            df['high'], df['low'], df['close'], window=14
        ).average_true_range()
        volatility['atr_20'] = ta.volatility.AverageTrueRange(
            df['high'], df['low'], df['close'], window=20
        ).average_true_range()
        
        # Historical Volatility (20-day)
        returns = df['close'].pct_change()
        volatility['hist_vol_20'] = returns.rolling(window=20).std() * np.sqrt(252)
        volatility['hist_vol_50'] = returns.rolling(window=50).std() * np.sqrt(252)
        
        # Keltner Channels
        kc = ta.volatility.KeltnerChannel(df['high'], df['low'], df['close'])
        volatility['kc_upper'] = kc.keltner_channel_hband()
        volatility['kc_middle'] = kc.keltner_channel_mband()
        volatility['kc_lower'] = kc.keltner_channel_lband()
        
        return volatility
    
    def _calculate_volume(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume indicators."""
        volume_ind = pd.DataFrame(index=df.index)
        
        # On-Balance Volume
        volume_ind['obv'] = ta.volume.OnBalanceVolumeIndicator(
            df['close'], df['volume']
        ).on_balance_volume()
        
        # OBV Moving Average
        volume_ind['obv_sma_20'] = ta.trend.SMAIndicator(
            volume_ind['obv'], window=20
        ).sma_indicator()
        
        # Money Flow Index
        volume_ind['mfi'] = ta.volume.MFIIndicator(
            df['high'], df['low'], df['close'], df['volume']
        ).money_flow_index()
        
        # Accumulation/Distribution Index
        volume_ind['ad_line'] = ta.volume.AccDistIndexIndicator(
            df['high'], df['low'], df['close'], df['volume']
        ).acc_dist_index()
        
        # Chaikin Money Flow
        volume_ind['cmf'] = ta.volume.ChaikinMoneyFlowIndicator(
            df['high'], df['low'], df['close'], df['volume']
        ).chaikin_money_flow()
        
        # Volume Weighted Average Price
        volume_ind['vwap'] = ta.volume.VolumeWeightedAveragePrice(
            df['high'], df['low'], df['close'], df['volume']
        ).volume_weighted_average_price()
        
        # Volume Moving Averages
        volume_ind['volume_sma_20'] = ta.trend.SMAIndicator(
            df['volume'], window=20
        ).sma_indicator()
        volume_ind['volume_sma_50'] = ta.trend.SMAIndicator(
            df['volume'], window=50
        ).sma_indicator()
        
        # Volume Ratio (current vs 20-day average)
        volume_ind['volume_ratio'] = df['volume'] / volume_ind['volume_sma_20']
        
        return volume_ind
    
    def _calculate_custom(self, df: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
        """Calculate custom indicators."""
        custom = pd.DataFrame(index=df.index)
        
        # Price relative to moving averages
        custom['price_to_sma20'] = df['close'] / features['sma_20']
        custom['price_to_sma50'] = df['close'] / features['sma_50']
        custom['price_to_sma200'] = df['close'] / features['sma_200']
        
        # Distance from Bollinger Bands
        custom['bb_position'] = (
            (df['close'] - features['bb_lower']) / 
            (features['bb_upper'] - features['bb_lower'])
        )
        
        # Trend strength (SMA slope)
        custom['sma20_slope'] = features['sma_20'].diff(5) / features['sma_20']
        custom['sma50_slope'] = features['sma_50'].diff(10) / features['sma_50']
        
        # Volatility ratios
        custom['atr_to_price'] = features['atr_14'] / df['close']
        custom['bb_width_norm'] = features['bb_width'] / features['bb_width'].rolling(50).mean()
        
        # Price momentum
        custom['return_1d'] = df['close'].pct_change(1)
        custom['return_5d'] = df['close'].pct_change(5)
        custom['return_10d'] = df['close'].pct_change(10)
        custom['return_20d'] = df['close'].pct_change(20)
        
        # High-Low Range
        custom['hl_range'] = (df['high'] - df['low']) / df['close']
        custom['hl_range_ma20'] = custom['hl_range'].rolling(20).mean()
        
        return custom
    
    def calculate_and_store(
        self, 
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate technical indicators and store them in the database.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with calculated indicators
        """
        features = self.calculate_all_indicators(ticker, start_date, end_date)
        
        # Store in database
        insert_technical_features(features)
        
        return features
    
    def batch_calculate(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        Calculate technical indicators for multiple tickers.
        
        Args:
            tickers: List of stock ticker symbols
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            Dictionary mapping tickers to feature DataFrames
        """
        results = {}
        errors = {}
        
        for ticker in tickers:
            try:
                results[ticker] = self.calculate_and_store(ticker, start_date, end_date)
                print(f"✅ Calculated technical indicators for {ticker}")
            except Exception as e:
                errors[ticker] = str(e)
                print(f"❌ Error calculating indicators for {ticker}: {e}")
        
        if errors:
            print(f"\n⚠️  {len(errors)} tickers failed:")
            for ticker, error in errors.items():
                print(f"  - {ticker}: {error}")
        
        return results
