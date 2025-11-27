"""
Recession Probability Model

Calculates the probability of a US recession using multiple economic indicators:
- Yield curve inversions (10Y-2Y and 10Y-3M spreads)
- Labor market (unemployment rate, Sahm Rule, jobless claims)
- Financial stress (credit spreads, Fed funds rate changes)
- Economic activity (industrial production, GDP growth)
- Consumer sentiment (U. Michigan Consumer Sentiment)
- Housing market (building permits)
- Stock market performance (S&P 500)

The model uses a weighted scoring approach based on empirical research
showing the predictive power of each indicator for recessions.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


# FRED series IDs for recession indicators
RECESSION_INDICATOR_SERIES = {
    # Yield Curve
    'yield_spread_10y2y': 'T10Y2Y',  # 10-Year minus 2-Year Treasury Spread
    'yield_spread_10y3m': 'T10Y3M',  # 10-Year minus 3-Month Treasury Spread
    
    # Labor Market
    'unemployment_rate': 'UNRATE',  # Civilian Unemployment Rate
    'initial_claims': 'ICSA',       # Initial Jobless Claims
    'continued_claims': 'CCSA',     # Continued Claims
    
    # Economic Activity
    'industrial_production': 'INDPRO',  # Industrial Production Index
    'real_gdp_growth': 'A191RL1Q225SBEA',  # Real GDP Growth Rate
    
    # Consumer/Confidence
    'consumer_sentiment': 'UMCSENT',  # University of Michigan Consumer Sentiment
    
    # Financial Conditions
    'fed_funds_rate': 'FEDFUNDS',  # Federal Funds Rate
    'corporate_spread': 'BAA10Y',   # Moody's BAA Corporate Bond Yield - 10Y Treasury
    
    # Housing
    'building_permits': 'PERMIT',   # New Private Housing Units Authorized
    
    # Stock Market
    'sp500_returns': None,  # Will use yfinance for this
}

# Weights for each indicator based on empirical recession prediction performance
# Higher weight = more predictive power for recessions
INDICATOR_WEIGHTS = {
    'yield_curve_signal': 0.25,      # Strong predictor, 12-18 month lead
    'labor_market_signal': 0.20,     # Important coincident/lagging indicator
    'financial_stress_signal': 0.15, # Credit conditions
    'economic_activity_signal': 0.15, # Production and GDP
    'consumer_signal': 0.10,         # Consumer health
    'housing_signal': 0.10,          # Leading indicator
    'market_signal': 0.05,           # Market sentiment
}


class RecessionProbabilityModel:
    """
    Calculate recession probability using multiple economic indicators.
    
    Uses a weighted scoring approach where each indicator contributes
    a signal strength (0-1) that is weighted by its empirical predictive power.
    """
    
    def __init__(self):
        self.indicator_data: Dict[str, pd.DataFrame] = {}
        self.signals: Dict[str, float] = {}
        self.last_update: Optional[datetime] = None
        
    def load_indicators_from_data(
        self,
        fred_data: pd.DataFrame,
        market_data: Optional[pd.DataFrame] = None
    ) -> None:
        """
        Load indicator data from provided DataFrames.
        
        Args:
            fred_data: DataFrame with FRED series data (columns are indicator names)
            market_data: Optional DataFrame with market data (e.g., S&P 500)
        """
        self.indicator_data['fred'] = fred_data
        if market_data is not None:
            self.indicator_data['market'] = market_data
        self.last_update = datetime.now()
        
    def _calculate_yield_curve_signal(self, data: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate yield curve signal based on spread inversions.
        
        Yield curve inversion (negative spread) is one of the most reliable
        recession predictors, typically leading by 12-18 months.
        
        Returns:
            Tuple of (signal_strength, details_dict)
        """
        details = {}
        signal = 0.0
        
        # 10Y-2Y Spread
        if 'yield_spread_10y2y' in data.columns:
            spread_10y2y = data['yield_spread_10y2y'].dropna()
            if not spread_10y2y.empty:
                current_spread = spread_10y2y.iloc[-1]
                details['10y2y_spread'] = current_spread
                
                # Check for inversion
                if current_spread < 0:
                    # Strong inversion signal - currently inverted
                    signal += 0.6
                    details['10y2y_inverted'] = True
                elif current_spread < 0.25:
                    # Near-inversion warning
                    signal += 0.3
                    details['10y2y_inverted'] = False
                else:
                    details['10y2y_inverted'] = False
                
                # Check for recent inversion in past 18 months
                lookback_days = 365 * 1.5  # 18 months
                recent_data = spread_10y2y[spread_10y2y.index >= datetime.now() - timedelta(days=lookback_days)]
                if not recent_data.empty:
                    min_spread = recent_data.min()
                    if min_spread < 0:
                        # There was an inversion in the lookback period
                        signal += 0.2
                        details['recent_inversion'] = True
                    else:
                        details['recent_inversion'] = False
        
        # 10Y-3M Spread (another important measure)
        if 'yield_spread_10y3m' in data.columns:
            spread_10y3m = data['yield_spread_10y3m'].dropna()
            if not spread_10y3m.empty:
                current_spread_3m = spread_10y3m.iloc[-1]
                details['10y3m_spread'] = current_spread_3m
                
                if current_spread_3m < 0:
                    signal += 0.2
                    details['10y3m_inverted'] = True
                else:
                    details['10y3m_inverted'] = False
        
        # Normalize signal to 0-1 range
        signal = min(signal, 1.0)
        
        return signal, details
    
    def _calculate_labor_market_signal(self, data: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate labor market signal based on unemployment and claims trends.
        
        Rising unemployment and jobless claims indicate economic weakness.
        
        Returns:
            Tuple of (signal_strength, details_dict)
        """
        details = {}
        signal = 0.0
        
        # Unemployment Rate
        if 'unemployment_rate' in data.columns:
            unemp = data['unemployment_rate'].dropna()
            if len(unemp) >= 12:
                current_unemp = unemp.iloc[-1]
                unemp_12m_ago = unemp.iloc[-12] if len(unemp) >= 12 else unemp.iloc[0]
                unemp_change = current_unemp - unemp_12m_ago
                
                details['unemployment_rate'] = current_unemp
                details['unemployment_change_12m'] = unemp_change
                
                # Rising unemployment is concerning
                if unemp_change > 1.0:
                    signal += 0.5
                elif unemp_change > 0.5:
                    signal += 0.3
                elif unemp_change > 0.2:
                    signal += 0.1
                
                # Sahm Rule: Recession starts when 3-month avg unemployment rises
                # 0.5 percentage points above its 12-month low
                if len(unemp) >= 3:
                    unemp_3m_avg = unemp.iloc[-3:].mean()
                    unemp_12m_low = unemp.iloc[-12:].min() if len(unemp) >= 12 else unemp.min()
                    sahm_indicator = unemp_3m_avg - unemp_12m_low
                    details['sahm_indicator'] = sahm_indicator
                    
                    if sahm_indicator >= 0.5:
                        signal += 0.4
                        details['sahm_triggered'] = True
                    else:
                        details['sahm_triggered'] = False
        
        # Initial Jobless Claims
        if 'initial_claims' in data.columns:
            claims = data['initial_claims'].dropna()
            if len(claims) >= 4:
                # 4-week moving average
                claims_4wk = claims.iloc[-4:].mean()
                claims_12wk = claims.iloc[-12:].mean() if len(claims) >= 12 else claims.mean()
                
                details['initial_claims_4wk_avg'] = claims_4wk
                
                # Rising claims trend
                claims_change_pct = (claims_4wk - claims_12wk) / claims_12wk * 100 if claims_12wk > 0 else 0
                details['claims_change_pct'] = claims_change_pct
                
                if claims_change_pct > 30:
                    signal += 0.3
                elif claims_change_pct > 15:
                    signal += 0.15
        
        signal = min(signal, 1.0)
        return signal, details
    
    def _calculate_financial_stress_signal(self, data: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate financial stress signal based on credit spreads and conditions.
        
        Widening credit spreads indicate financial stress and risk aversion.
        
        Returns:
            Tuple of (signal_strength, details_dict)
        """
        details = {}
        signal = 0.0
        
        # Corporate Bond Spread (BAA - 10Y Treasury)
        if 'corporate_spread' in data.columns:
            spread = data['corporate_spread'].dropna()
            if not spread.empty:
                current_spread = spread.iloc[-1]
                avg_spread = spread.mean()
                std_spread = spread.std()
                
                details['corporate_spread'] = current_spread
                details['avg_spread'] = avg_spread
                
                # Z-score of spread
                z_score = (current_spread - avg_spread) / std_spread if std_spread > 0 else 0
                details['spread_zscore'] = z_score
                
                # Elevated spreads indicate stress
                if z_score > 2:
                    signal += 0.5
                elif z_score > 1:
                    signal += 0.3
                elif z_score > 0.5:
                    signal += 0.15
                
                # Absolute spread level
                if current_spread > 3.0:
                    signal += 0.3
                elif current_spread > 2.5:
                    signal += 0.15
        
        # Fed Funds Rate changes (rapid hikes can stress economy)
        if 'fed_funds_rate' in data.columns:
            ff_rate = data['fed_funds_rate'].dropna()
            if len(ff_rate) >= 12:
                current_rate = ff_rate.iloc[-1]
                rate_12m_ago = ff_rate.iloc[-12] if len(ff_rate) >= 12 else ff_rate.iloc[0]
                rate_change = current_rate - rate_12m_ago
                
                details['fed_funds_rate'] = current_rate
                details['rate_change_12m'] = rate_change
                
                # Rapid rate increases stress the economy
                if rate_change > 2.0:
                    signal += 0.2
                elif rate_change > 1.0:
                    signal += 0.1
        
        signal = min(signal, 1.0)
        return signal, details
    
    def _calculate_economic_activity_signal(self, data: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate economic activity signal based on production and GDP.
        
        Declining industrial production and GDP indicate economic contraction.
        
        Returns:
            Tuple of (signal_strength, details_dict)
        """
        details = {}
        signal = 0.0
        
        # Industrial Production
        if 'industrial_production' in data.columns:
            ip = data['industrial_production'].dropna()
            if len(ip) >= 12:
                # Calculate YoY change
                ip_yoy_change = (ip.iloc[-1] / ip.iloc[-12] - 1) * 100 if len(ip) >= 12 else 0
                
                details['industrial_production_yoy'] = ip_yoy_change
                
                if ip_yoy_change < -3:
                    signal += 0.5
                elif ip_yoy_change < 0:
                    signal += 0.3
                elif ip_yoy_change < 1:
                    signal += 0.1
        
        # Real GDP Growth
        if 'real_gdp_growth' in data.columns:
            gdp = data['real_gdp_growth'].dropna()
            if not gdp.empty:
                current_gdp = gdp.iloc[-1]
                details['gdp_growth'] = current_gdp
                
                # Negative GDP is a red flag
                if current_gdp < -1:
                    signal += 0.5
                elif current_gdp < 0:
                    signal += 0.3
                elif current_gdp < 1:
                    signal += 0.1
                
                # Two consecutive negative quarters
                if len(gdp) >= 2:
                    if gdp.iloc[-1] < 0 and gdp.iloc[-2] < 0:
                        signal += 0.3
                        details['two_negative_quarters'] = True
                    else:
                        details['two_negative_quarters'] = False
        
        signal = min(signal, 1.0)
        return signal, details
    
    def _calculate_consumer_signal(self, data: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate consumer signal based on sentiment and spending indicators.
        
        Declining consumer confidence often precedes spending cuts.
        
        Returns:
            Tuple of (signal_strength, details_dict)
        """
        details = {}
        signal = 0.0
        
        # Consumer Sentiment
        if 'consumer_sentiment' in data.columns:
            sentiment = data['consumer_sentiment'].dropna()
            if len(sentiment) >= 12:
                current_sentiment = sentiment.iloc[-1]
                avg_sentiment = sentiment.mean()
                sentiment_12m_ago = sentiment.iloc[-12] if len(sentiment) >= 12 else sentiment.iloc[0]
                
                details['consumer_sentiment'] = current_sentiment
                details['avg_sentiment'] = avg_sentiment
                
                # Low absolute level
                if current_sentiment < 60:
                    signal += 0.4
                elif current_sentiment < 70:
                    signal += 0.2
                elif current_sentiment < 80:
                    signal += 0.1
                
                # Declining trend
                sentiment_change = current_sentiment - sentiment_12m_ago
                details['sentiment_change_12m'] = sentiment_change
                
                if sentiment_change < -15:
                    signal += 0.3
                elif sentiment_change < -10:
                    signal += 0.2
                elif sentiment_change < -5:
                    signal += 0.1
        
        signal = min(signal, 1.0)
        return signal, details
    
    def _calculate_housing_signal(self, data: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate housing signal based on building permits and housing starts.
        
        Housing is a leading indicator - declining permits precede downturns.
        
        Returns:
            Tuple of (signal_strength, details_dict)
        """
        details = {}
        signal = 0.0
        
        # Building Permits
        if 'building_permits' in data.columns:
            permits = data['building_permits'].dropna()
            if len(permits) >= 12:
                # Calculate YoY change
                permits_yoy_change = (permits.iloc[-1] / permits.iloc[-12] - 1) * 100 if len(permits) >= 12 and permits.iloc[-12] > 0 else 0
                
                details['building_permits'] = permits.iloc[-1]
                details['permits_yoy_change'] = permits_yoy_change
                
                if permits_yoy_change < -20:
                    signal += 0.5
                elif permits_yoy_change < -10:
                    signal += 0.3
                elif permits_yoy_change < -5:
                    signal += 0.15
        
        signal = min(signal, 1.0)
        return signal, details
    
    def _calculate_market_signal(self, data: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate market signal based on stock market performance.
        
        Stock market declines can signal economic concerns.
        
        Returns:
            Tuple of (signal_strength, details_dict)
        """
        details = {}
        signal = 0.0
        
        # Check for market data
        if 'market' in self.indicator_data:
            market = self.indicator_data['market']
            if 'Close' in market.columns or 'close' in market.columns:
                close_col = 'Close' if 'Close' in market.columns else 'close'
                prices = market[close_col].dropna()
                
                if len(prices) >= 252:  # ~1 year of trading days
                    current_price = prices.iloc[-1]
                    price_52wk_high = prices.iloc[-252:].max()
                    
                    # Drawdown from 52-week high
                    drawdown = (current_price - price_52wk_high) / price_52wk_high * 100
                    details['drawdown_from_52wk_high'] = drawdown
                    
                    # Significant drawdown indicates market stress
                    if drawdown < -20:  # Bear market territory
                        signal += 0.5
                    elif drawdown < -10:  # Correction territory
                        signal += 0.3
                    elif drawdown < -5:
                        signal += 0.1
                    
                    # 200-day moving average
                    ma_200 = prices.rolling(200).mean()
                    if not ma_200.empty and len(ma_200) >= 200:
                        current_ma200 = ma_200.iloc[-1]
                        if current_price < current_ma200:
                            signal += 0.2
                            details['below_200ma'] = True
                        else:
                            details['below_200ma'] = False
        
        signal = min(signal, 1.0)
        return signal, details
    
    def calculate_recession_probability(self) -> Dict[str, Any]:
        """
        Calculate the overall recession probability based on all indicators.
        
        Returns:
            Dictionary with probability, individual signals, and details
        """
        if 'fred' not in self.indicator_data:
            raise ValueError("No indicator data loaded. Call load_indicators_from_data first.")
        
        data = self.indicator_data['fred']
        
        # Calculate each signal
        yield_signal, yield_details = self._calculate_yield_curve_signal(data)
        labor_signal, labor_details = self._calculate_labor_market_signal(data)
        financial_signal, financial_details = self._calculate_financial_stress_signal(data)
        activity_signal, activity_details = self._calculate_economic_activity_signal(data)
        consumer_signal, consumer_details = self._calculate_consumer_signal(data)
        housing_signal, housing_details = self._calculate_housing_signal(data)
        market_signal, market_details = self._calculate_market_signal(data)
        
        # Store signals
        self.signals = {
            'yield_curve_signal': yield_signal,
            'labor_market_signal': labor_signal,
            'financial_stress_signal': financial_signal,
            'economic_activity_signal': activity_signal,
            'consumer_signal': consumer_signal,
            'housing_signal': housing_signal,
            'market_signal': market_signal,
        }
        
        # Calculate weighted probability
        weighted_probability = sum(
            self.signals[key] * INDICATOR_WEIGHTS[key]
            for key in INDICATOR_WEIGHTS.keys()
            if key in self.signals
        )
        
        # The weighted probability is already normalized to 0-1 range
        # since each signal is 0-1 and weights sum to 1
        probability = weighted_probability
        
        # Determine risk level
        if probability >= 0.7:
            risk_level = 'HIGH'
            risk_color = 'red'
        elif probability >= 0.4:
            risk_level = 'ELEVATED'
            risk_color = 'orange'
        elif probability >= 0.2:
            risk_level = 'MODERATE'
            risk_color = 'yellow'
        else:
            risk_level = 'LOW'
            risk_color = 'green'
        
        result = {
            'probability': probability,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'signals': self.signals,
            'details': {
                'yield_curve': yield_details,
                'labor_market': labor_details,
                'financial_stress': financial_details,
                'economic_activity': activity_details,
                'consumer': consumer_details,
                'housing': housing_details,
                'market': market_details,
            },
            'weights': INDICATOR_WEIGHTS,
            'calculation_time': datetime.now().isoformat(),
        }
        
        return result
    
    def get_indicator_explanations(self) -> Dict[str, str]:
        """
        Get explanations for each recession indicator.
        
        Returns:
            Dictionary mapping indicator names to explanations
        """
        return {
            'yield_curve_signal': (
                "The yield curve spread (10Y-2Y Treasury) is one of the most reliable recession "
                "predictors. An inverted yield curve (negative spread) has preceded every US recession "
                "since 1955, typically by 12-18 months. It signals that markets expect short-term "
                "rates to fall due to economic weakness."
            ),
            'labor_market_signal': (
                "Labor market indicators including unemployment rate and jobless claims are key "
                "recession signals. The Sahm Rule, which triggers when the 3-month average unemployment "
                "rate rises 0.5 percentage points above its 12-month low, has accurately identified "
                "every recession since 1970."
            ),
            'financial_stress_signal': (
                "Credit spreads between corporate bonds and Treasuries indicate financial stress "
                "and risk aversion. Widening spreads suggest investors are demanding higher premiums "
                "for risk, often preceding economic downturns. Rapid Fed rate hikes can also "
                "stress the economy."
            ),
            'economic_activity_signal': (
                "Industrial production and GDP growth directly measure economic output. Declining "
                "industrial production often leads recessions, while two consecutive quarters of "
                "negative GDP growth is a common (though not official) recession definition."
            ),
            'consumer_signal': (
                "Consumer sentiment measures confidence in the economy and future spending intentions. "
                "Sharp declines in consumer confidence often precede reduced spending and economic "
                "slowdowns, as consumption drives about 70% of US GDP."
            ),
            'housing_signal': (
                "Housing is a leading economic indicator. Declining building permits and housing "
                "starts often precede broader economic weakness, as construction affects employment, "
                "consumer spending, and financial markets."
            ),
            'market_signal': (
                "Stock market performance reflects investor expectations about future earnings "
                "and economic conditions. While volatile, significant market drawdowns and "
                "prices below long-term moving averages can signal economic concerns."
            ),
        }
    
    def get_historical_probabilities(
        self,
        data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Calculate historical recession probabilities over a date range.
        
        Args:
            data: DataFrame with historical indicator data
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            
        Returns:
            DataFrame with dates and recession probabilities
        """
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        probabilities = []
        
        # Calculate probability for each date (using rolling windows)
        for i in range(12, len(data)):  # Need at least 12 periods of history
            window_data = data.iloc[:i+1]
            self.load_indicators_from_data(window_data)
            
            try:
                result = self.calculate_recession_probability()
                probabilities.append({
                    'date': data.index[i],
                    'probability': result['probability'],
                    'risk_level': result['risk_level'],
                })
            except Exception as e:
                logger.warning(f"Could not calculate probability for {data.index[i]}: {e}")
                continue
        
        return pd.DataFrame(probabilities)


def get_recession_indicator_series() -> Dict[str, str]:
    """
    Get the dictionary of FRED series IDs needed for recession probability model.
    
    Returns:
        Dictionary mapping indicator names to FRED series IDs
    """
    return {k: v for k, v in RECESSION_INDICATOR_SERIES.items() if v is not None}
