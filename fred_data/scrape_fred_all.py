import requests
import pandas as pd
import time

FRED_API_KEY = "b077ecbf05fa5f0a6407b38e22552c4e"
BASE_URL = "https://api.stlouisfed.org/fred"

# Endpoints to scrape (basic, not all require parameters)
ENDPOINTS = {
    "categories": ["category", "category/children", "category/related", "category/series", "category/tags", "category/related_tags"],
    "releases": ["releases", "releases/dates", "release", "release/dates", "release/series", "release/sources", "release/tags", "release/related_tags", "release/tables"],
    "series": ["series", "series/categories", "series/observations", "series/release", "series/search", "series/search/tags", "series/search/related_tags", "series/tags", "series/updates", "series/vintagedates"],
    "sources": ["sources", "source", "source/releases"],
    "tags": ["tags", "related_tags", "tags/series"]
}

# Some endpoints require IDs or parameters; for demo, use basic calls or skip if required
# For full scraping, you would iterate over IDs from parent endpoints

def fetch_and_save(endpoint, params=None, filename=None):
    url = f"{BASE_URL}/{endpoint}"
    if params is None:
        params = {}
    params["api_key"] = FRED_API_KEY
    params["file_type"] = "json"
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        # Find main data key
        main_key = next((k for k in data if isinstance(data[k], list)), None)
        if main_key:
            df = pd.DataFrame(data[main_key])
        else:
            df = pd.DataFrame([data])
        if filename:
            df.to_csv(filename, index=False)
            print(f"Saved {filename} ({len(df)} rows)")
        return df
    except Exception as e:
        print(f"Error fetching {endpoint}: {e}")
        return None

def main():
    for group, endpoints in ENDPOINTS.items():
        for endpoint in endpoints:
            filename = f"fred_{endpoint.replace('/', '_')}.csv"
            print(f"Fetching {endpoint}...")
            fetch_and_save(endpoint, filename=filename)
            time.sleep(1)  # Be polite to API

if __name__ == "__main__":
    main()
