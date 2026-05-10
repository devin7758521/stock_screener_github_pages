from .market_data import get_session


def get_fundamentals(symbol, dry_run=False):
    if dry_run:
        return {"symbol": symbol, "name": f"{symbol} Demo Corp", "sector": "Demo", "revenue_growth": 0.12, "profit_margin": 0.18}
    try:
        import yfinance as yf
        info = yf.Ticker(symbol, session=get_session()).info or {}
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
    except Exception as e:
        print(f"[WARN] 基本面获取失败 {symbol}: {e}")
        return {"symbol": symbol}
