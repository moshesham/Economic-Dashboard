#!/usr/bin/env python3
"""
Local testing script for the Economic Dashboard.
Run this script to validate the application before deployment.
"""

import sys
import os
import subprocess
import time

def run_tests():
    """Run the test suite."""
    print("🧪 Running test suite...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=os.getcwd())

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def check_syntax():
    """Check Python syntax for all modules."""
    print("🔍 Checking Python syntax...")
    files_to_check = [
        "app.py",
        "modules/data_loader.py",
        "pages/1_Economic_Indicators_Deep_Dive.py",
        "pages/2_Financial_Markets_Deep_Dive.py",
        "tests/test_data_loader.py",
        "tests/test_app_integration.py"
    ]

    all_good = True
    for file in files_to_check:
        if os.path.exists(file):
            try:
                subprocess.run([sys.executable, "-m", "py_compile", file],
                             check=True, capture_output=True)
                print(f"✅ {file}")
            except subprocess.CalledProcessError:
                print(f"❌ {file} - Syntax error")
                all_good = False
        else:
            print(f"⚠️  {file} - File not found")

    return all_good

def test_offline_mode():
    """Test app functionality in offline mode."""
    print("Testing offline mode...")

    # Set offline mode
    import os
    os.environ['ECONOMIC_DASHBOARD_OFFLINE'] = 'true'

    try:
        # Reload config to pick up environment variable
        import importlib
        import config
        importlib.reload(config)

        if not config.is_offline_mode():
            print("❌ Could not enable offline mode")
            return False

        # Test data loading in offline mode
        from modules.data_loader import load_fred_data, load_world_bank_gdp

        # Test FRED data
        fred_data = load_fred_data({'GDP Growth': 'A191RL1Q225SBEA'})
        if fred_data.empty:
            print("❌ FRED offline data not working")
            return False
        print("✅ FRED offline data loaded")

        # Test World Bank data
        wb_data = load_world_bank_gdp()
        if wb_data.empty:
            print("❌ World Bank offline data not working")
            return False
        print("✅ World Bank offline data loaded")

        return True

    except Exception as e:
        print(f"❌ Offline mode test failed: {e}")
        return False
    finally:
        # Reset environment
        os.environ.pop('ECONOMIC_DASHBOARD_OFFLINE', None)
        importlib.reload(config)

def main():
    """Main testing function."""
    print("🌍 Economic Dashboard - Local Testing Framework")
    print("=" * 50)

    results = []

    # Check syntax
    results.append(("Syntax Check", check_syntax()))

    # Run tests
    results.append(("Unit Tests", run_tests()))

    # Test offline mode
    results.append(("Offline Mode", test_offline_mode()))

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())