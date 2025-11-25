import requests
import pandas as pd
from typing import List, Dict

FRED_API_KEY = "b077ecbf05fa5f0a6407b38e22552c4e"
BASE_URL = "https://api.stlouisfed.org/fred/related_tags"


def fetch_related_tags(tag_names: List[str], exclude_tag_names: List[str] = None,
                      group_id: str = None, search_text: str = None,
                      limit: int = 1000, order_by: str = "series_count",
                      sort_order: str = "desc") -> pd.DataFrame:
    """
    Fetch related FRED tags for given tag names and optional filters.
    Returns a DataFrame of tags and their metadata.
    """
    params = {
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "tag_names": ";".join(tag_names),
        "limit": limit,
        "order_by": order_by,
        "sort_order": sort_order
    }
    if exclude_tag_names:
        params["exclude_tag_names"] = ";".join(exclude_tag_names)
    if group_id:
        params["tag_group_id"] = group_id
    if search_text:
        params["search_text"] = search_text

    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    tags = data.get("tags", [])
    return pd.DataFrame(tags)


def main():
    # Example: scan for monetary aggregates and weekly tags
    tag_names = ["monetary aggregates", "weekly"]
    df = fetch_related_tags(tag_names)
    print("Fetched tags:")
    print(df.head(10))
    print("\nAll tag names:", df["name"].tolist())
    print("\nAll tag groups:", df["group_id"].unique())
    print("\nAll notes:", df["notes"].dropna().unique())

    # Save to CSV for further analysis
    df.to_csv("fred_related_tags.csv", index=False)
    print("\nSaved to fred_related_tags.csv")

if __name__ == "__main__":
    main()
