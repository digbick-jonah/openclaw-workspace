"""Fetch NQ futures data from Polygon.io"""
from datetime import datetime, timedelta
from polygon import RESTClient
import pandas as pd
import yaml


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def fetch_nq_data(client, start_date: str, end_date: str, multiplier: int = 1, span: str = "day", ticker: str = "XNAS:NDX") -> pd.DataFrame:
    """
    Fetch NASDAQ-100 data from Polygon.
    
    Args:
        client: Polygon RESTClient
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        multiplier: 1 for daily, less for intraday
        span: 'day', 'hour', 'minute'
        ticker: Polygon ticker (default XNAS:NDX for Nasdaq-100 index)
    """
    
    bars = list(client.list_aggs(
        ticker=ticker,
        multiplier=multiplier,
        timespan=span,
        from_=start_date,
        to=end_date,
        limit=50000
    ))
    
    if not bars:
        raise ValueError(f"No data found for {ticker} from {start_date} to {end_date}")
    
    df = pd.DataFrame([
        {
            "timestamp": datetime.fromtimestamp(b.timestamp / 1000),
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume if b.volume is not None else 0
        }
        for b in bars
    ])
    
    df.set_index("timestamp", inplace=True)
    return df


def get_data(start_date: str = None, end_date: str = None, ticker: str = None) -> pd.DataFrame:
    """Convenience function to fetch data using config defaults."""
    config = load_config()
    client = RESTClient(config["polygon_api_key"])
    
    start = start_date or config["backtest"]["start_date"]
    end = end_date or config["backtest"]["end_date"]
    tkr = ticker or "I:NDX"  # Nasdaq-100 Index
    
    return fetch_nq_data(client, start, end, ticker=tkr)


if __name__ == "__main__":
    df = get_data()
    print(f"Fetched {len(df)} bars")
    print(df.head())
    print(df.tail())
