"""Where files live, and the user's preferences.

User data follows the XDG spec, so an installed copy never writes next to its
own code: ~/.config/uninews/settings.json and ~/.local/share/uninews/uninews.db
"""

import copy
import json
import os
from pathlib import Path

APP_NAME = "uninews"

PACKAGE_DIR = Path(__file__).resolve().parent
PUBLISHERS_DIR = PACKAGE_DIR / "resources" / "publishers"


def xdg_dir(variable: str, default: str) -> Path:
    base = os.environ.get(variable) or Path.home() / default
    return Path(base) / APP_NAME


CONFIG_DIR = xdg_dir("XDG_CONFIG_HOME", ".config")
DATA_DIR = xdg_dir("XDG_DATA_HOME", ".local/share")
CACHE_DIR = xdg_dir("XDG_CACHE_HOME", ".cache")

SETTINGS_FILE = CONFIG_DIR / "settings.json"
DATABASE_FILE = DATA_DIR / "uninews.db"

DEFAULT_SETTINGS = {
    "theme": "light",
    "page_size": 12,
    "refresh_on_startup": True,
    "refresh_interval_minutes": 0,          # 0 = only when asked
    "max_cached_articles": 500,
}

MIN_REFRESH_INTERVAL_MINUTES = 15           # be kind to university servers


def load_settings() -> dict:
    """Defaults, with whatever the user has saved on top."""
    settings = copy.deepcopy(DEFAULT_SETTINGS)

    try:
        stored = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return settings
    except (json.JSONDecodeError, OSError):
        backup = SETTINGS_FILE.with_suffix(".json.broken")
        SETTINGS_FILE.replace(backup)       # keep it; don't silently wipe it
        return settings

    if isinstance(stored, dict):
        settings.update(stored)

    return settings


def save_settings(settings: dict) -> None:
    """Write atomically, so a crash mid-save can't corrupt the file."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary = SETTINGS_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    temporary.replace(SETTINGS_FILE)


def refresh_interval_ms(settings: dict) -> int:
    """Auto-refresh interval in milliseconds, or 0 when it is off."""
    minutes = int(settings.get("refresh_interval_minutes", 0) or 0)

    if minutes <= 0:
        return 0

    return max(minutes, MIN_REFRESH_INTERVAL_MINUTES) * 60 * 1000
