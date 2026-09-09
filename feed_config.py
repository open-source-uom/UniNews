import json

from settings import FEEDS_FILE


def load_builtin_feeds() -> list[dict]:
    if not FEEDS_FILE.exists():
        return []

    with open(FEEDS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_all_feeds(app_settings: dict) -> list[dict]:
    builtin_feeds = load_builtin_feeds()
    custom_feeds = app_settings.get("custom_rss_feeds", [])

    feeds = []
    seen = set()

    for feed in builtin_feeds + custom_feeds:
        source_type = feed.get("type", "rss")

        if source_type == "rss":
            name = feed.get("name", "").strip()
            url = feed.get("url", "").strip()

            if not name or not url:
                continue

            key = ("rss", url.lower())

        elif source_type == "scraper":
            name = feed.get("name", "").strip()
            scraper = feed.get("scraper", "").strip()

            if not name or not scraper:
                continue

            key = ("scraper", scraper.lower())

        else:
            continue

        if key in seen:
            continue

        seen.add(key)
        feeds.append(feed)

    return feeds
