"""
Unit tests for credentials manager.
"""

import pytest
import os
import tempfile
from pathlib import Path
from modules.auth.credentials_manager import CredentialsManager


class TestCredentialsManager:
    """Test cases for credentials manager."""

    @pytest.fixture
    def temp_creds_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def creds_manager(self, temp_creds_dir):
        """Create credentials manager with temp directory."""
        return CredentialsManager(credentials_dir=temp_creds_dir)

    def test_initialization(self, creds_manager, temp_creds_dir):
        """Test credentials manager initialization."""
        assert creds_manager.credentials_dir.exists()
        assert creds_manager.key_file.exists()

    def test_set_and_get_api_key(self, creds_manager):
        """Test storing and retrieving API key."""
        test_key = "test_api_key_12345"
        creds_manager.set_api_key('test_service', test_key)
        
        retrieved_key = creds_manager.get_api_key('test_service')
        assert retrieved_key == test_key

    def test_multiple_api_keys(self, creds_manager):
        """Test storing multiple API keys."""
        keys = {
            'fred': 'fred_key_123',
            'yahoo': 'yahoo_key_456',
            'worldbank': 'wb_key_789'
        }
        
        for service, key in keys.items():
            creds_manager.set_api_key(service, key)
        
        for service, key in keys.items():
            assert creds_manager.get_api_key(service) == key

    def test_delete_api_key(self, creds_manager):
        """Test deleting API key."""
        creds_manager.set_api_key('test', 'test_key')
        assert creds_manager.has_api_key('test')
        
        result = creds_manager.delete_api_key('test')
        assert result is True
        assert not creds_manager.has_api_key('test')

    def test_delete_nonexistent_key(self, creds_manager):
        """Test deleting non-existent API key."""
        result = creds_manager.delete_api_key('nonexistent')
        assert result is False

    def test_list_services(self, creds_manager):
        """Test listing configured services."""
        services = ['fred', 'yahoo', 'alpha_vantage']
        
        for service in services:
            creds_manager.set_api_key(service, f'{service}_key')
        
        listed = creds_manager.list_services()
        assert set(listed) == set(services)

    def test_has_api_key(self, creds_manager):
        """Test checking if API key exists."""
        assert not creds_manager.has_api_key('fred')
        
        creds_manager.set_api_key('fred', 'fred_key')
        assert creds_manager.has_api_key('fred')

    def test_encryption_persistence(self, temp_creds_dir):
        """Test that credentials persist across manager instances."""
        # Create first manager and set key
        manager1 = CredentialsManager(credentials_dir=temp_creds_dir)
        manager1.set_api_key('fred', 'secret_key_123')
        
        # Create second manager and retrieve key
        manager2 = CredentialsManager(credentials_dir=temp_creds_dir)
        retrieved_key = manager2.get_api_key('fred')
        
        assert retrieved_key == 'secret_key_123'

    def test_empty_credentials(self, creds_manager):
        """Test behavior with no stored credentials."""
        assert creds_manager.list_services() == []
        assert creds_manager.get_api_key('anything') is None
        assert not creds_manager.has_api_key('anything')

    def test_update_existing_key(self, creds_manager):
        """Test updating an existing API key."""
        creds_manager.set_api_key('fred', 'old_key')
        creds_manager.set_api_key('fred', 'new_key')
        
        assert creds_manager.get_api_key('fred') == 'new_key'


if __name__ == "__main__":
    pytest.main([__file__])
