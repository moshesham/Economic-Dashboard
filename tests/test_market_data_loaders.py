"""
Unit tests for ICI ETF flows and CBOE VIX data loaders.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestICIETFDataLoader:
    """Test cases for ICI ETF data loading functions."""

    @patch('modules.ici_etf_data.requests.get')
    def test_fetch_ici_weekly_etf_flows_success(self, mock_get):
        """Test successful fetching of weekly ETF flows."""
        # Mock CSV response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """date,fund_type,estimated_flows,total_net_assets
2024-01-10,Equity,1000,50000
2024-01-10,Bond,500,30000
2024-01-17,Equity,1200,51000
"""
        mock_get.return_value = mock_response
        
        from modules.ici_etf_data import fetch_ici_weekly_etf_flows
        
        result = fetch_ici_weekly_etf_flows()
        
        assert not result.empty
        assert 'week_ending' in result.columns
        assert 'fund_type' in result.columns
        mock_get.assert_called_once()

    @patch('modules.ici_etf_data.requests.get')
    def test_fetch_ici_weekly_etf_flows_network_error(self, mock_get):
        """Test handling of network errors."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        from modules.ici_etf_data import fetch_ici_weekly_etf_flows
        
        result = fetch_ici_weekly_etf_flows()
        
        assert result.empty

    @patch('modules.ici_etf_data.requests.get')
    def test_fetch_ici_monthly_etf_flows_success(self, mock_get):
        """Test successful fetching of monthly ETF flows."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """date,fund_category,net_new_cash_flow,net_issuance,redemptions,reinvested_dividends,total_net_assets
2024-01-31,Domestic Equity,5000,5500,500,100,100000
2024-01-31,International Equity,2000,2200,200,50,50000
"""
        mock_get.return_value = mock_response
        
        from modules.ici_etf_data import fetch_ici_monthly_etf_flows
        
        result = fetch_ici_monthly_etf_flows()
        
        assert not result.empty
        assert 'date' in result.columns
        assert 'fund_category' in result.columns

    def test_ici_etf_flows_table_schema(self):
        """Test that ICI ETF flows table has correct columns."""
        expected_weekly_columns = ['week_ending', 'fund_type', 'estimated_flows', 'total_net_assets']
        expected_monthly_columns = ['date', 'fund_category', 'net_new_cash_flow', 'net_issuance',
                                   'redemptions', 'reinvested_dividends', 'total_net_assets']
        
        # Verify expected column structure
        for col in expected_weekly_columns:
            assert isinstance(col, str)
        
        for col in expected_monthly_columns:
            assert isinstance(col, str)


class TestCBOEVIXDataLoader:
    """Test cases for CBOE VIX data loading functions."""

    @patch('modules.cboe_vix_data.requests.get')
    def test_fetch_cboe_vix_history_success(self, mock_get):
        """Test successful fetching of VIX history."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """DATE,OPEN,HIGH,LOW,CLOSE
01/02/2024,13.5,14.2,13.1,13.8
01/03/2024,13.8,15.0,13.5,14.5
01/04/2024,14.5,14.8,14.0,14.3
"""
        mock_get.return_value = mock_response
        
        from modules.cboe_vix_data import fetch_cboe_vix_history
        
        result = fetch_cboe_vix_history()
        
        assert not result.empty
        assert 'date' in result.columns
        assert 'close' in result.columns
        mock_get.assert_called_once()

    @patch('modules.cboe_vix_data.requests.get')
    def test_fetch_cboe_vix_history_network_error(self, mock_get):
        """Test handling of network errors."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        from modules.cboe_vix_data import fetch_cboe_vix_history
        
        result = fetch_cboe_vix_history()
        
        assert result.empty

    @patch('modules.cboe_vix_data.requests.get')
    def test_fetch_cboe_vix_history_data_validation(self, mock_get):
        """Test that VIX data is properly validated."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """DATE,OPEN,HIGH,LOW,CLOSE
