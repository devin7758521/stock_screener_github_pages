import json
import io
import time
from pathlib import Path

import pandas as pd


CACHE_FILE = Path("public/data/universe_cache.json")
FALLBACK_FILE = Path("config/universe_fallback.json")


def _normalize_symbols(symbols):
    cleaned = []

    for symbol in symbols:
        s = str(symbol).strip()

        if not s:
            continue

        if s.lower() in ["nan", "none", "ticker", "symbol"]:
            continue

        # Yahoo Finance 对 BRK.B / BF.B 这类股票代码使用 BRK-B / BF-B
        s = s.replace(".", "-")

        cleaned.append(s)

    return sorted(list(set(cleaned)))


def _save_cache(symbols):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    symbols = _normalize_symbols(symbols)

    CACHE_FILE.write_text(
        json.dumps(symbols, indent=2),
        encoding="utf-8"
    )


def _load_json_file(path):
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
    return _load_json_file(CACHE_FILE)


def _load_fallback():
    return _load_json_file(FALLBACK_FILE)


def _read_html_with_headers(url):
    """
    GitHub Actions 里直接 pd.read_html(url) 有时会被 403。
    这里增加 User-Agent，降低被拒绝概率。
    """

    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return pd.read_html(io.StringIO(response.text))


def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    tables = _read_html_with_headers(url)

    df = tables[0]

    if "Symbol" not in df.columns:
        raise RuntimeError("S&P 500 页面未找到 Symbol 列")

    return _normalize_symbols(df["Symbol"].tolist())


def get_nasdaq100_symbols():
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"

    tables = _read_html_with_headers(url)

    for table in tables:
        for col in table.columns:
            name = str(col).lower()

            if (
                name in ["ticker", "symbol"]
                or "ticker" in name
                or "symbol" in name
            ):
                symbols = _normalize_symbols(table[col].tolist())

                if symbols:
                    return symbols

    raise RuntimeError("Nasdaq-100 页面未找到 ticker/symbol 列")


def get_universe(dry_run=False):
    if dry_run:
        from .sample_data import dry_run_symbols

        return dry_run_symbols()

    # 1. 优先尝试在线获取最新股票池
    try:
        sp500 = get_sp500_symbols()
        time.sleep(1)
        nasdaq100 = get_nasdaq100_symbols()

        symbols = _normalize_symbols(sp500 + nasdaq100)

        if symbols:
            _save_cache(symbols)
            print(f"[INFO] 在线股票池获取成功，数量: {len(symbols)}")
            return symbols

    except Exception as e:
        print(f"[WARN] 在线获取股票池失败: {e}")

    # 2. 在线失败，读取历史缓存
    cached = _load_cache()

    if cached:
        print(f"[INFO] 使用历史缓存股票池，数量: {len(cached)}")
        return cached

    # 3. 第一次运行没有缓存，则读取本地 fallback
    fallback = _load_fallback()

    if fallback:
        print(f"[INFO] 使用本地 fallback 股票池，数量: {len(fallback)}")
        return fallback

    # 4. 全部失败才报错
    raise RuntimeError("股票池获取失败，且没有可用缓存或 fallback 文件。")
