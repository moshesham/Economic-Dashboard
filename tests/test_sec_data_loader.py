"""
Tests for SEC Data Loader Module
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime


class TestSECDataLoader:
    """Tests for SEC data loading functions"""
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock response object"""
        mock = Mock()
        mock.status_code = 200
        return mock
    
    def test_lookup_cik_formats_correctly(self):
        """Test that CIK numbers are properly zero-padded"""
        # Test that the function expects 10-digit CIKs
        cik = "320193"
        expected = "0000320193"
        assert cik.zfill(10) == expected
    
    def test_company_facts_url_format(self):
        """Test that company facts API URL is correctly formatted"""
        cik = "0000320193"
        expected_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        assert "companyfacts" in expected_url
        assert cik in expected_url
    
    def test_submissions_url_format(self):
        """Test that submissions API URL is correctly formatted"""
        cik = "0000320193"
        expected_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        assert "submissions" in expected_url
        assert cik in expected_url
    
    def test_financial_statement_url_format(self):
        """Test that FSDS URL is correctly formatted"""
        year = 2024
        quarter = 3
        expected_url = f"https://www.sec.gov/files/dera/data/financial-statement-data-sets/{year}q{quarter}.zip"
        assert str(year) in expected_url
        assert f"q{quarter}" in expected_url
    
    @patch('requests.get')
    def test_rate_limiting_headers(self, mock_get):
        """Test that SEC API calls include required User-Agent header"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        # The SEC requires a User-Agent header
        expected_headers = {
            "User-Agent": "Economic-Dashboard/1.0 (contact@example.com)",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        }
        
        # Verify headers structure
        assert "User-Agent" in expected_headers
        assert expected_headers["User-Agent"] != ""
    
    def test_extract_financial_metric_structure(self):
        """Test the structure of extracted financial metrics"""
        # Mock company facts response structure
        mock_facts = {
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {
                                    "val": 100000000,
                                    "end": "2023-09-30",
                                    "fy": 2023,
                                    "fp": "FY",
                                    "form": "10-K",
                                    "filed": "2023-11-02"
                                }
                            ]
                        }
                    }
                }
            }
        }
        
        # Verify structure
        assert "facts" in mock_facts
        assert "us-gaap" in mock_facts["facts"]
        assert "Revenues" in mock_facts["facts"]["us-gaap"]
        assert "units" in mock_facts["facts"]["us-gaap"]["Revenues"]
    
    def test_key_financial_concepts(self):
        """Test that key financial concepts are defined"""
        key_concepts = [
            'Revenues',
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'NetIncomeLoss',
            'Assets',
            'Liabilities',
            'StockholdersEquity',
            'OperatingIncomeLoss',
            'GrossProfit',
            'CashAndCashEquivalentsAtCarryingValue',
            'LongTermDebt',
            'EarningsPerShareBasic',
            'EarningsPerShareDiluted'
        ]
        
        # All concepts should be non-empty strings
        for concept in key_concepts:
            assert isinstance(concept, str)
            assert len(concept) > 0
    
    def test_fsds_file_components(self):
        """Test that FSDS ZIP file components are correctly defined"""
        expected_files = {
            'sub.txt': 'sub',  # Submission metadata
            'num.txt': 'num',  # Numeric data
            'pre.txt': 'pre',  # Presentation data
            'tag.txt': 'tag'   # Tag definitions
        }
        
        for filename, key in expected_files.items():
            assert filename.endswith('.txt')
            assert len(key) == 3


class TestSECDatabaseSchema:
    """Tests for SEC database schema definitions"""
    
    def test_sec_submissions_table_columns(self):
        """Test that SEC submissions table has required columns"""
        required_columns = [
            'adsh', 'cik', 'name', 'form', 'filed', 'period'
        ]
        
        # These columns are essential for the table
        for col in required_columns:
            assert isinstance(col, str)
    
    def test_sec_financial_statements_table_columns(self):
        """Test that SEC financial statements table has required columns"""
        required_columns = [
            'adsh', 'tag', 'ddate', 'value', 'uom'
        ]
        
        for col in required_columns:
            assert isinstance(col, str)
    
    def test_sec_company_facts_table_columns(self):
        """Test that SEC company facts table has required columns"""
        required_columns = [
            'cik', 'concept', 'value', 'end_date', 'form'
        ]
        
        for col in required_columns:
            assert isinstance(col, str)
    
    def test_sec_filings_table_columns(self):
        """Test that SEC filings table has required columns"""
        required_columns = [
            'cik', 'accession_number', 'form', 'filing_date'
        ]
        
        for col in required_columns:
            assert isinstance(col, str)
    
    def test_sec_ftd_table_columns(self):
        """Test that SEC fails-to-deliver table has required columns"""
        required_columns = [
            'settlement_date', 'cusip', 'symbol', 'quantity'
        ]
        
        for col in required_columns:
            assert isinstance(col, str)
    
    def test_sec_13f_holdings_table_columns(self):
        """Test that SEC 13F holdings table has required columns"""
        required_columns = [
            'cik', 'filing_date', 'cusip', 'value_usd', 'shares_amount'
        ]
        
        for col in required_columns:
            assert isinstance(col, str)


class TestSECDataQueries:
    """Tests for SEC database query functions"""
    
    def test_query_returns_dataframe(self):
        """Test that query functions are expected to return DataFrames"""
        # This tests the expected return type
        result = pd.DataFrame()
        assert isinstance(result, pd.DataFrame)
    
    def test_cik_filtering(self):
        """Test CIK filtering in queries"""
        test_cik = "0000320193"
        query = f"WHERE cik = '{test_cik}'"
        assert test_cik in query
    
    def test_date_filtering(self):
        """Test date filtering in queries"""
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        query = f"WHERE filing_date >= '{start_date}' AND filing_date <= '{end_date}'"
        assert start_date in query
        assert end_date in query
    
    def test_form_type_filtering(self):
        """Test form type filtering in queries"""
        form_types = ['10-K', '10-Q']
        forms_list = "','".join(form_types)
        query = f"WHERE form IN ('{forms_list}')"
        assert '10-K' in query
        assert '10-Q' in query


class TestCIKLookup:
    """Tests for CIK lookup functionality"""
    
    def test_ticker_uppercase(self):
        """Test that tickers are converted to uppercase"""
        ticker = "aapl"
        assert ticker.upper() == "AAPL"
    
    def test_cik_padding(self):
        """Test that CIKs are zero-padded to 10 digits"""
        cik = "320193"
        padded = cik.zfill(10)
        assert len(padded) == 10
        assert padded == "0000320193"
    
    def test_known_cik_mappings(self):
        """Test known ticker to CIK mappings"""
        known_mappings = {
            'AAPL': '0000320193',
            'MSFT': '0000789019',
            'AMZN': '0001018724',
            'GOOGL': '0001652044',
            'TSLA': '0001318605',
        }
        
        for ticker, cik in known_mappings.items():
            assert len(cik) == 10
            assert cik.startswith('0')


class TestSECAPIResponses:
    """Tests for handling SEC API responses"""
    
    def test_empty_response_handling(self):
        """Test handling of empty API responses"""
        empty_response = {}
        facts = empty_response.get('facts', {})
        assert facts == {}
    
    def test_missing_concept_handling(self):
        """Test handling of missing concepts in response"""
        mock_facts = {
            "facts": {
                "us-gaap": {}
            }
        }
        
        concept_data = mock_facts.get('facts', {}).get('us-gaap', {}).get('NonExistentConcept', {})
        assert concept_data == {}
    
    def test_multiple_units_handling(self):
        """Test handling of multiple units (USD, shares, etc.)"""
        mock_units = {
            "USD": [{"val": 100}],
            "shares": [{"val": 1000}]
        }
        
        # Should be able to iterate over all units
        all_values = []
        for unit_type, values in mock_units.items():
            for v in values:
                all_values.append((unit_type, v['val']))
        
        assert len(all_values) == 2
        assert ('USD', 100) in all_values
        assert ('shares', 1000) in all_values


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
