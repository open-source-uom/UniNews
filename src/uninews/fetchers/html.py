"""Generic scraper for list pages, driven by CSS selectors from JSON."""

from collections.abc import Iterator
from functools import lru_cache

import requests
from bs4 import BeautifulSoup, Tag

from uninews.fetchers.base import Fetcher, FetcherError


class HtmlFetcher(Fetcher):
    """JSON keys:

    required: label, url, item_selector, title_selector
    optional: date_selector, summary_selector, image_selector (default "img"),
              pages (default 1), page_url (needed when pages > 1,
              e.g. "{url}?pn={page}" or "{url}/page/{page}/")

    Comma-separated title/date/summary/image selectors are tried left to right:
    the first one that matches wins. (Plain CSS would pick whichever element
    comes first in the page instead.)
    """

    fetcher_type = "html"
    required_keys = Fetcher.required_keys + ("item_selector", "title_selector")

    noise_phrases = (
        "Continue reading →",
        "Read more",
        "Συνεχίστε την ανάγνωση →",
        "Περισσότερα",
    )

    def __init__(self, publisher: str, category: str, config: dict):
        super().__init__(publisher, category, config)

        self.pages = int(config.get("pages", 1))

        if self.pages > 1 and "{page}" not in config.get("page_url", ""):
            raise ValueError("'pages' > 1 needs a 'page_url' containing {page}")

    def fetch_raw(self) -> list[dict]:
        items = []

        for number, page_url in enumerate(self.page_urls(), start=1):
            try:
                html = self.get_html(page_url)
            except requests.RequestException:
                if number == 1:
                    raise
                break

            page_items = self.parse_page(html)

            if not page_items:
                if number == 1:
                    raise FetcherError(self.explain_empty_page(html))
                break

            items.extend(page_items)

        return items

    def explain_empty_page(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")

        if len(html) < 5000 and soup.find("script"):
            title = soup.title.get_text(strip=True) if soup.title else ""
            return (
                f"got a bot-check or JavaScript-only page ({title!r}) "
                "instead of the news list"
            )

        return "no items matched item_selector; the site's markup may have changed"

    def page_urls(self) -> Iterator[str]:
        yield self.url

        template = self.config.get("page_url", "")
        base = self.url.rstrip("/")

        for page in range(2, self.pages + 1):
            yield template.replace("{url}", base).replace("{page}", str(page))

    def parse_page(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results = []

        for item in soup.select(self.config["item_selector"]):
            raw = self.parse_item(item)

            if raw:
                results.append(raw)

        return results

    def parse_item(self, item: Tag) -> dict | None:
        link = self.find_link(item)

        if link is None:
            return None

        return {
            "title": self.strip_noise(link.get_text(" ", strip=True)),
            "link": link.get("href", ""),
            "published": self.select_text(item, "date_selector"),
            "summary": self.strip_noise(self.select_text(item, "summary_selector")),
            "image_url": self.find_image(item),
        }

    def find_link(self, item: Tag) -> Tag | None:
        for selector in split_selectors(self.config["title_selector"]):
            for match in item.select(selector):
                link = match if match.name == "a" else match.select_one("a[href]")

                if link is not None and self.is_article_link(link):
                    return link

        return None

    def is_article_link(self, link: Tag) -> bool:
        href = (link.get("href") or "").strip()
        title = self.strip_noise(link.get_text(" ", strip=True)).strip()

        if not title or not href or href.startswith(("#", "javascript:")):
            return False

        return not title.startswith(("http://", "https://"))

    def select_text(self, item: Tag, key: str) -> str:
        selector = self.config.get(key)

        if not selector:
            return ""

        element = select_first(item, selector)
        return element.get_text(" ", strip=True) if element else ""

    def find_image(self, item: Tag) -> str:
        image = select_first(item, self.config.get("image_selector", "img"))

        if image is None:
            return ""

        src = (
            image.get("data-src")
            or image.get("data-lazy-src")
            or image.get("src")
            or ""
        )

        if not src and image.get("srcset"):
            parts = image["srcset"].split(",")[0].split()
            src = parts[0] if parts else ""

        return "" if src.startswith("data:") else src

    def strip_noise(self, text: str) -> str:
        for phrase in self.noise_phrases:
            text = text.replace(phrase, "")
        return text


def select_first(item: Tag, selector: str) -> Tag | None:
    """Try each comma-separated selector in order; return the first match."""
    for part in split_selectors(selector):
        element = item.select_one(part)
        if element is not None:
            return element
    return None


@lru_cache(maxsize=256)
def split_selectors(selector: str) -> tuple[str, ...]:
    """Split "a, b" into ("a", "b"), ignoring commas inside (), [] or quotes."""
    parts, current, depth, quote = [], [], 0, ""

    for char in selector:
        if quote:
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
        elif char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue

        current.append(char)

    parts.append("".join(current).strip())
    return tuple(part for part in parts if part)
