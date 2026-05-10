import pandas as pd
from .config import MIN_AVG_DOLLAR_VOLUME, VOLUME_MULTIPLIER


def _to_scalar(value):
    if hasattr(value, "iloc"):
        return float(value.iloc[0])
    return float(value)


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        seen = set()
        cols = []
        for c in out.columns:
            name = c[0] if isinstance(c, tuple) else c
            if name not in seen:
                seen.add(name)
                cols.append(name)
        out.columns = cols
    required = ["Open", "High", "Low", "Close"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"Missing OHLC columns: {missing}")
    if "Volume" not in out.columns:
        out["Volume"] = 0
    return out.dropna(subset=required)


def candle_body(row) -> float:
    return abs(_to_scalar(row["Close"]) - _to_scalar(row["Open"]))


def body_ratio_latest_vs_prev3(df: pd.DataFrame) -> float:
    df = normalize_ohlcv(df)
    if len(df) < 4:
        return 0.0
    latest_body = candle_body(df.iloc[-1])
    prev3_max = df.iloc[-4:-1].apply(candle_body, axis=1).max()
    if prev3_max == 0:
        return 0.0
    return round(float(latest_body / prev3_max), 4)


def is_bullish(row) -> bool:
    return _to_scalar(row["Close"]) > _to_scalar(row["Open"])


def latest_body_gt_prev3(df: pd.DataFrame, multiplier=1.0) -> bool:
    df = normalize_ohlcv(df)
    if len(df) < 4:
        return False
    latest = df.iloc[-1]
    return bool(is_bullish(latest) and body_ratio_latest_vs_prev3(df) >= multiplier)


def volume_metrics(daily_df: pd.DataFrame):
    df = normalize_ohlcv(daily_df)
    if len(df) < 20:
        return {"volume_ratio": 0, "avg_dollar_volume_20": 0}
    latest_volume = _to_scalar(df["Volume"].iloc[-1])
    avg_volume_20 = _to_scalar(df["Volume"].rolling(20).mean().iloc[-1])
    avg_dollar_volume_20 = _to_scalar((df["Close"] * df["Volume"]).rolling(20).mean().iloc[-1])
    return {
        "volume_ratio": round(latest_volume / avg_volume_20, 4) if avg_volume_20 else 0,
        "avg_dollar_volume_20": round(avg_dollar_volume_20, 2),
    }


def weekly_ma60_deviation_risk_label(deviation):
    if deviation is None:
        return "未知"
    if deviation < 0:
        return "低于60周线"
    if deviation < 0.70:
        return "正常延伸"
    if deviation < 1.20:
        return "偏热"
    if deviation < 1.80:
        return "明显过热"
    return "极度延伸"


def weekly_metrics(weekly_df: pd.DataFrame):
    df = normalize_ohlcv(weekly_df)
    if len(df) < 60:
        return None
    df = df.copy()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA25"] = df["Close"].rolling(25).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    latest = df.iloc[-1]
    if pd.isna(latest["MA60"]):
        return None
    close = _to_scalar(latest["Close"])
    ma60 = _to_scalar(latest["MA60"])
    weekly_ma60_deviation = round(close / ma60 - 1, 4) if ma60 else None
    return {
        "close": round(close, 2),
        "weekly_body_ratio": body_ratio_latest_vs_prev3(df),
        "weekly_bullish": is_bullish(latest),
        "above_ma5": _to_scalar(latest["Close"]) > _to_scalar(latest["MA5"]),
        "above_ma25": _to_scalar(latest["Close"]) > _to_scalar(latest["MA25"]),
        "above_ma60": _to_scalar(latest["Close"]) > _to_scalar(latest["MA60"]),
        "ma5_gt_ma25": _to_scalar(latest["MA5"]) > _to_scalar(latest["MA25"]),
        "ma25_gt_ma60": _to_scalar(latest["MA25"]) > _to_scalar(latest["MA60"]),
        "weekly_ma60": round(ma60, 2),
        "weekly_ma60_deviation": weekly_ma60_deviation,
        "weekly_ma60_deviation_risk": weekly_ma60_deviation_risk_label(weekly_ma60_deviation),
    }


