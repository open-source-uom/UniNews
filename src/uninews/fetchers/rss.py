"""RSS and Atom feeds."""

import feedparser
from bs4 import BeautifulSoup

from uninews.fetchers.base import Fetcher


class RssFetcher(Fetcher):
    """JSON keys: label, url"""

    fetcher_type = "rss"

    def fetch_raw(self) -> list[dict]:
        # Download ourselves so the timeout applies; feedparser has none.
        feed = feedparser.parse(self.request(self.url).content)

        if feed.bozo and not feed.entries:
            raise ValueError(f"not a valid feed: {feed.bozo_exception}")

        return [
            {
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published") or entry.get("updated"),
                "summary": html_to_text(entry.get("summary", "")),
                "image_url": find_image(entry),
            }
            for entry in feed.entries
        ]


def html_to_text(text: str) -> str:
    if "<" not in text:
        return text
    return BeautifulSoup(text, "html.parser").get_text(" ")


def find_image(entry) -> str:
    for key in ("media_content", "media_thumbnail"):
        media = entry.get(key)
        if media:
            return media[0].get("url", "")

    for link in entry.get("links", []):
        if link.get("type", "").startswith("image/"):
            return link.get("href", "")

    return ""
