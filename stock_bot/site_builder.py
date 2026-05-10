import json
from datetime import datetime
from .config import DATA_DIR, RUNS_DIR, ensure_dirs


def build_history_index():
    """Scan RUNS_DIR and rebuild history.json."""
    history = []
    for f in sorted(RUNS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            history.append({"date": f.stem, "count": len(data.get("items", [])), "generated_at": data.get("generated_at", "")})
        except Exception:
            history.append({"date": f.stem, "count": None, "generated_at": ""})
    (DATA_DIR / "history.json").write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def write_site_data(payload):
    ensure_dirs()
    date_key = datetime.now().strftime("%Y-%m-%d")
    latest_file = DATA_DIR / "latest.json"
    run_file = RUNS_DIR / f"{date_key}.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    latest_file.write_text(text, encoding="utf-8")
    run_file.write_text(text, encoding="utf-8")

    build_history_index()
    return latest_file, run_file