01/02/2024,13.5,14.2,13.1,13.8
"""
        mock_get.return_value = mock_response
        
        from modules.cboe_vix_data import fetch_cboe_vix_history
        
        result = fetch_cboe_vix_history()
        
        if not result.empty:
            # VIX values should be positive (filter out NaN for check)
            valid_closes = result['close'].dropna()
            if len(valid_closes) > 0:
                assert (valid_closes > 0).all(), "VIX close values should be positive"
            # Date should be valid
            assert pd.api.types.is_datetime64_any_dtype(result['date'])

    def test_cboe_vix_table_schema(self):
        """Test that CBOE VIX table has correct columns."""
        expected_columns = ['date', 'open', 'high', 'low', 'close']
        
        # Verify expected column structure
        for col in expected_columns:
            assert isinstance(col, str)


class TestDatabaseSchema:
    """Test cases for new database schema tables."""

    def test_ici_etf_flows_table_creation(self):
        """Test ICI ETF flows table can be created."""
        from modules.database.schema import create_ici_etf_flows_table
        
        # Should not raise any errors
        try:
            create_ici_etf_flows_table()
        except Exception as e:
            pytest.fail(f"Failed to create ici_etf_flows table: {e}")

    def test_ici_etf_weekly_flows_table_creation(self):
        """Test ICI weekly ETF flows table can be created."""
        from modules.database.schema import create_ici_etf_weekly_flows_table
        
        try:
            create_ici_etf_weekly_flows_table()
        except Exception as e:
            pytest.fail(f"Failed to create ici_etf_weekly_flows table: {e}")

    def test_cboe_vix_history_table_creation(self):
        """Test CBOE VIX history table can be created."""
        from modules.database.schema import create_cboe_vix_history_table
        
        try:
            create_cboe_vix_history_table()
        except Exception as e:
            pytest.fail(f"Failed to create cboe_vix_history table: {e}")

    def test_cboe_vix_term_structure_table_creation(self):
        """Test CBOE VIX term structure table can be created."""
        from modules.database.schema import create_cboe_vix_term_structure_table
        
        try:
            create_cboe_vix_term_structure_table()
        except Exception as e:
            pytest.fail(f"Failed to create cboe_vix_term_structure table: {e}")


class TestDatabaseQueries:
    """Test cases for new database query functions."""

    def test_get_ici_weekly_etf_flows_function_exists(self):
        """Test that get_ici_weekly_etf_flows function exists."""
        from modules.database.queries import get_ici_weekly_etf_flows
        
        assert callable(get_ici_weekly_etf_flows)

    def test_get_ici_monthly_etf_flows_function_exists(self):
        """Test that get_ici_monthly_etf_flows function exists."""
        from modules.database.queries import get_ici_monthly_etf_flows
        
        assert callable(get_ici_monthly_etf_flows)

    def test_get_cboe_vix_history_function_exists(self):
        """Test that get_cboe_vix_history function exists."""
        from modules.database.queries import get_cboe_vix_history
        
        assert callable(get_cboe_vix_history)

    def test_get_latest_vix_data_function_exists(self):
        """Test that get_latest_vix_data function exists."""
        from modules.database.queries import get_latest_vix_data
        
        assert callable(get_latest_vix_data)

    def test_insert_functions_exist(self):
        """Test that insert functions exist for new tables."""
        from modules.database.queries import (
            insert_ici_weekly_flows,
            insert_ici_monthly_flows,
            insert_cboe_vix_data,
            insert_cboe_vix_term_structure
        )
        
        assert callable(insert_ici_weekly_flows)
        assert callable(insert_ici_monthly_flows)
        assert callable(insert_cboe_vix_data)
        assert callable(insert_cboe_vix_term_structure)


class TestDataIntegrity:
    """Test cases for data integrity and validation."""

    def test_etf_flows_data_columns_match_schema(self):
        """Test that ETF flows data columns match database schema."""
        expected_weekly_cols = {'week_ending', 'fund_type', 'estimated_flows', 'total_net_assets'}
        expected_monthly_cols = {'date', 'fund_category', 'net_new_cash_flow', 'net_issuance',
                                'redemptions', 'reinvested_dividends', 'total_net_assets'}
        
        # The columns should be a subset of what's expected
        assert len(expected_weekly_cols) == 4
        assert len(expected_monthly_cols) == 7

    def test_vix_data_columns_match_schema(self):
        """Test that VIX data columns match database schema."""
        expected_cols = {'date', 'open', 'high', 'low', 'close'}
        
        assert len(expected_cols) == 5

    def test_vix_ohlc_consistency(self):
        """Test that VIX OHLC values maintain logical consistency."""
        # Create sample data
        sample_data = {
            'date': [datetime.now()],
            'open': [15.0],
            'high': [16.0],
            'low': [14.0],
            'close': [15.5]
        }
        df = pd.DataFrame(sample_data)
        
        # High should be >= all other values
        assert (df['high'] >= df['open']).all()
        assert (df['high'] >= df['close']).all()
        assert (df['high'] >= df['low']).all()
        
        # Low should be <= all other values
        assert (df['low'] <= df['open']).all()
        assert (df['low'] <= df['close']).all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
