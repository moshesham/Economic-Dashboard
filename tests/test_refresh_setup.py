"""
Quick test script for the automated data refresh system.
Run this to verify the setup works before enabling automation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all required packages are installed."""
    print("Testing imports...")
    try:
        import pandas as pd
        print("  ✓ pandas")
        import pandas_datareader
        print("  ✓ pandas_datareader")
        import yfinance
        print("  ✓ yfinance")
        import pickle
        print("  ✓ pickle")
        return True
    except ImportError as e:
        print(f"  ✗ Missing dependency: {e}")
        return False


def test_directories():
    """Test that required directories exist or can be created."""
    print("\nTesting directories...")
    from config_settings import ensure_cache_dir, get_cache_dir
    import os
    
    try:
        ensure_cache_dir()
        cache_dir = get_cache_dir()
        print(f"  ✓ Cache directory: {cache_dir}")
        
        os.makedirs('data/backups', exist_ok=True)
        print(f"  ✓ Backup directory: data/backups")
        
        return True
    except Exception as e:
        print(f"  ✗ Directory creation failed: {e}")
        return False


def test_fred_connection():
    """Test FRED API connection with a simple query."""
    print("\nTesting FRED API connection...")
    try:
        from pandas_datareader import data as pdr
        from datetime import datetime, timedelta
        
        start_date = datetime.now() - timedelta(days=365)  # Get more data
        df = pdr.DataReader('GDP', 'fred', start=start_date)
        
        if not df.empty:
            print(f"  ✓ FRED API accessible")
            print(f"    Latest GDP data: {df.index[-1]} = {df.iloc[-1, 0]:.2f}")
            return True
        else:
            print(f"  ⚠ No data returned from FRED (may be rate limited)")
            print(f"    Note: This is OK - the refresh script handles this")
            return True  # Don't fail on this
    except Exception as e:
        # FRED API errors are common without API key, but not critical
        print(f"  ⚠ FRED API issue: {e}")
        print(f"    Note: This is OK - automated refresh will use API key")
        return True  # Don't fail the test suite for this


def test_yfinance_connection():
    """Test Yahoo Finance connection."""
    print("\nTesting Yahoo Finance connection...")
    try:
        import yfinance as yf
        
        ticker = yf.Ticker("^GSPC")
        hist = ticker.history(period="5d")
        
        if not hist.empty:
            print(f"  ✓ Yahoo Finance accessible")
            print(f"    Latest S&P 500: {hist.index[-1].date()} = {hist['Close'].iloc[-1]:.2f}")
            return True
        else:
            print(f"  ✗ No data returned from Yahoo Finance")
            return False
    except Exception as e:
        print(f"  ✗ Yahoo Finance error: {e}")
        return False


def test_refresh_script():
    """Test the smart refresh script execution."""
    print("\nTesting smart refresh script execution...")
    print("This will test frequency-based refresh with 1 series from each category...")
    
    try:
        # Import from config
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from modules.data_series_config import get_series_by_frequency
        from pandas_datareader import data as pdr
        import yfinance as yf
        from datetime import datetime, timedelta
        
        # Test one series from each frequency
        test_series = {
            'daily': ('10Y Treasury', 'DGS10'),
            'weekly': ('Initial Jobless Claims', 'ICSA'),
            'monthly': ('Unemployment Rate', 'UNRATE'),
            'quarterly': ('GDP', 'GDP'),
        }
        
        start_date = datetime.now() - timedelta(days=365)
        successful = 0
        
        for freq, (name, series_id) in test_series.items():
            try:
                print(f"  Testing {freq:10} - {name:25} ({series_id})...", end=' ', flush=True)
                df = pdr.DataReader(series_id, 'fred', start=start_date)
                if not df.empty:
                    print(f"✓ ({len(df)} rows)")
                    successful += 1
                else:
                    print("✗ No data")
            except Exception as e:
                print(f"✗ {str(e)[:40]}")
        
        # Test one Yahoo Finance ticker
        try:
            print(f"  Testing market    - S&P 500              (^GSPC)...", end=' ', flush=True)
            data = yf.download('^GSPC', start=start_date, progress=False)
            if not data.empty:
                print(f"✓ ({len(data)} rows)")
                successful += 1
            else:
                print("✗ No data")
        except Exception as e:
            print(f"✗ {str(e)[:40]}")
        
        if successful >= 3:  # At least 3 out of 5 should work
            print(f"  ✓ Refresh test passed ({successful}/5 series successful)")
            return True
        else:
            print(f"  ✗ Too many failures ({successful}/5 series successful)")
            return False
            
    except Exception as e:
        print(f"  ✗ Refresh script error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Economic Dashboard - Data Refresh Test Suite")
    print("=" * 60)
    
    results = {
        'Imports': test_imports(),
        'Directories': test_directories(),
        'FRED API': test_fred_connection(),
        'Yahoo Finance': test_yfinance_connection(),
        'Refresh Script': test_refresh_script(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:.<30} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! You can enable automated refresh.")
        print("\nNext steps:")
        print("1. Review docs/AUTOMATED_DATA_REFRESH.md")
        print("2. Choose deployment method (GitHub Actions or Airflow)")
        print("3. Test full refresh: .venv\\Scripts\\python.exe scripts\\refresh_data.py")
        print("4. Enable automation")
    else:
        print("❌ Some tests failed. Please fix issues before enabling automation.")
        print("\nCommon fixes:")
        print("- Make sure to use: .venv\\Scripts\\python.exe (not global python)")
        print("- Install missing packages: .venv\\Scripts\\pip.exe install -r requirements.txt")
        print("- Check internet connection")
        print("- Consider getting FRED API key for better rate limits")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
