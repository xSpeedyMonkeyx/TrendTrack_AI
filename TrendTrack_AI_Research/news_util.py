
import os, requests
import pandas as pd
from datetime import date

NEWSAPI_KEY = "8736c7316c5342358f9e60377b5c9b50"
API_URL = "https://newsapi.org/v2/everything"

def fetch_manufacturer_headlines(manufacturer: str, max_results: int = 3) -> pd.DataFrame:
    if not NEWSAPI_KEY or not manufacturer:
        return pd.DataFrame()

    params = {
        "q": f'"{manufacturer}" AND (shock OR suspension OR factory OR innovation OR product)',
        "sortBy": "publishedAt",
        "pageSize": max_results * 2,
        "language": "en",
        "apiKey": NEWSAPI_KEY
    }

    #filter search to try and lessen the unnecessary results
    try:
        r = requests.get(API_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", [])

        important_keywords = [
            "shock", "suspension", "launch", "product",
            "technology", "announcement", "factory", "update"
        ]

        filtered_articles = []
        for art in articles:
            combined = (art.get("title", "") + " " + art.get("description", "")).lower()
            if any(k in combined for k in important_keywords):
                filtered_articles.append({
                    "title": art.get("title"),
                    "source": art.get("source", {}).get("name"),
                    "publishedAt": art.get("publishedAt"),
                    "url": art.get("url")
                })
                if len(filtered_articles) >= max_results:
                    break

        return pd.DataFrame(filtered_articles)
    
    except Exception as e:
        print(f"⚠️ NewsAPI fetch failed for {manufacturer}: {e}")
        return pd.DataFrame()
