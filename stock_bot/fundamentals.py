from .config import LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, LONGBRIDGE_ACCESS_TOKEN
from . import universe


def _yfinance_info(symbol):
    import yfinance as yf
    try:
        info = yf.Ticker(symbol).info
        return info if isinstance(info, dict) else {}
    except Exception:
        return {}


def _longbridge_fundamentals(symbol):
    """Fallback: fetch PE, PB, market cap from LongPort OpenAPI (free tier)."""
    if not (LONGBRIDGE_APP_KEY and LONGBRIDGE_APP_SECRET and LONGBRIDGE_ACCESS_TOKEN):
        return None

    try:
        from longport.openapi import Config, QuoteContext

        cfg = Config(
            app_key=LONGBRIDGE_APP_KEY,
            app_secret=LONGBRIDGE_APP_SECRET,
            access_token=LONGBRIDGE_ACCESS_TOKEN,
        )
        ctx = QuoteContext(cfg)
        lb_symbol = f"{symbol}.US"
        resp = ctx.calc_index(
            [lb_symbol],
            pe_ttm_ratio=True,
            pb_ratio=True,
            total_market_value=True,
            dividend_ratio_ttm=True,
        )
        for item in resp:
            if item.symbol == lb_symbol:
                return {
                    "trailing_pe": float(item.pe_ttm_ratio) if item.pe_ttm_ratio else None,
                    "pb_ratio": float(item.pb_ratio) if item.pb_ratio else None,
                    "market_cap": float(item.total_market_value) if item.total_market_value else None,
                    "dividend_yield": float(item.dividend_ratio_ttm) if item.dividend_ratio_ttm else None,
                }
    except ImportError:
        print("[WARN] longport SDK 未安装，跳过长桥基本面回退")
    except Exception as e:
        print(f"[WARN] 长桥基本面获取失败 {symbol}: {e}")
    return None


def get_fundamentals(symbol, dry_run=False):
    if dry_run:
        return {"symbol": symbol, "name": f"{symbol} Demo Corp", "sector": "Demo", "revenue_growth": 0.12, "profit_margin": 0.18}

    info = _yfinance_info(symbol)
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

    # Fallback: Longbridge
    lb = _longbridge_fundamentals(symbol)
    if lb is not None:
        result = {"symbol": symbol, "name": universe.lookup_name(symbol)}
        result.update(lb)
        return result

    # Last resort: try the universe name map
    name = universe.lookup_name(symbol)
    if name:
        return {"symbol": symbol, "name": name}

    return {"symbol": symbol}
