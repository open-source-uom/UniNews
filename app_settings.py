import json

from settings import APP_DATA_DIR

SETTINGS_FILE = APP_DATA_DIR / "settings.json"


DEFAULT_SETTINGS = {
    "refresh_on_startup": True,
    "refresh_interval_minutes": 0,
    "notifications_enabled": False,
    "notification_keywords": ["deadline", "scholarship", "application", "exam"],
    "theme": "light",
    "max_cached_articles": 500,
    "custom_rss_feeds": [],
}


def load_app_settings() -> dict:
    if not SETTINGS_FILE.exists():
        save_app_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            settings = json.load(file)

        merged_settings = DEFAULT_SETTINGS.copy()
        merged_settings.update(settings)

        return merged_settings

    except json.JSONDecodeError:
        save_app_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()


def save_app_settings(settings: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=4)
