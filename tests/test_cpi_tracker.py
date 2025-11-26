"""
Unit tests for CPI Inflation Tracker module.
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


class TestCPIBasketConfig:
    """Test cases for CPI basket configuration."""
    
    def test_cpi_basket_structure(self):
        """Test that CPI basket has correct structure."""
        from modules.cpi_basket_config import CPI_BASKET, CPIItem
        
        assert len(CPI_BASKET) > 0
        assert 'food_and_beverages' in CPI_BASKET
        assert 'housing' in CPI_BASKET
        assert 'transportation' in CPI_BASKET
        assert 'medical_care' in CPI_BASKET
        
        # Check that each category has items
        for category, items in CPI_BASKET.items():
            assert len(items) > 0
            for item in items:
                assert isinstance(item, CPIItem)
                assert item.name
                assert item.fred_series_id
                assert item.weight > 0
                assert item.category
    
    def test_cpi_headline_indices(self):
        """Test headline CPI indices configuration."""
        from modules.cpi_basket_config import CPI_HEADLINE_INDICES
        
        assert 'all_items' in CPI_HEADLINE_INDICES
        assert 'core_cpi' in CPI_HEADLINE_INDICES
        assert 'food' in CPI_HEADLINE_INDICES
        assert 'energy' in CPI_HEADLINE_INDICES
        
        # Check headline series IDs
        assert CPI_HEADLINE_INDICES['all_items'].fred_series_id == 'CPIAUCSL'
        assert CPI_HEADLINE_INDICES['core_cpi'].fred_series_id == 'CPILFESL'
    
    def test_get_all_cpi_items(self):
        """Test getting all CPI items."""
        from modules.cpi_basket_config import get_all_cpi_items
        
        items = get_all_cpi_items()
        assert len(items) > 40  # Should have many items
        
        # Check items have required fields
        for item in items:
            assert item.name
            assert item.fred_series_id
            assert item.weight >= 0
    
    def test_get_all_fred_series(self):
        """Test getting all FRED series as dictionary."""
        from modules.cpi_basket_config import get_all_fred_series
        
        series = get_all_fred_series()
        assert isinstance(series, dict)
        assert len(series) > 50
        
        # Check known series
        assert 'CPI All Items' in series
        assert series['CPI All Items'] == 'CPIAUCSL'
    
    def test_get_primary_series(self):
        """Test getting primary CPI series for efficient loading."""
        from modules.cpi_basket_config import get_primary_series
        
        series = get_primary_series()
        assert isinstance(series, dict)
        assert len(series) >= 10
        
        # Check key series are included
        assert 'CPI All Items' in series
        assert 'Core CPI (Less Food and Energy)' in series
    
    def test_get_headline_series(self):
        """Test getting headline series dictionary."""
        from modules.cpi_basket_config import get_headline_series
        
        series = get_headline_series()
        assert isinstance(series, dict)
        assert len(series) == 6
        
        # Verify series IDs
        series_ids = set(series.values())
        assert 'CPIAUCSL' in series_ids
        assert 'CPILFESL' in series_ids
    
    def test_category_weights_sum(self):
        """Test that major category weights are reasonable."""
        from modules.cpi_basket_config import get_category_weights
        
        weights = get_category_weights()
        assert isinstance(weights, dict)
        
        # Housing should be the largest
        assert weights['housing'] > 30  # ~44% of CPI
        
        # Total of main categories should be reasonable
        total = sum(weights.values())
        assert 50 < total < 120  # Approximate sum with subcategories
    
    def test_cache_ttl_configuration(self):
        """Test cache TTL configuration."""
        from modules.cpi_basket_config import (
            get_cache_ttl, 
            get_max_cache_age,
            CPI_UPDATE_SCHEDULE
        )
        
        ttl = get_cache_ttl()
        max_age = get_max_cache_age()
        
        assert isinstance(ttl, timedelta)
        assert isinstance(max_age, timedelta)
        assert ttl < max_age
        assert CPI_UPDATE_SCHEDULE['frequency'] == 'monthly'


class TestCPIDatabaseSchema:
    """Test cases for CPI database schema."""
    
    def test_create_cpi_tables(self):
        """Test CPI table creation."""
        from modules.database.schema import (
            create_cpi_basket_items_table,
            create_cpi_price_data_table,
            create_cpi_inflation_summary_table,
            create_cpi_category_breakdown_table,
        )
        from modules.database import get_db_connection
        
        # Create tables (should not raise)
        create_cpi_basket_items_table()
        create_cpi_price_data_table()
        create_cpi_inflation_summary_table()
        create_cpi_category_breakdown_table()
        
        # Verify tables exist
        db = get_db_connection()
        tables = db.query(
            "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'cpi_%'"
        )
        table_names = set(tables['table_name'])
        
        assert 'cpi_basket_items' in table_names
        assert 'cpi_price_data' in table_names
        assert 'cpi_inflation_summary' in table_names
        assert 'cpi_category_breakdown' in table_names


class TestCPIDatabaseQueries:
    """Test cases for CPI database queries."""
    
    @pytest.fixture(autouse=True)
    def setup_tables(self):
        """Ensure CPI tables exist before each test."""
        from modules.database.schema import (
            create_cpi_basket_items_table,
            create_cpi_price_data_table,
            create_cpi_inflation_summary_table,
            create_cpi_category_breakdown_table,
        )
        create_cpi_basket_items_table()
        create_cpi_price_data_table()
        create_cpi_inflation_summary_table()
        create_cpi_category_breakdown_table()
    
    def test_insert_and_get_cpi_price_data(self):
        """Test inserting and retrieving CPI price data."""
        from modules.database.queries import (
            insert_cpi_price_data,
            get_cpi_price_data,
        )
        import uuid
        
        # Create unique series ID for test isolation
        test_id = f"TEST_{uuid.uuid4().hex[:8]}"
        
        # Create sample data
        sample_data = pd.DataFrame({
            'series_id': [test_id, test_id, f"{test_id}_2"],
            'date': pd.date_range('2024-01-01', periods=3, freq='MS'),
            'value': [300.0, 301.0, 290.0],
            'yoy_change': [6.0, 5.5, 5.0],
            'mom_change': [0.3, 0.2, 0.25],
        })
        
        # Insert data
        count = insert_cpi_price_data(sample_data)
        assert count == 3
        
        # Retrieve data
        result = get_cpi_price_data([test_id])
        assert not result.empty
        assert len(result[result['series_id'] == test_id]) >= 2
    
    def test_insert_and_get_inflation_summary(self):
        """Test inserting and retrieving inflation summary."""
        from modules.database.queries import (
            insert_cpi_inflation_summary,
            get_cpi_inflation_summary,
        )
        import random
        
        # Use unique dates to avoid conflicts
        year = 2024 + random.randint(10, 99)
        
        # Create sample summary
        sample_summary = pd.DataFrame({
            'date': [datetime(year, 1, 1), datetime(year, 2, 1)],
            'headline_cpi': [300.0, 301.0],
            'core_cpi': [290.0, 291.0],
            'headline_yoy': [6.0, 5.8],
            'core_yoy': [5.5, 5.3],
        })
        
        # Insert
        count = insert_cpi_inflation_summary(sample_summary)
        assert count == 2
        
        # Retrieve
        result = get_cpi_inflation_summary()
        assert not result.empty
    
    def test_get_latest_cpi_values(self):
        """Test getting latest CPI values."""
        from modules.database.queries import (
            insert_cpi_price_data,
            get_latest_cpi_values,
        )
        import uuid
        
        # Insert some data first with unique series ID
        test_series = f"TEST_LATEST_{uuid.uuid4().hex[:8]}"
        sample_data = pd.DataFrame({
            'series_id': [test_series, test_series],
            'date': [datetime(2025, 1, 1), datetime(2025, 2, 1)],
            'value': [300.0, 302.0],
            'yoy_change': [6.0, 5.8],
            'mom_change': [0.3, 0.4],
        })
        insert_cpi_price_data(sample_data)
        
        # Get latest values
        result = get_latest_cpi_values()
        assert not result.empty
        
        # Should return only the latest date for each series
        test_rows = result[result['series_id'] == test_series]
        assert len(test_rows) <= 1
    
    def test_get_cpi_data_freshness(self):
        """Test data freshness query."""
        from modules.database.queries import get_cpi_data_freshness
        
        result = get_cpi_data_freshness()
        assert not result.empty
        assert 'source' in result.columns
        assert 'latest_date' in result.columns
        assert 'total_records' in result.columns


class TestCPIRefreshScript:
    """Test cases for CPI data refresh script."""
    
    def test_ensure_cpi_tables_exist(self):
        """Test table creation function."""
        from scripts.refresh_cpi_data import ensure_cpi_tables_exist
        
        result = ensure_cpi_tables_exist()
        assert result is True
    
    @patch('scripts.refresh_cpi_data.pdr.DataReader')
    def test_fetch_cpi_series_data(self, mock_datareader):
        """Test fetching CPI series data."""
        from scripts.refresh_cpi_data import fetch_cpi_series_data
        
        # Mock FRED data
        mock_df = pd.DataFrame({
            'CPIAUCSL': [300.0, 301.0, 302.0]
        }, index=pd.date_range('2023-01-01', periods=3, freq='MS'))
        mock_datareader.return_value = mock_df
        
        series = {'CPI All Items': 'CPIAUCSL'}
        result = fetch_cpi_series_data(series, years_back=1)
        
        assert not result.empty
        assert 'series_id' in result.columns
        assert 'value' in result.columns
        assert 'yoy_change' in result.columns
        assert 'mom_change' in result.columns
    
    def test_calculate_inflation_summary(self):
        """Test inflation summary calculation."""
        from scripts.refresh_cpi_data import calculate_inflation_summary
        
        # Create sample price data
        price_data = pd.DataFrame({
            'series_id': ['CPIAUCSL', 'CPIAUCSL', 'CPILFESL', 'CPILFESL'],
            'date': [datetime(2023, 1, 1), datetime(2023, 2, 1),
                     datetime(2023, 1, 1), datetime(2023, 2, 1)],
            'value': [300.0, 301.0, 290.0, 291.0],
            'yoy_change': [6.0, 5.8, 5.5, 5.3],
            'mom_change': [0.3, 0.2, 0.25, 0.2],
        })
        
        result = calculate_inflation_summary(price_data)
        
        assert not result.empty
        assert 'headline_cpi' in result.columns
        assert 'headline_yoy' in result.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
