from pytrends.request import TrendReq
import pandas as pd
import time
from datetime import datetime, timedelta
import os

FALLBACK_DIR = "fallback_trends"
os.makedirs(FALLBACK_DIR, exist_ok=True)


def fetch_trend_data(keyword: str, months_back: int = 6) -> pd.DataFrame:
    try:
        time.sleep(2)  # reduce chance of 429
        end_date = datetime.today()
        start_date = end_date - timedelta(days=30 * months_back)
        timeframe = f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"

        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe)
        data = pytrends.interest_over_time()

        if not data.empty and keyword in data.columns:
            # Save to fallback for future use
            os.makedirs(FALLBACK_DIR, exist_ok=True)
            fallback_path = os.path.join(FALLBACK_DIR, f"{keyword}.csv")
            data[[keyword]].to_csv(fallback_path) #save trend results to local CSV
            print(f"💾 Cached Google Trends data to {fallback_path}")
            return data[[keyword]]

        raise ValueError("Empty data returned from Google Trends.")

    except Exception as e:
        print(f"⚠️ Google Trends fetch failed for {keyword}: {e}")

        # Try fallback
        fallback_file = os.path.join(FALLBACK_DIR, f"{keyword}.csv")
        if os.path.exists(fallback_file):
            try:
                fallback_data = pd.read_csv(fallback_file, parse_dates=True, index_col=0)
                print(f"ℹ️ Loaded fallback trends for {keyword} from {fallback_file}")
                return fallback_data
            except Exception as fallback_error:
                print(f"❌ Failed to load fallback data for {keyword}: {fallback_error}")

        return pd.DataFrame()
