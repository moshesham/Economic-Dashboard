#!/usr/bin/env python3
"""
Simple validation script for the Economic Dashboard.
Tests basic functionality without external dependencies.
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        import streamlit as st
        print("✅ streamlit imported")
    except ImportError as e:
        print(f"❌ streamlit import failed: {e}")
        return False

    try:
        import pandas as pd
        print("✅ pandas imported")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False

    try:
        import plotly.express as px
        print("✅ plotly imported")
    except ImportError as e:
        print(f"❌ plotly import failed: {e}")
        return False

    try:
        import yfinance as yf
        print("✅ yfinance imported")
    except ImportError as e:
        print(f"❌ yfinance import failed: {e}")
        return False

    try:
        import pandas_datareader
        print("✅ pandas_datareader imported")
    except ImportError as e:
        print(f"❌ pandas_datareader import failed: {e}")
        return False

    return True

def test_app_structure():
    """Test that app files exist and have basic structure."""
    print("Testing app structure...")

    required_files = [
        "app.py",
        "modules/data_loader.py",
        "pages/1_Economic_Indicators_Deep_Dive.py",
        "pages/2_Financial_Markets_Deep_Dive.py",
        "requirements.txt",
        "README.md"
    ]

    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False

    return True

def test_syntax():
    """Test Python syntax for all files."""
    print("Testing syntax...")

    files_to_check = [
        "app.py",
        "modules/data_loader.py",
        "pages/1_Economic_Indicators_Deep_Dive.py",
        "pages/2_Financial_Markets_Deep_Dive.py"
    ]

    import py_compile
    for file in files_to_check:
        try:
            py_compile.compile(file, doraise=True)
            print(f"✅ {file} syntax OK")
        except py_compile.PyCompileError as e:
            print(f"❌ {file} syntax error: {e}")
            return False

    return True

def main():
    """Main validation function."""
    print("🌍 Economic Dashboard - Basic Validation")
    print("=" * 50)

    tests = [
        ("Dependencies", test_imports),
        ("File Structure", test_app_structure),
        ("Python Syntax", test_syntax)
    ]

    all_passed = True
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if not test_func():
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 Basic validation passed!")
        print("Note: External API tests (FRED, Yahoo Finance) may fail without internet connection.")
        return 0
    else:
        print("⚠️  Some basic checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())