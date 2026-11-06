"""Local configuration management for FreeScrape.

All configuration is stored in a plain JSON file under the user's home
directory. There is no paid account, no remote login, and no telemetry.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".freescrape"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS: Dict[str, Any] = {
    "user_agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "proxy": None,                 # e.g. "http://127.0.0.1:7890" or None for direct
    "timeout": 30,                 # seconds
    "output_format": "human",     # human | json | pretty
    "browser_headless": True,
    "browser_user_data_dir": None,  # persistent session dir for `browser`
    # Optional LLM (OpenAI-compatible). Leave blank to disable AI features.
    "llm_api_key": None,
    "llm_base_url": "https://api.openai.com/v1",
    "llm_model": "gpt-4o-mini",
}


def ensure_config() -> Path:
    """Make sure the config directory and file exist; return the path."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(DEFAULTS, indent=2, ensure_ascii=False), encoding="utf-8")
    return CONFIG_PATH


def load_config() -> Dict[str, Any]:
    """Load config, merging saved values over defaults."""
    ensure_config()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if v is not None})
    return merged


def save_config(data: Dict[str, Any]) -> None:
    """Persist the full config dict to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def set_key(key: str, value: Any) -> Dict[str, Any]:
    """Set a single key and return the updated config."""
    cfg = load_config()
    cfg[key] = value
    save_config(cfg)
    return cfg


def get_key(key: str) -> Any:
    return load_config().get(key)
