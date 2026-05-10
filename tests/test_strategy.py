from stock_bot.sample_data import make_ohlcv
from stock_bot.strategy import weekly_metrics, daily_metrics, hard_pass_default, build_score_and_tags, weekly_ma60_deviation_risk_label


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


def test_weekly_ma60_deviation():
    weekly = make_ohlcv(rows=90, strong_last=True, freq="W")
    wm = weekly_metrics(weekly)
    assert "weekly_ma60_deviation" in wm
    assert "weekly_ma60_deviation_risk" in wm
    assert "weekly_ma60" in wm
    assert isinstance(wm["weekly_ma60_deviation"], float)
    # strong_last data: close > ma60, so deviation should be positive
    assert wm["weekly_ma60_deviation"] > 0


def test_deviation_risk_label():
    assert weekly_ma60_deviation_risk_label(-0.1) == "低于60周线"
    assert weekly_ma60_deviation_risk_label(0.3) == "正常延伸"
    assert weekly_ma60_deviation_risk_label(0.8) == "偏热"
    assert weekly_ma60_deviation_risk_label(1.4) == "明显过热"
    assert weekly_ma60_deviation_risk_label(2.0) == "极度延伸"
    assert weekly_ma60_deviation_risk_label(None) == "未知"
