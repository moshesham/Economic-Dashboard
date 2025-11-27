"""
Initialize FRED API key and other credentials.
Run this script once to set up your API keys securely.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from modules.auth.credentials_manager import get_credentials_manager


def initialize_credentials():
    """Initialize API credentials"""
    print("🔐 API Credentials Setup")
    print("=" * 50)
    
    creds_manager = get_credentials_manager()
    
    # FRED API Key
    print("\nSetting up FRED API key...")
    fred_key = "b077ecbf05fa5f0a6407b38e22552c4e"
    creds_manager.set_api_key('fred', fred_key)
    print("✅ FRED API key stored securely")
    
    # Display stored services
    print("\n📋 Configured API Keys:")
    for service in creds_manager.list_services():
        print(f"  ✓ {service}")
    
    print("\n" + "=" * 50)
    print("✅ Credentials initialized successfully!")
    print("\nYou can now use the dashboard with authenticated API access.")
    print("Credentials are encrypted and stored in: data/credentials/")


if __name__ == "__main__":
    initialize_credentials()
