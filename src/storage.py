import json
import os
from datetime import datetime
from typing import Any, Dict, List, Set

DATA_DIR = os.path.join(os.getcwd(), "data")
SEEN_PATH = os.path.join(DATA_DIR, "seen.json")
LOG_PATH = os.path.join(DATA_DIR, "bot.log")
SNAPSHOT_DIR = os.path.join(DATA_DIR, "snapshots")

def log(msg: str) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    line = f"{datetime.now().isoformat()} | {msg}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    print(msg, flush=True)

def load_seen() -> Set[str]:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SEEN_PATH):
        return set()
    try:
        with open(SEEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return set(str(x) for x in data)
        return set()
    except Exception:
        return set()

def save_seen(seen: Set[str]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen)), f, ensure_ascii=False, indent=2)

def save_snapshot(items: List[Dict[str, Any]]) -> str:
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(SNAPSHOT_DIR, f"items_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    return path
