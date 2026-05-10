import json
import time
from pathlib import Path

import pandas as pd

_CACHE_FILE = Path("public/data/universe_cache.json")
_NAME_CACHE_FILE = Path("public/data/universe_names.json")
_FALLBACK_FILE = Path("config/universe_fallback.json")

# Populated after successful online fetch — used by fundamentals.py for name lookup
_name_map: dict[str, str] = {}


def _normalize_symbols(symbols):
    cleaned = []
    for symbol in symbols:
        s = str(symbol).strip()
        if not s:
            continue
        if s.lower() in ("nan", "none", "ticker", "symbol"):
            continue
        s = s.replace(".", "-")
        cleaned.append(s)
    return sorted(set(cleaned))


def _save_cache(symbols, name_map=None):
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    symbols = _normalize_symbols(symbols)
    _CACHE_FILE.write_text(json.dumps(symbols, indent=2), encoding="utf-8")
    if name_map:
        _NAME_CACHE_FILE.write_text(json.dumps(name_map, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_json_list(path):
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            return _normalize_symbols(data)
    except Exception as e:
        print(f"[WARN] 读取 {path} 失败: {e}")
    return []


def _load_cache():
    return _load_json_list(_CACHE_FILE)


def _load_fallback():
    return _load_json_list(_FALLBACK_FILE)


def _fetch_csv(url):
    """Fetch a CSV from a raw URL, return DataFrame."""
    import requests
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return pd.read_csv(url)


def get_sp500_symbols():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    df = _fetch_csv(url)
    name_map = {}
    symbols = []
    for _, row in df.iterrows():
        sym = str(row.get("Symbol", "")).strip()
        name = str(row.get("Name", "")).strip()
        if sym:
            symbols.append(sym)
            if name and name.lower() not in ("nan", ""):
                name_map[sym] = name
    return _normalize_symbols(symbols), name_map


def get_nasdaq100_symbols():
    url = "https://raw.githubusercontent.com/Gary-Strauss/nasdaq100-scraper/main/data/nasdaq100_constituents.csv"
    df = _fetch_csv(url)
    name_map = {}
    symbols = []
    for _, row in df.iterrows():
        sym = str(row.get("Ticker", "")).strip()
        name = str(row.get("Company", "")).strip()
        if sym:
            symbols.append(sym)
            if name and name.lower() not in ("nan", ""):
                name_map[sym] = name
    return _normalize_symbols(symbols), name_map


def lookup_name(symbol: str) -> str | None:
    """Return company name for a symbol, if known from the last universe fetch."""
    return _name_map.get(symbol)


def get_universe(dry_run=False):
    global _name_map

    if dry_run:
        from .sample_data import dry_run_symbols
        return dry_run_symbols()

    # 1. GitHub datasets CSVs (no anti-scraping)
    try:
        sp500, names_sp = get_sp500_symbols()
        time.sleep(0.5)
        nasdaq100, names_nq = get_nasdaq100_symbols()

        symbols = _normalize_symbols(sp500 + nasdaq100)
        _name_map = {**names_sp, **names_nq}

        if symbols:
            _save_cache(symbols, _name_map)
            print(f"[INFO] 在线股票池获取成功，数量: {len(symbols)}")
            return symbols
    except Exception as e:
        print(f"[WARN] 在线获取股票池失败: {e}")

    # 2. Cache
    cached = _load_cache()
    if cached:
        print(f"[INFO] 使用历史缓存股票池，数量: {len(cached)}")
        return cached

    # 3. Fallback JSON
    fallback = _load_fallback()
    if fallback:
        print(f"[INFO] 使用本地 fallback 股票池，数量: {len(fallback)}")
        return fallback

    raise RuntimeError("股票池获取失败，且没有可用缓存或 fallback 文件。")
