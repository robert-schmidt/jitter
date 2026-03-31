"""Persistent settings stored in ~/.jitter/config.json."""

import json
import os

_DIR = os.path.join(os.path.expanduser("~"), ".jitter")
_PATH = os.path.join(_DIR, "config.json")

DEFAULTS = {
    "schedule_enabled": False,
    "schedule_start": "09:00",
    "schedule_end": "18:00",
    "schedule_days": [0, 1, 2, 3, 4],  # Mon-Fri
    "pulse_interval": 120,              # 2 minutes
    "afk_threshold": 3600,              # 60 min
    "afk_skip": 600,                    # 10 min
    "launch_at_login": False,
}

_cache: dict | None = None


def _ensure_dir():
    os.makedirs(_DIR, exist_ok=True)


def load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(_PATH) as f:
            stored = json.load(f)
        # Merge with defaults so new keys are always present
        merged = {**DEFAULTS, **stored}
        _cache = merged
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        _cache = dict(DEFAULTS)
        return _cache


def save(cfg: dict):
    global _cache
    _ensure_dir()
    _cache = cfg
    with open(_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def get(key: str):
    return load()[key]
