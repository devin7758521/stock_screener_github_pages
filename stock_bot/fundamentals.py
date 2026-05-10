from .market_data import get_session


def _fetch_fundamentals_yfinance(symbol):
    import yfinance as yf
    info = yf.Ticker(symbol).info or {}
    return {
        "symbol": symbol,
        "name": info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "profit_margin": info.get("profitMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "debt_to_equity": info.get("debtToEquity"),
    }


def _fetch_fundamentals_yahoo_direct(symbol):
    """Fallback: scrape basic info from Yahoo Finance summary."""
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=assetProfile,summaryDetail,defaultKeyStatistics"
    resp = get_session().get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    qs = data.get("quoteSummary", {}).get("result", [None])[0]
    if not qs:
        raise ValueError("empty result")
    sp = qs.get("summaryDetail", {})
    dp = qs.get("defaultKeyStatistics", {})
    ap = qs.get("assetProfile", {})
    return {
        "symbol": symbol,
        "name": ap.get("longBusinessName") or sp.get("shortName"),
        "sector": ap.get("sector"),
        "industry": ap.get("industry"),
        "market_cap": sp.get("marketCap", {}).get("raw"),
        "trailing_pe": sp.get("trailingPE", {}).get("raw"),
        "forward_pe": sp.get("forwardPE", {}).get("raw"),
        "profit_margin": dp.get("profitMargins", {}).get("raw"),
        "revenue_growth": dp.get("revenueGrowth", {}).get("raw"),
        "earnings_growth": dp.get("earningsGrowth", {}).get("raw"),
        "debt_to_equity": dp.get("debtToEquity", {}).get("raw"),
    }


def get_fundamentals(symbol, dry_run=False):
    if dry_run:
        return {"symbol": symbol, "name": f"{symbol} Demo Corp", "sector": "Demo", "revenue_growth": 0.12, "profit_margin": 0.18}

    sources = [
        ("yfinance", _fetch_fundamentals_yfinance),
        ("Yahoo Direct", _fetch_fundamentals_yahoo_direct),
    ]

    for name, fetch_fn in sources:
        try:
            return fetch_fn(symbol)
        except Exception as e:
            print(f"[WARN] {name} 基本面获取失败 {symbol}: {e}")

    return {"symbol": symbol}
