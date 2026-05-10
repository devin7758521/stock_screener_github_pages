from stock_bot.sample_data import make_ohlcv
from stock_bot.strategy import weekly_metrics, daily_metrics, hard_pass_default, build_score_and_tags


def test_metrics_and_default_pass():
    weekly = make_ohlcv(rows=90, strong_last=True, freq="W")
    daily = make_ohlcv(rows=140, strong_last=True, freq="D")
    wm = weekly_metrics(weekly)
    dm = daily_metrics(daily)
    metrics = {**wm, **dm}
    assert metrics["weekly_body_ratio"] >= 1
    assert metrics["daily_body_ratio"] >= 1
    assert metrics["volume_ratio"] > 1
    assert hard_pass_default(metrics) is True


def test_score_tags():
    weekly = make_ohlcv(rows=90, strong_last=True, freq="W")
    daily = make_ohlcv(rows=140, strong_last=True, freq="D")
    metrics = {**weekly_metrics(weekly), **daily_metrics(daily), "beat_spy_60d": True, "beat_qqq_60d": False}
    score, tags = build_score_and_tags(metrics)
    assert score >= 6
    assert "周K实体突破" in tags
