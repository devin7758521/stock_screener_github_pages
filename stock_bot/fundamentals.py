def _safe_info(symbol):
    """Get ticker info, returning empty dict on any internal yfinance error."""
    import yfinance as yf
    try:
        info = yf.Ticker(symbol).info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def get_fundamentals(symbol, dry_run=False):
    if dry_run:
        return {"symbol": symbol, "name": f"{symbol} Demo Corp", "sector": "Demo", "revenue_growth": 0.12, "profit_margin": 0.18}
    info = _safe_info(symbol)
    if info:
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
    return {"symbol": symbol}