def daily_metrics(daily_df: pd.DataFrame):
    df = normalize_ohlcv(daily_df)
    if len(df) < 25:
        return None
    v = volume_metrics(df)
    return {
        "daily_body_ratio": body_ratio_latest_vs_prev3(df),
        "daily_bullish": is_bullish(df.iloc[-1]),
        **v,
    }


def relative_strength_metrics(symbol_df: pd.DataFrame, spy_df: pd.DataFrame = None, qqq_df: pd.DataFrame = None, window: int = 60):
    df = normalize_ohlcv(symbol_df)
    result = {"stock_return_60d": 0, "spy_return_60d": None, "qqq_return_60d": None, "beat_spy_60d": False, "beat_qqq_60d": False}
    if len(df) <= window:
        return result
    stock_ret = _to_scalar(df["Close"].iloc[-1] / df["Close"].iloc[-window] - 1)
    result["stock_return_60d"] = round(stock_ret, 4)
    for name, bench, key in [("spy", spy_df, "spy_return_60d"), ("qqq", qqq_df, "qqq_return_60d")]:
        if bench is None or len(bench) <= window:
            continue
        b = normalize_ohlcv(bench)
        bench_ret = _to_scalar(b["Close"].iloc[-1] / b["Close"].iloc[-window] - 1)
        result[key] = round(bench_ret, 4)
        result[f"beat_{name}_60d"] = stock_ret > bench_ret
    return result


def kdj_metrics(df: pd.DataFrame, n=18, k_smooth=3, d_smooth=3) -> dict:
    """Calculate KDJ indicator.

    RSV = (Close - LLV(Low, N)) / (HHV(High, N) - LLV(Low, N)) * 100
    K = SMA(RSV, K_smooth)
    D = SMA(K, D_smooth)
    J = 3 * K - 2 * D
    """
    df = normalize_ohlcv(df)
    min_len = n + max(k_smooth, d_smooth)
    if len(df) < min_len:
        return {"k": 50.0, "d": 50.0, "j": 50.0, "kdj_bullish": True}

    llv = df["Low"].rolling(window=n).min()
    hhv = df["High"].rolling(window=n).max()
    denom = hhv - llv
    # Avoid division by zero
    rsv = ((df["Close"] - llv) / denom.replace(0, float("nan")) * 100).fillna(50)

    k = rsv.rolling(window=k_smooth, min_periods=1).mean()
    d = k.rolling(window=d_smooth, min_periods=1).mean()
    j = 3 * k - 2 * d

    return {
        "k": round(float(k.iloc[-1]), 2),
        "d": round(float(d.iloc[-1]), 2),
        "j": round(float(j.iloc[-1]), 2),
        "kdj_bullish": bool(float(k.iloc[-1]) > float(d.iloc[-1])),
    }


def build_score_and_tags(metrics):
    score, tags = 0, []
    m = metrics
    if m.get("above_ma5"):
        score += 1; tags.append("高于5周线")
    if m.get("above_ma25"):
        score += 1; tags.append("高于25周线")
    if m.get("above_ma60"):
        score += 1; tags.append("高于60周线")
    if m.get("ma5_gt_ma25"):
        score += 1; tags.append("5周线>25周线")
    if m.get("ma25_gt_ma60"):
        score += 1; tags.append("25周线>60周线")
    if m.get("weekly_bullish") and m.get("weekly_body_ratio", 0) >= 1:
        score += 2; tags.append("周K实体突破")
    if m.get("daily_bullish") and m.get("daily_body_ratio", 0) >= 1:
        score += 2; tags.append("日K实体确认")
    if m.get("volume_ratio", 0) >= VOLUME_MULTIPLIER:
        score += 1; tags.append("日成交量放大")
    if m.get("avg_dollar_volume_20", 0) >= MIN_AVG_DOLLAR_VOLUME:
        score += 1; tags.append("流动性达标")
    if m.get("beat_spy_60d"):
        score += 1; tags.append("跑赢SPY")
    if m.get("beat_qqq_60d"):
        score += 1; tags.append("跑赢QQQ")
    return score, tags


def hard_pass_default(metrics):
    return (
        metrics.get("above_ma5") and
        metrics.get("weekly_bullish") and metrics.get("weekly_body_ratio", 0) >= 1 and
        metrics.get("daily_bullish") and metrics.get("daily_body_ratio", 0) >= 1 and
        metrics.get("avg_dollar_volume_20", 0) >= MIN_AVG_DOLLAR_VOLUME
    )
