"""
Derived Features Calculator

Creates derived features from technical indicators and options data:
- Feature interactions
- Z-scores and normalizations
- Regime classifications
- Multi-timeframe features
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from modules.database import get_db_connection, get_technical_features
from modules.features.options_metrics import OptionsMetricsCalculator


class DerivedFeaturesCalculator:
    """Calculate derived features from technical and options data."""
    
    def __init__(self):
        self.db = get_db_connection()
        self.options_calc = OptionsMetricsCalculator()
    
    def calculate_z_scores(
        self,
        df: pd.DataFrame,
        features: List[str],
        window: int = 20
    ) -> pd.DataFrame:
        """
        Calculate rolling Z-scores for specified features.
        
        Z-score = (value - rolling_mean) / rolling_std
        
        Args:
            df: DataFrame with features
            features: List of feature column names
            window: Rolling window size
            
        Returns:
            DataFrame with Z-score columns
        """
        z_scores = pd.DataFrame(index=df.index)
        
        for feature in features:
            if feature not in df.columns:
                continue
            
            rolling_mean = df[feature].rolling(window=window).mean()
            rolling_std = df[feature].rolling(window=window).std()
            
            # Avoid division by zero
            z_score = (df[feature] - rolling_mean) / rolling_std.replace(0, np.nan)
            z_scores[f'{feature}_zscore'] = z_score
        
        return z_scores
    
    def classify_momentum_regime(
        self,
        rsi_14: pd.Series,
        macd_hist: pd.Series,
        price_to_sma50: pd.Series
    ) -> pd.Series:
        """
        Classify market momentum regime.
        
        Regimes:
        - 1: Bullish (RSI > 60, MACD > 0, Price > SMA50)
        - 0: Neutral
        - -1: Bearish (RSI < 40, MACD < 0, Price < SMA50)
        
        Args:
            rsi_14: RSI(14) values
            macd_hist: MACD histogram values
            price_to_sma50: Price / SMA50 ratio
            
        Returns:
            Series with regime classification
        """
        regime = pd.Series(0, index=rsi_14.index, dtype=int)
        
        # Bullish conditions
        bullish = (rsi_14 > 60) & (macd_hist > 0) & (price_to_sma50 > 1.0)
        regime[bullish] = 1
        
        # Bearish conditions
        bearish = (rsi_14 < 40) & (macd_hist < 0) & (price_to_sma50 < 1.0)
        regime[bearish] = -1
        
        return regime
    
    def classify_volatility_regime(
        self,
        hist_vol_20: pd.Series,
        bb_width: pd.Series,
        atr_to_price: pd.Series
    ) -> pd.Series:
        """
        Classify volatility regime.
        
        Regimes:
        - 1: High volatility (above 75th percentile)
        - 0: Normal volatility
        - -1: Low volatility (below 25th percentile)
        
        Args:
            hist_vol_20: 20-day historical volatility
            bb_width: Bollinger Band width
            atr_to_price: ATR / Price ratio
            
        Returns:
            Series with regime classification
        """
        # Calculate composite volatility score
        vol_score = (
            hist_vol_20.rank(pct=True) + 
            bb_width.rank(pct=True) + 
            atr_to_price.rank(pct=True)
        ) / 3
        
        regime = pd.Series(0, index=vol_score.index, dtype=int)
        regime[vol_score > 0.75] = 1   # High volatility
        regime[vol_score < 0.25] = -1  # Low volatility
        
        return regime
    
    def calculate_feature_interactions(
        self,
        tech_features: pd.DataFrame,
        options_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Calculate feature interactions and cross-products.
        
        Args:
            tech_features: DataFrame with technical indicators
            options_data: Optional DataFrame with options data
            
        Returns:
            DataFrame with interaction features
        """
        interactions = pd.DataFrame(index=tech_features.index)
        
        # RSI × Volume Ratio
        if 'rsi_14' in tech_features.columns and 'volume_ratio' in tech_features.columns:
            interactions['rsi_x_volume'] = (
                tech_features['rsi_14'] * tech_features['volume_ratio']
            )
        
        # MACD × ATR (momentum × volatility)
        if 'macd_hist' in tech_features.columns and 'atr_14' in tech_features.columns:
            interactions['macd_x_atr'] = (
                tech_features['macd_hist'] * tech_features['atr_14']
            )
        
        # BB Width × Volume Ratio
        if 'bb_width' in tech_features.columns and 'volume_ratio' in tech_features.columns:
            interactions['bbwidth_x_volume'] = (
                tech_features['bb_width'] * tech_features['volume_ratio']
            )
        
        # Options interactions (if available)
        if options_data is not None and not options_data.empty:
            # RSI × Put/Call Ratio
            if 'rsi_14' in tech_features.columns and 'put_call_ratio' in options_data.columns:
                interactions['rsi_x_pcr'] = (
                    tech_features['rsi_14'] * options_data['put_call_ratio']
                )
            
            # Volatility × IV Rank
            if 'hist_vol_20' in tech_features.columns and 'iv_rank' in options_data.columns:
                interactions['histvol_x_ivrank'] = (
                    tech_features['hist_vol_20'] * options_data['iv_rank']
                )
        
        return interactions
    
    def calculate_price_patterns(self, tech_features: pd.DataFrame) -> pd.DataFrame:
        """
        Detect price patterns and chart formations.
        
        Args:
            tech_features: DataFrame with technical indicators
            
        Returns:
            DataFrame with pattern indicators
        """
        patterns = pd.DataFrame(index=tech_features.index)
        
        # Golden Cross / Death Cross
        if 'sma_50' in tech_features.columns and 'sma_200' in tech_features.columns:
            sma50_above_sma200 = tech_features['sma_50'] > tech_features['sma_200']
            patterns['golden_cross'] = (
                sma50_above_sma200 & ~sma50_above_sma200.shift(1)
            ).astype(int)
            patterns['death_cross'] = (
                ~sma50_above_sma200 & sma50_above_sma200.shift(1)
            ).astype(int)
        
        # MACD Cross
        if 'macd' in tech_features.columns and 'macd_signal' in tech_features.columns:
            macd_above_signal = tech_features['macd'] > tech_features['macd_signal']
            patterns['macd_bullish_cross'] = (
                macd_above_signal & ~macd_above_signal.shift(1)
            ).astype(int)
            patterns['macd_bearish_cross'] = (
                ~macd_above_signal & macd_above_signal.shift(1)
            ).astype(int)
        
        # BB Squeeze (low volatility setup)
        if 'bb_width' in tech_features.columns:
            bb_width_20 = tech_features['bb_width'].rolling(20).mean()
            patterns['bb_squeeze'] = (
                tech_features['bb_width'] < bb_width_20 * 0.5
            ).astype(int)
        
        # Overbought / Oversold
        if 'rsi_14' in tech_features.columns:
            patterns['rsi_overbought'] = (tech_features['rsi_14'] > 70).astype(int)
            patterns['rsi_oversold'] = (tech_features['rsi_14'] < 30).astype(int)
        
        return patterns
    
    def calculate_all_derived_features(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate all derived features for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with all derived features
        """
        # Get technical features
        tech_features = get_technical_features(ticker, start_date, end_date)
        
        if tech_features.empty:
            raise ValueError(f"No technical features found for {ticker}")
        
        # Get options data (if available)
        options_data = self.options_calc.get_historical_put_call_ratio(
            ticker, start_date, end_date
        )
        
        # Merge on date
        if not options_data.empty:
            combined = tech_features.merge(
                options_data,
                on=['date', 'ticker'],
                how='left'
            )
        else:
            combined = tech_features.copy()
        
        # Calculate derived features
        derived = pd.DataFrame(index=combined.index)
        derived['ticker'] = ticker
        derived['date'] = combined['date']
        
        # Z-scores
        z_score_features = ['rsi_14', 'volume_ratio', 'macd_hist', 'bb_width']
        if 'put_call_ratio' in combined.columns:
            z_score_features.append('put_call_ratio')
        
        z_scores = self.calculate_z_scores(combined, z_score_features)
        derived = pd.concat([derived, z_scores], axis=1)
        
        # Regime classification
        if all(col in combined.columns for col in ['rsi_14', 'macd_hist', 'price_to_sma50']):
            derived['momentum_regime'] = self.classify_momentum_regime(
                combined['rsi_14'],
                combined['macd_hist'],
                combined['price_to_sma50']
            )
        
        if all(col in combined.columns for col in ['hist_vol_20', 'bb_width', 'atr_to_price']):
            derived['volatility_regime'] = self.classify_volatility_regime(
                combined['hist_vol_20'],
                combined['bb_width'],
                combined['atr_to_price']
            )
        
        # Feature interactions
        interactions = self.calculate_feature_interactions(
            combined,
            options_data if not options_data.empty else None
        )
        derived = pd.concat([derived, interactions], axis=1)
        
        # Price patterns
        patterns = self.calculate_price_patterns(combined)
        derived = pd.concat([derived, patterns], axis=1)
        
        # Price relatives (already in technical features, but ensure they're here)
        if 'price_to_sma20' in combined.columns:
            derived['price_vs_sma20_pct'] = (combined['price_to_sma20'] - 1) * 100
        if 'price_to_sma50' in combined.columns:
            derived['price_vs_sma50_pct'] = (combined['price_to_sma50'] - 1) * 100
        if 'price_to_sma200' in combined.columns:
            derived['price_vs_sma200_pct'] = (combined['price_to_sma200'] - 1) * 100
        
        return derived
    
    def store_derived_features(self, df: pd.DataFrame) -> None:
        """
        Store derived features in the database.
        
        Args:
            df: DataFrame with derived features
        """
        if df.empty:
            return
        
        try:
            self.db.insert_df(df, 'derived_features', if_exists='append')
            print(f"✅ Stored derived features: {len(df)} records")
        except Exception as e:
            print(f"❌ Error storing derived features: {e}")
    
    def calculate_and_store(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate derived features and store them in the database.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            
        Returns:
            DataFrame with calculated features
        """
        features = self.calculate_all_derived_features(ticker, start_date, end_date)
        self.store_derived_features(features)
        return features
    
    def batch_calculate(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        Calculate derived features for multiple tickers.
        
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
                print(f"✅ Calculated derived features for {ticker}")
            except Exception as e:
                errors[ticker] = str(e)
                print(f"❌ Error calculating derived features for {ticker}: {e}")
        
        if errors:
            print(f"\n⚠️  {len(errors)} tickers failed:")
            for ticker, error in errors.items():
                print(f"  - {ticker}: {error}")
        
        return results
