#!/usr/bin/env python3
"""
Generate all sample data for offline mode.
Run this script to create sample datasets for testing without internet.
"""

import os
import sys

def generate_sample_data():
    """Generate all sample data files."""
    print("Generating sample data for offline mode...")

    scripts = [
        'data/create_sample_fred_data.py',
        'data/create_sample_yfinance_data.py',
        'data/create_sample_world_bank_data.py'
    ]

    for script in scripts:
        if os.path.exists(script):
            print(f"Running {script}...")
            try:
                result = os.system(f"{sys.executable} {script}")
                if result == 0:
                    print(f"✅ {script} completed successfully")
                else:
                    print(f"❌ {script} failed with exit code {result}")
            except Exception as e:
                print(f"❌ Error running {script}: {e}")
        else:
            print(f"⚠️  {script} not found")

    print("\nSample data generation complete!")
    print("You can now run the app in offline mode:")
    print("export ECONOMIC_DASHBOARD_OFFLINE=true")
    print("streamlit run app.py")

if __name__ == "__main__":
    generate_sample_data()