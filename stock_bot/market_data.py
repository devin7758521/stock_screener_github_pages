import time
import random
import requests
from requests.adapters import HTTPAdapter, Retry

# Shared session — created once, reused across threads
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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[401, 403, 429, 500, 502, 503])
        _session.mount("https://", HTTPAdapter(max_retries=retry))
    return _session


def get_price_data(symbol, interval="1d", period="1y", dry_run=False):
    if dry_run:
        from .sample_data import dry_run_data
        return dry_run_data(symbol, interval=interval, period=period)
    try:
        import yfinance as yf
        df = yf.download(
            symbol, interval=interval, period=period,
            session=get_session(),
            progress=False, threads=False,
        )
        if df is not None and not df.empty:
            return df.dropna()
    except Exception as e:
        print(f"[WARN] yfinance 获取失败 {symbol}: {e}")
        time.sleep(0.5 + random.random())
    return None
