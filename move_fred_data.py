import os
import shutil

FRED_DATA_DIR = "fred_data"

# List of file patterns to move
patterns = [
    "fred_",  # All files starting with fred_
    "scan_fred_tags.py",
    "scrape_fred_all.py",
    "scrape_fred_categories_recursive.py"
]

os.makedirs(FRED_DATA_DIR, exist_ok=True)

for file in os.listdir('.'):
    if any(file.startswith(p) for p in patterns if p.endswith('_')) or file in patterns:
        src = os.path.join('.', file)
        dst = os.path.join(FRED_DATA_DIR, file)
        if os.path.isfile(src):
            shutil.move(src, dst)
            print(f"Moved {file} to {FRED_DATA_DIR}/")

print("All FRED data and scripts have been moved to fred_data/")
