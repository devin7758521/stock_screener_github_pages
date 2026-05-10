import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stock_bot.config import RUNS_DIR, CACHE_KEEP_DAYS
from stock_bot.site_builder import build_history_index


def main():
    if not RUNS_DIR.exists():
        return
    cutoff = datetime.now().date() - timedelta(days=CACHE_KEEP_DAYS)
    for file in RUNS_DIR.glob("*.json"):
        try:
            file_date = datetime.strptime(file.stem, "%Y-%m-%d").date()
        except ValueError:
            continue
        if file_date < cutoff:
            print(f"Delete old cache: {file}")
            file.unlink()

    build_history_index()


if __name__ == "__main__":
    main()
