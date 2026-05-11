import pandas as pd
import numpy as np


def make_ohlcv(rows=120, start=100, strong_last=True, freq="D", volume=2_000_000):
    idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=rows, freq=freq)
    n = len(idx)
    trend = np.linspace(start, start * 1.35, n)
    open_ = trend * (1 + np.sin(np.arange(n)) * 0.003)
    close = trend * (1 + np.cos(np.arange(n)) * 0.003)
    high = np.maximum(open_, close) * 1.01
    low = np.minimum(open_, close) * 0.99
    vol = np.full(n, float(volume))
    if strong_last:
        open_[-4:-1] = close[-4:-1] - [0.5, 0.8, 0.7]
        close[-1] = close[-2] * 1.08
        open_[-1] = close[-2] * 1.01
        high[-1] = close[-1] * 1.01
        low[-1] = open_[-1] * 0.99
        vol[-1] = volume * 2.2
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol}, index=idx)


def dry_run_symbols():
    return ["DEMO1", "DEMO2", "DEMO3", "DEMO4"]


def dry_run_data(symbol, interval="1d", period="1y"):
    freq = "W" if interval == "1wk" else "D"
    rows = 90 if interval == "1wk" else 140
    strong = symbol != "DEMO2"
    start = 100 if symbol in ["DEMO1", "DEMO2"] else 75
    vol = 2_000_000 if symbol != "DEMO4" else 500_000
    return make_ohlcv(rows=rows, start=start, strong_last=strong, freq=freq, volume=vol)
