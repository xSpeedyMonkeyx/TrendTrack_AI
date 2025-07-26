
import os, requests
import pandas as pd
from datetime import date

NEWSAPI_KEY = "8736c7316c5342358f9e60377b5c9b50"
API_URL = "https://newsapi.org/v2/everything"

def fetch_manufacturer_headlines(manufacturer: str, max_results: int = 3) -> pd.DataFrame:
    if not NEWSAPI_KEY or not manufacturer:
        return pd.DataFrame()

    params = {
        "q": manufacturer,
        "sortBy": "publishedAt",
        "pageSize": max_results,
        "language": "en",
        "apiKey": NEWSAPI_KEY
    }
    try:
        r = requests.get(API_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", [])[:max_results]
        records = []
        for art in articles:
            records.append({
                "title": art.get("title"),
                "source": art.get("source", {}).get("name"),
                "publishedAt": art.get("publishedAt"),
                "url": art.get("url")
            })
        return pd.DataFrame(records)
    except Exception as e:
        print(f"⚠️ NewsAPI fetch failed for {manufacturer}: {e}")
        return pd.DataFrame()
