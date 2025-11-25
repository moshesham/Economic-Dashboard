"""
Secure credentials management for API keys and authentication tokens.
Provides encrypted storage and retrieval of sensitive credentials.
"""

import os
import json
from typing import Optional, Dict
from cryptography.fernet import Fernet
from pathlib import Path


class CredentialsManager:
    """Manage API keys and credentials securely"""
    
    def __init__(self, credentials_dir: str = 'data/credentials'):
        """
        Initialize credentials manager.
        
        Args:
            credentials_dir: Directory to store encrypted credentials
        """
        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load encryption key
        self.key_file = self.credentials_dir / '.key'
        self.cipher = self._init_encryption()
        
        # Credentials file
        self.creds_file = self.credentials_dir / 'credentials.enc'
    
    def _init_encryption(self) -> Fernet:
        """Initialize encryption cipher with key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new encryption key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Secure the key file
            os.chmod(self.key_file, 0o600)
        
        return Fernet(key)
    
    def _load_credentials(self) -> Dict[str, str]:
        """Load and decrypt all credentials"""
        if not self.creds_file.exists():
            return {}
        
        try:
            with open(self.creds_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Warning: Could not load credentials: {e}")
            return {}
    
    def _save_credentials(self, credentials: Dict[str, str]):
        """Encrypt and save all credentials"""
        try:
            json_data = json.dumps(credentials).encode()
            encrypted_data = self.cipher.encrypt(json_data)
            
            with open(self.creds_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Secure the credentials file
            os.chmod(self.creds_file, 0o600)
        except Exception as e:
            print(f"Error saving credentials: {e}")
    
    def set_api_key(self, service: str, api_key: str):
        """
        Store an API key securely.
        
        Args:
            service: Name of the service (e.g., 'fred', 'yahoo_finance')
            api_key: The API key to store
        """
        credentials = self._load_credentials()
        credentials[service] = api_key
        self._save_credentials(credentials)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Retrieve an API key.
        
        Args:
            service: Name of the service
            
        Returns:
            API key if found, None otherwise
        """
        credentials = self._load_credentials()
        return credentials.get(service)
    
    def delete_api_key(self, service: str) -> bool:
        """
        Delete an API key.
        
        Args:
            service: Name of the service
            
        Returns:
            True if deleted, False if not found
        """
        credentials = self._load_credentials()
        if service in credentials:
            del credentials[service]
            self._save_credentials(credentials)
            return True
        return False
    
    def list_services(self) -> list:
        """Get list of services with stored credentials"""
        credentials = self._load_credentials()
        return list(credentials.keys())
    
    def has_api_key(self, service: str) -> bool:
        """Check if API key exists for service"""
        return service in self._load_credentials()


# Global instance for easy access
_credentials_manager = None

def get_credentials_manager() -> CredentialsManager:
    """Get global credentials manager instance"""
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = CredentialsManager()
    return _credentials_manager
