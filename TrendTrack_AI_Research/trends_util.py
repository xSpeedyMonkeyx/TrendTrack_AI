from pytrends.request import TrendReq
import pandas as pd

def fetch_trend_data(keyword: str, start_date: str = "2024-01-01", end_date: str = "2024-06-30") -> pd.DataFrame:
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([keyword], cat=0, timeframe=f"{start_date} {end_date}")
        data = pytrends.interest_over_time()

        if not data.empty and keyword in data.columns:
            return data[[keyword]]
        else:
            return pd.DataFrame()
    except Exception:
        # Handle failed fetches
        return pd.DataFrame()
