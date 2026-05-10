import time
import random
import json

import requests
from requests.adapters import HTTPAdapter, Retry

# HTTP session for fallback requests (yfinance manages its own session internally)
_session = None


def get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/html,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        retry = Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503])
        _session.mount("https://", HTTPAdapter(max_retries=retry))
    return _session


def _fetch_yfinance(symbol, interval, period):
    """Try yfinance first (no custom session — yfinance manages curl_cffi internally)."""
    import yfinance as yf
    df = yf.download(symbol, interval=interval, period=period, progress=False, threads=False)
    if df is not None and not df.empty:
        return df.dropna()
    return None


def _fetch_yahoo_direct(symbol, interval, period):
    """Fallback: hit Yahoo Finance v8 chart API directly via HTTP."""
    import pandas as pd
    interval_map = {"1d": "1d", "1wk": "1wk", "1mo": "1mo"}
    period_map = {"1y": "1y", "6mo": "6mo", "2y": "2y", "max": "max"}
    yf_interval = interval_map.get(interval, "1d")
    yf_range = period_map.get(period, "1y")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={yf_interval}&range={yf_range}"
    resp = get_session().get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    result = data["chart"]["result"]
    if not result:
        return None
    result = result[0]
    timestamps = result["timestamp"]
    quotes = result["indicators"]["quote"][0]
    opens = quotes.get("open")
    highs = quotes.get("high")
    lows = quotes.get("low")
    closes = quotes.get("close")
    volumes = quotes.get("volume")
    if not all([timestamps, opens, highs, lows, closes, volumes]):
        return None
    df = pd.DataFrame({
        "Open": opens,
        "High": highs,
        "Low": lows,
        "Close": closes,
        "Volume": volumes,
    }, index=pd.to_datetime(timestamps, unit="s"))
    return df.dropna()


def get_price_data(symbol, interval="1d", period="1y", dry_run=False):
    if dry_run:
        from .sample_data import dry_run_data
        return dry_run_data(symbol, interval=interval, period=period)

    sources = [
        ("yfinance", _fetch_yfinance),
        ("Yahoo Direct", _fetch_yahoo_direct),
    ]

    for name, fetch_fn in sources:
        try:
            df = fetch_fn(symbol, interval, period)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            print(f"[WARN] {name} 获取 {symbol} 失败: {e}")
            time.sleep(0.3 + random.random() * 0.5)

    return None
