import json
from typing import Dict

from config import DATA_DIR, SAVE_PATH

DEFAULT_SAVE = {"best_score": 0, "best_rescued": 0, "tutorial_completed": False}


def load_save() -> Dict[str, int]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SAVE_PATH.exists():
        save_record(DEFAULT_SAVE)
        return DEFAULT_SAVE.copy()

    try:
        with SAVE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        save_record(DEFAULT_SAVE)
        return DEFAULT_SAVE.copy()

    if not isinstance(data, dict):
        save_record(DEFAULT_SAVE)
        return DEFAULT_SAVE.copy()

    return {
        "best_score": _safe_non_negative_int(data.get("best_score", 0)),
        "best_rescued": _safe_non_negative_int(data.get("best_rescued", 0)),
        "tutorial_completed": bool(data.get("tutorial_completed", False)),
    }


def save_record(data: Dict[str, int]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    clean_data = {
        "best_score": _safe_non_negative_int(data.get("best_score", 0)),
        "best_rescued": _safe_non_negative_int(data.get("best_rescued", 0)),
        "tutorial_completed": bool(data.get("tutorial_completed", False)),
    }
    with SAVE_PATH.open("w", encoding="utf-8") as file:
        json.dump(clean_data, file, ensure_ascii=False, indent=2)


def _safe_non_negative_int(value: object) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
