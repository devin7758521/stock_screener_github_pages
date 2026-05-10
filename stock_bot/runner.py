import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .universe import get_universe
from .market_data import get_price_data
from .strategy import (
    weekly_metrics, daily_metrics, relative_strength_metrics,
    build_score_and_tags, hard_pass_default, normalize_ohlcv,
)
from .fundamentals import get_fundamentals
from .news import get_google_news
from .deepseek_analyzer import analyze_with_deepseek
from .feishu import send_feishu_message
from .site_builder import write_site_data
from .config import MAX_STOCK_COUNT_FOR_DEEPSEEK, VOLUME_MULTIPLIER, MIN_AVG_DOLLAR_VOLUME


def market_status(spy, qqq):
    try:
        def above_ma20(df):
            return float(df["Close"].iloc[-1]) > float(df["Close"].rolling(20).mean().iloc[-1])
        spy_ok, qqq_ok = above_ma20(spy), above_ma20(qqq)
        if spy_ok and qqq_ok: return "偏强"
        if spy_ok or qqq_ok: return "中性"
        return "偏弱"
    except Exception:
        return "未知"


def build_feishu_message(items, status):
    if not items:
        return "【美股强势股观察名单】\n今日没有筛选出符合默认条件的股票。"
    lines = ["【美股强势股观察名单】", f"市场状态：{status}", f"候选数量：{len(items)}", ""]
    for i, item in enumerate(items[:10], 1):
        lines.append(f"{i}. {item['symbol']} | 评分：{item['score']}")
        lines.append("标签：" + "、".join(item.get("tags", [])))
        lines.append("摘要：" + item.get("ai_summary", ""))
        lines.append("")
    return "\n".join(lines)


def process_symbol(symbol, spy_norm, qqq_norm, dry_run):
    """Fetch data and compute metrics for a single symbol."""
    weekly = get_price_data(symbol, "1wk", "2y", dry_run=dry_run)
    daily = get_price_data(symbol, "1d", "6mo", dry_run=dry_run)
    wm, dm = weekly_metrics(weekly), daily_metrics(daily)
    if not wm or not dm:
        return None
    rs = relative_strength_metrics(daily, spy_norm, qqq_norm)
    metrics = {**wm, **dm, **rs}
    score, tags = build_score_and_tags(metrics)
    fundamentals = get_fundamentals(symbol, dry_run=dry_run)
    news = get_google_news(symbol, dry_run=dry_run)
    return {
        "symbol": symbol,
        "name": fundamentals.get("name") or symbol,
        "score": score,
        "tags": tags,
        "default_pass": bool(hard_pass_default(metrics)),
        "metrics": metrics,
        "fundamentals": fundamentals,
        "news": news,
    }


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="使用内置模拟数据，不访问外部网络/API")
    parser.add_argument("--site-output", action="store_true", help="生成GitHub Pages需要的public/data/*.json")
    parser.add_argument("--no-feishu", action="store_true", help="不推送飞书")
    parser.add_argument("--workers", type=int, default=4, help="并行拉取数据的线程数")
    args = parser.parse_args(argv)
    dry_run = args.dry_run

    symbols = get_universe(dry_run=dry_run)
    print(f"股票池数量：{len(symbols)}")

    spy_raw = get_price_data("SPY", "1d", "6mo", dry_run=dry_run)
    qqq_raw = get_price_data("QQQ", "1d", "6mo", dry_run=dry_run)
    status = market_status(spy_raw, qqq_raw)

    # Pre-normalize benchmarks once to avoid redundant work per-symbol
    spy_norm = normalize_ohlcv(spy_raw) if spy_raw is not None else None
    qqq_norm = normalize_ohlcv(qqq_raw) if qqq_raw is not None else None

    # Phase 1: parallel data fetching and scoring
    items = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_symbol, s, spy_norm, qqq_norm, dry_run): s for s in symbols}
        for future in as_completed(futures):
            item = future.result()
            if item:
                items.append(item)

    items.sort(key=lambda x: x["score"], reverse=True)
    top_items = items[:MAX_STOCK_COUNT_FOR_DEEPSEEK]
    print(f"筛选结果：{len(items)} 只，Top {len(top_items)} 将进行AI分析")

    # Phase 2: DeepSeek analysis only on top N (parallel)
    def analyze(item):
        item["ai_summary"] = analyze_with_deepseek(
            item["symbol"], item["metrics"], item["fundamentals"], item["news"], dry_run=dry_run,
        )
        return item

    if top_items:
        if dry_run:
            for item in top_items:
                analyze(item)
        else:
            with ThreadPoolExecutor(max_workers=min(5, len(top_items))) as executor:
                executor.map(analyze, top_items)

    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market_status": status,
        "universe_count": len(symbols),
        "defaults": {
            "weeklyBodyMultiplier": 1.0,
            "dailyBodyMultiplier": 1.0,
            "enableVolumeFilter": True,
            "volumeMultiplier": VOLUME_MULTIPLIER,
            "enableDollarVolumeFilter": True,
            "minAvgDollarVolume": MIN_AVG_DOLLAR_VOLUME,
            "topN": 10,
        },
        "items": top_items,
    }

    if args.site_output:
        latest, run_file = write_site_data(payload)
        print(f"Site data written: {latest}, {run_file}")

    if not args.no_feishu:
        send_feishu_message(build_feishu_message(top_items, status), dry_run=dry_run)
    return payload
