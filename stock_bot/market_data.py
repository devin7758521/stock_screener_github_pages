import time


def get_price_data(symbol, interval="1d", period="1y", dry_run=False):
    if dry_run:
        from .sample_data import dry_run_data
        return dry_run_data(symbol, interval=interval, period=period)
    try:
        import yfinance as yf
        df = yf.download(symbol, interval=interval, period=period, progress=False, threads=False)
        if df is not None and not df.empty:
            return df.dropna()
    except Exception as e:
        print(f"[WARN] yfinance 获取失败 {symbol}: {e}")
        time.sleep(0.5)
    return None
