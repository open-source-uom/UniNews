"""Base class for all sources: HTTP, validation, cleanup, registration."""

from abc import ABC, abstractmethod
from typing import ClassVar
from urllib.parse import urljoin

import requests

from uninews.dates import parse_date
from uninews.article import Article
from uninews.text import clean_text

class FetcherError(Exception):
    """A source could not deliver articles, with a reason a person can act on."""


USER_AGENT = "UniNews/0.2 (+https://github.com/open-source-uom/UniNews)"
TIMEOUT_SECONDS = 15


class Fetcher(ABC):
    """One page or feed to fetch, configured by a JSON entry.

    Subclasses set `fetcher_type` (the JSON "type" value) and implement fetch_raw().
    Defining a subclass registers it automatically.
    """

    fetcher_type: ClassVar[str] = ""
    required_keys: ClassVar[tuple[str, ...]] = ("label", "url")
    registry: ClassVar[dict[str, type["Fetcher"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.fetcher_type:
            return
        if cls.fetcher_type in Fetcher.registry:
            raise TypeError(f"Duplicate source type: {cls.fetcher_type!r}")
        Fetcher.registry[cls.fetcher_type] = cls

    def __init__(self, publisher: str, category: str, config: dict):
        missing = [key for key in self.required_keys if not config.get(key)]
        if missing:
            raise ValueError(f"missing {', '.join(missing)}")

        self.publisher = publisher
        self.category = category
        self.config = config
        self.label: str = config["label"]
        self.url: str = config["url"]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.publisher!r}, {self.label!r})"

    @abstractmethod
    def fetch_raw(self) -> list[dict]:
        """Return dicts with 'title' and 'link'.

        Optional keys: 'published', 'summary', 'image_url'.
        Links and image URLs may be relative.
        """

    def fetch(self) -> list[Article]:
        """Fetch, clean, and deduplicate. This is what the app calls."""
        articles = []
        seen_links = set()

        for raw in self.fetch_raw():
            title = clean_text(raw.get("title"))
            href = (raw.get("link") or "").strip()

            if not title or not href:
                continue

            link = urljoin(self.url, href)

            if link in seen_links:
                continue

            seen_links.add(link)
            image_url = raw.get("image_url") or ""
            published = clean_text(raw.get("published")) or None

            articles.append(
                Article(
                    publisher=self.publisher,
                    category=self.category,
                    source=self.label,
                    title=title,
                    link=link,
                    published=published,
                    published_at=parse_date(published),
                    summary=clean_text(raw.get("summary")),
                    image_url=urljoin(self.url, image_url) if image_url else "",
                )
            )

        return articles

    def request(self, url: str) -> requests.Response:
        response = requests.get(
            url,
            timeout=TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response

    def get_html(self, url: str) -> str:
        response = self.request(url)

        # Without a charset header, requests assumes ISO-8859-1 and garbles Greek.
        if "charset" not in response.headers.get("Content-Type", "").lower():
            response.encoding = response.apparent_encoding

        return response.text
