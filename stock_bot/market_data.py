import time
import random


def _fetch_yfinance(symbol, interval, period):
    """Source 1: yfinance with Ticker.history() (uses curl_cffi internally)."""
    import yfinance as yf
    yf_interval = {"1wk": "1wk", "1d": "1d", "1mo": "1mo"}.get(interval, "1d")
    yf_period = {"2y": "2y", "1y": "1y", "6mo": "6mo", "max": "max"}.get(period, "1y")
    ticker = yf.Ticker(symbol)
    df = ticker.history(interval=yf_interval, period=yf_period, auto_adjust=False)
    if df is not None and not df.empty:
        return df.dropna()
    return None


def _fetch_yfinance_download(symbol, interval, period):
    """Source 2: yfinance download as fallback (different code path)."""
    import yfinance as yf
    df = yf.download(symbol, interval=interval, period=period, progress=False, threads=False)
    if df is not None and not df.empty:
        return df.dropna()
    return None


def get_price_data(symbol, interval="1d", period="1y", dry_run=False):
    if dry_run:
        from .sample_data import dry_run_data
        return dry_run_data(symbol, interval=interval, period=period)

    sources = [
        ("yfinance (Ticker)", _fetch_yfinance),
        ("yfinance (download)", _fetch_yfinance_download),
    ]

    for name, fetch_fn in sources:
        try:
            df = fetch_fn(symbol, interval, period)
            if df is not None and not df.empty:
                # Normalize MultiIndex columns (yfinance download may return them)
                if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
                    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
                return df
        except Exception as e:
            print(f"[WARN] {name} 获取 {symbol} 失败: {e}")
            time.sleep(0.3 + random.random() * 0.5)

    return None
