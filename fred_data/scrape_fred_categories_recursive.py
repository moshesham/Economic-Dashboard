import requests
import pandas as pd
import time

FRED_API_KEY = "b077ecbf05fa5f0a6407b38e22552c4e"
BASE_URL = "https://api.stlouisfed.org/fred"
CATEGORY_CHILDREN_CSV = "fred_category_children.csv"

CATEGORY_ENDPOINTS = ["category/tags", "category/series", "category/related_tags"]

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
        print(f"Error fetching {endpoint} with params {params}: {e}")
        return None

def main():
    # Load all category IDs
    cat_df = pd.read_csv(CATEGORY_CHILDREN_CSV)
    category_ids = cat_df["id"].astype(str).tolist()
    print(f"Found {len(category_ids)} category IDs.")

    # For each category endpoint, fetch for all category IDs
    for endpoint in CATEGORY_ENDPOINTS:
        for cat_id in category_ids:
            params = {"category_id": cat_id}
            filename = f"fred_{endpoint.replace('/', '_')}_{cat_id}.csv"
            print(f"Fetching {endpoint} for category_id={cat_id}...")
            fetch_and_save(endpoint, params=params, filename=filename)
            time.sleep(1)

if __name__ == "__main__":
    main()
