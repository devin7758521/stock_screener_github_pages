import os
from pathlib import Path

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "")

PUBLIC_DIR = Path("public")
DATA_DIR = PUBLIC_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"


def ensure_dirs():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

MIN_AVG_DOLLAR_VOLUME = float(os.getenv("MIN_AVG_DOLLAR_VOLUME", "50000000"))
VOLUME_MULTIPLIER = float(os.getenv("VOLUME_MULTIPLIER", "1.2"))
MAX_STOCK_COUNT_FOR_DEEPSEEK = int(os.getenv("MAX_STOCK_COUNT_FOR_DEEPSEEK", "10"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
CACHE_KEEP_DAYS = int(os.getenv("CACHE_KEEP_DAYS", "10"))

# Longbridge / LongPort OpenAPI (free tier, for fundamentals fallback)
LONGBRIDGE_APP_KEY = os.getenv("LONGBRIDGE_APP_KEY", "")
LONGBRIDGE_APP_SECRET = os.getenv("LONGBRIDGE_APP_SECRET", "")
LONGBRIDGE_ACCESS_TOKEN = os.getenv("LONGBRIDGE_ACCESS_TOKEN", "")
