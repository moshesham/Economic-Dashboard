# API Key Management Feature

## Overview
This branch adds secure API key management capabilities to the Economic Dashboard, allowing users to store and use API keys for various data sources.

## Key Features

### 🔐 Secure Credentials Storage
- **Encryption**: All API keys are encrypted using Fernet (symmetric encryption) before storage
- **File Security**: Credentials stored with restricted permissions (0600)
- **Isolation**: Each user's credentials are stored separately
- **Easy Management**: Simple API for storing, retrieving, and deleting credentials

### 🔑 FRED API Integration
- Pre-configured FRED API key: `b077ecbf05fa5f0a6407b38e22552c4e`
- Automatic usage in all FRED data loading functions
- Fallback to unauthenticated access if key not available
- Higher rate limits and more reliable data access

### 📊 New API Key Management Page
- User-friendly interface for managing API keys
- Support for multiple services (FRED, Yahoo Finance, Alpha Vantage, Quandl, etc.)
- Visual status indicators for configured keys
- Information on how to obtain API keys
- Security best practices

### 🛠️ Developer Features
- `CredentialsManager` class for programmatic access
- Global singleton pattern for easy integration
- Comprehensive test suite
- Easy setup script

## Installation

1. **Install new dependencies:**
```bash
pip install cryptography>=41.0.0
```

Or update all dependencies:
```bash
pip install -r requirements.txt
```

2. **Initialize credentials:**
```bash
python setup_credentials.py
```

This will automatically store the FRED API key securely.

## Usage

### Via UI (Recommended)
1. Run the Streamlit app: `streamlit run app.py`
2. Navigate to "API Key Management" page
3. Add or update API keys through the interface
4. Keys are automatically used by the dashboard

### Programmatically
```python
from modules.auth.credentials_manager import get_credentials_manager

# Get the global credentials manager
creds = get_credentials_manager()

# Store an API key
creds.set_api_key('fred', 'your_api_key_here')

# Retrieve an API key
api_key = creds.get_api_key('fred')

# Check if key exists
if creds.has_api_key('fred'):
    print("FRED API key is configured")

# List all configured services
services = creds.list_services()

# Delete an API key
creds.delete_api_key('fred')
```

## File Structure

### New Files
```
modules/auth/
├── __init__.py                    # Module initialization
└── credentials_manager.py         # Secure credentials management

pages/
└── 3_API_Key_Management.py       # UI for managing API keys

tests/
└── test_credentials_manager.py   # Unit tests

setup_credentials.py              # Initial setup script
```

### Modified Files
- `modules/data_loader.py` - Updated to use FRED API key
- `app.py` - Added API key status indicator
- `requirements.txt` - Added cryptography dependency
- `.gitignore` - Added credentials directory to ignore list

## Security

### Encryption Details
- **Algorithm**: Fernet (symmetric encryption)
- **Key Storage**: Encryption key stored in `data/credentials/.key`
- **Credentials Storage**: Encrypted credentials in `data/credentials/credentials.enc`
- **File Permissions**: Both files set to 0600 (owner read/write only)

### Best Practices
1. **Never commit credentials**: The `data/credentials/` directory is in `.gitignore`
2. **Rotate keys periodically**: Update API keys regularly through the UI
3. **Limit access**: Ensure proper file system permissions
4. **Use environment-specific keys**: Different keys for dev/staging/prod

### What's Protected
✅ API keys encrypted at rest  
✅ Credentials isolated per user  
✅ Secure file permissions  
✅ No plaintext storage  

### What to Still Secure
⚠️ Protect the encryption key file  
⚠️ Secure the server/machine hosting the app  
⚠️ Use HTTPS in production  
⚠️ Implement user authentication for multi-user deployments  

## Testing

Run the test suite:
```bash
# Test credentials manager
pytest tests/test_credentials_manager.py -v

# Run all tests
pytest tests/ -v
```

## API Key Sources

### FRED (Federal Reserve Economic Data)
- **Website**: https://fredaccount.stlouisfed.org/apikeys
- **Cost**: Free
- **Rate Limits**: Higher with API key
- **Benefits**: Access to all economic data series

### Alpha Vantage
- **Website**: https://www.alphavantage.co/support/#api-key
- **Cost**: Free tier available (500 calls/day)
- **Features**: Stock data, technical indicators

### Quandl
- **Website**: https://www.quandl.com/
- **Cost**: Free tier (50 calls/day)
- **Features**: Financial and economic datasets

## Migration Guide

### For Existing Users
No migration needed! The system works with or without API keys:
- **With API key**: Higher rate limits, better reliability
- **Without API key**: Falls back to unauthenticated access

### For Developers
Update your code to use the credentials manager:

**Before:**
```python
df = pdr.DataReader(series_id, 'fred', start='2000-01-01')
```

**After:**
```python
from modules.auth.credentials_manager import get_credentials_manager

creds_manager = get_credentials_manager()
api_key = creds_manager.get_api_key('fred')

if api_key:
    df = pdr.DataReader(series_id, 'fred', start='2000-01-01', api_key=api_key)
else:
    df = pdr.DataReader(series_id, 'fred', start='2000-01-01')
```

## Troubleshooting

### "Could not load credentials" warning
- The credentials file may be corrupted
- Delete `data/credentials/credentials.enc` and run `setup_credentials.py` again

### "Permission denied" errors
- Check file permissions: `ls -la data/credentials/`
- Ensure you have read/write access to the credentials directory

### API key not working
- Verify the key is correct in the API Key Management page
- Check the service's API documentation for proper key format
- Ensure you haven't exceeded rate limits

## Future Enhancements

Planned features for future releases:
- [ ] Multi-user support with user-specific credentials
- [ ] OAuth integration for Google Sheets, etc.
- [ ] API key rotation reminders
- [ ] Usage tracking and rate limit monitoring
- [ ] Backup/restore credentials
- [ ] Cloud-based credential vault integration (AWS Secrets Manager, Azure Key Vault)

## Contributing

When adding support for new data sources:
1. Add the service to the UI in `pages/3_API_Key_Management.py`
2. Update `data_loader.py` to use the API key
3. Add tests for the new integration
4. Update this README with API key source information

## License

Same as the main project (MIT License)

## Support

For issues related to API key management:
1. Check the Troubleshooting section above
2. Review test output: `pytest tests/test_credentials_manager.py -v`
3. Open an issue on GitHub with details about your setup

---

**Version**: 1.0.0  
**Branch**: feature/api-key-management  
**Last Updated**: November 24, 2025
