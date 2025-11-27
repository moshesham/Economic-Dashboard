"""
Unit tests for the Recession Probability Model.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.ml.recession_model import (
    RecessionProbabilityModel,
    get_recession_indicator_series,
    INDICATOR_WEIGHTS,
    RECESSION_INDICATOR_SERIES
)


class TestRecessionProbabilityModel:
    """Test cases for RecessionProbabilityModel class."""
    
    @pytest.fixture
    def sample_fred_data(self):
        """Create sample FRED data for testing."""
        dates = pd.date_range(end=datetime.now(), periods=24, freq='ME')
        
        data = pd.DataFrame({
            'yield_spread_10y2y': np.random.uniform(-0.5, 2.0, 24),
            'yield_spread_10y3m': np.random.uniform(-0.3, 2.5, 24),
            'unemployment_rate': np.random.uniform(3.5, 5.0, 24),
            'initial_claims': np.random.uniform(200000, 300000, 24),
            'corporate_spread': np.random.uniform(1.5, 3.0, 24),
            'fed_funds_rate': np.random.uniform(0.0, 5.5, 24),
            'industrial_production': np.random.uniform(100, 110, 24),
            'real_gdp_growth': np.random.uniform(-1.0, 4.0, 24),
            'consumer_sentiment': np.random.uniform(60, 100, 24),
            'building_permits': np.random.uniform(1200, 1600, 24),
        }, index=dates)
        
        return data
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        dates = pd.date_range(end=datetime.now(), periods=300, freq='D')
        
        # Simulate a trending market with some volatility
        prices = 4000 + np.cumsum(np.random.randn(300) * 10)
        
        data = pd.DataFrame({
            'Close': prices,
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, 300)),
            'High': prices * (1 + np.random.uniform(0, 0.02, 300)),
            'Low': prices * (1 - np.random.uniform(0, 0.02, 300)),
            'Volume': np.random.uniform(1e9, 5e9, 300),
        }, index=dates)
        
        return data
    
    @pytest.fixture
    def model(self):
        """Create a RecessionProbabilityModel instance."""
        return RecessionProbabilityModel()
    
    def test_model_initialization(self, model):
        """Test that model initializes with empty data."""
        assert model.indicator_data == {}
        assert model.signals == {}
        assert model.last_update is None
    
    def test_load_indicators_from_data(self, model, sample_fred_data, sample_market_data):
        """Test loading indicator data."""
        model.load_indicators_from_data(sample_fred_data, sample_market_data)
        
        assert 'fred' in model.indicator_data
        assert 'market' in model.indicator_data
        assert model.last_update is not None
    
    def test_load_indicators_without_market_data(self, model, sample_fred_data):
        """Test loading indicator data without market data."""
        model.load_indicators_from_data(sample_fred_data)
        
        assert 'fred' in model.indicator_data
        assert 'market' not in model.indicator_data
    
    def test_calculate_recession_probability(self, model, sample_fred_data):
        """Test calculating recession probability."""
        model.load_indicators_from_data(sample_fred_data)
        result = model.calculate_recession_probability()
        
        assert 'probability' in result
        assert 'risk_level' in result
        assert 'signals' in result
        assert 'details' in result
        assert 'weights' in result
        
        # Probability should be between 0 and 1
        assert 0 <= result['probability'] <= 1
        
        # Risk level should be one of the defined levels
        assert result['risk_level'] in ['LOW', 'MODERATE', 'ELEVATED', 'HIGH']
    
    def test_calculate_recession_probability_without_data(self, model):
        """Test that calculation fails without loaded data."""
        with pytest.raises(ValueError, match="No indicator data loaded"):
            model.calculate_recession_probability()
    
    def test_signals_are_calculated(self, model, sample_fred_data):
        """Test that all expected signals are calculated."""
        model.load_indicators_from_data(sample_fred_data)
        result = model.calculate_recession_probability()
        
        expected_signals = [
            'yield_curve_signal',
            'labor_market_signal',
            'financial_stress_signal',
            'economic_activity_signal',
            'consumer_signal',
            'housing_signal',
            'market_signal',
        ]
        
        for signal_name in expected_signals:
            assert signal_name in result['signals']
            # Each signal should be between 0 and 1
            assert 0 <= result['signals'][signal_name] <= 1
    
    def test_indicator_weights_sum_to_one(self):
        """Test that indicator weights sum to exactly 1."""
        total_weight = sum(INDICATOR_WEIGHTS.values())
        assert total_weight == 1.0, f"Weights sum to {total_weight}, expected 1.0"
    
    def test_yield_curve_inversion_increases_signal(self, model):
        """Test that yield curve inversion increases the yield curve signal."""
        dates = pd.date_range(end=datetime.now(), periods=24, freq='ME')
        
        # Normal yield curve (positive spread)
        normal_data = pd.DataFrame({
            'yield_spread_10y2y': [1.5] * 24,
            'yield_spread_10y3m': [2.0] * 24,
        }, index=dates)
        
        # Inverted yield curve (negative spread)
        inverted_data = pd.DataFrame({
            'yield_spread_10y2y': [-0.5] * 24,
            'yield_spread_10y3m': [-0.3] * 24,
        }, index=dates)
        
        # Calculate with normal curve
        model.load_indicators_from_data(normal_data)
        normal_result = model.calculate_recession_probability()
        normal_signal = normal_result['signals']['yield_curve_signal']
        
        # Calculate with inverted curve
        model.load_indicators_from_data(inverted_data)
        inverted_result = model.calculate_recession_probability()
        inverted_signal = inverted_result['signals']['yield_curve_signal']
        
        # Inverted curve should produce higher signal
        assert inverted_signal > normal_signal
    
    def test_high_unemployment_increases_labor_signal(self, model):
        """Test that high/rising unemployment increases the labor signal."""
        dates = pd.date_range(end=datetime.now(), periods=24, freq='ME')
        
        # Low, stable unemployment
        low_unemp_data = pd.DataFrame({
            'unemployment_rate': [3.5] * 24,
            'initial_claims': [200000] * 24,
        }, index=dates)
        
        # High, rising unemployment (simulating Sahm rule trigger)
        high_unemp_values = list(np.linspace(3.5, 4.5, 24))  # Rising unemployment
        high_unemp_data = pd.DataFrame({
            'unemployment_rate': high_unemp_values,
            'initial_claims': [350000] * 24,
        }, index=dates)
        
        # Calculate with low unemployment
        model.load_indicators_from_data(low_unemp_data)
        low_result = model.calculate_recession_probability()
        low_signal = low_result['signals']['labor_market_signal']
        
        # Calculate with high unemployment
        model.load_indicators_from_data(high_unemp_data)
        high_result = model.calculate_recession_probability()
        high_signal = high_result['signals']['labor_market_signal']
        
        # High/rising unemployment should produce higher signal
        assert high_signal > low_signal
    
    def test_get_indicator_explanations(self, model):
        """Test that explanations are provided for all indicators."""
        explanations = model.get_indicator_explanations()
        
        expected_keys = [
            'yield_curve_signal',
            'labor_market_signal',
            'financial_stress_signal',
            'economic_activity_signal',
            'consumer_signal',
            'housing_signal',
            'market_signal',
        ]
        
        for key in expected_keys:
            assert key in explanations
            assert len(explanations[key]) > 0  # Should have non-empty explanation
    
    def test_risk_level_thresholds(self, model):
        """Test that risk levels are assigned correctly based on probability."""
        dates = pd.date_range(end=datetime.now(), periods=24, freq='ME')
        
        # Create data that should produce LOW risk (minimal indicators)
        low_risk_data = pd.DataFrame({
            'yield_spread_10y2y': [2.0] * 24,
            'unemployment_rate': [3.5] * 24,
            'consumer_sentiment': [100] * 24,
            'real_gdp_growth': [3.0] * 24,
            'building_permits': [1500] * 24,
        }, index=dates)
        
        model.load_indicators_from_data(low_risk_data)
        result = model.calculate_recession_probability()
        
        # With positive indicators, should have lower probability
        assert result['probability'] < 0.5
    
    def test_details_contain_indicator_values(self, model, sample_fred_data):
        """Test that details contain specific indicator values."""
        model.load_indicators_from_data(sample_fred_data)
        result = model.calculate_recession_probability()
        
        details = result['details']
        
        # Check yield curve details
        assert 'yield_curve' in details
        if sample_fred_data['yield_spread_10y2y'].dropna().any():
            assert '10y2y_spread' in details['yield_curve']
        
        # Check labor market details
        assert 'labor_market' in details
        if sample_fred_data['unemployment_rate'].dropna().any():
            assert 'unemployment_rate' in details['labor_market']


class TestRecessionIndicatorSeries:
    """Test cases for recession indicator configuration."""
    
    def test_get_recession_indicator_series(self):
        """Test that the indicator series dictionary is valid."""
        series = get_recession_indicator_series()
        
        assert isinstance(series, dict)
        assert len(series) > 0
        
        # All values should be non-None FRED series IDs
        for name, series_id in series.items():
            assert series_id is not None
            assert isinstance(series_id, str)
            assert len(series_id) > 0
    
    def test_recession_indicator_series_contains_key_indicators(self):
        """Test that key recession indicators are present."""
        series = get_recession_indicator_series()
        
        expected_indicators = [
            'yield_spread_10y2y',
            'unemployment_rate',
            'fed_funds_rate',
        ]
        
        for indicator in expected_indicators:
            assert indicator in series


class TestIndicatorWeights:
    """Test cases for indicator weights configuration."""
    
    def test_weights_are_positive(self):
        """Test that all weights are positive."""
        for key, weight in INDICATOR_WEIGHTS.items():
            assert weight > 0, f"Weight for {key} should be positive"
    
    def test_weights_are_reasonable(self):
        """Test that no single weight dominates."""
        for key, weight in INDICATOR_WEIGHTS.items():
            assert weight <= 0.5, f"Weight for {key} should not exceed 50%"
    
    def test_all_expected_weights_present(self):
        """Test that weights are defined for all expected signals."""
        expected_signals = [
            'yield_curve_signal',
            'labor_market_signal',
            'financial_stress_signal',
            'economic_activity_signal',
            'consumer_signal',
            'housing_signal',
            'market_signal',
        ]
        
        for signal in expected_signals:
            assert signal in INDICATOR_WEIGHTS, f"Missing weight for {signal}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
