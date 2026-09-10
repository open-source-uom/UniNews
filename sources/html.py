"""Generic scraper for list pages, driven by CSS selectors from JSON."""

from collections.abc import Iterator

import requests
from bs4 import BeautifulSoup, Tag

from sources.base import Source


class HtmlSource(Source):
    """JSON keys:

    required: label, url, item_selector, title_selector
    optional: date_selector, summary_selector, image_selector (default "img"),
              pages (default 1), page_url (needed when pages > 1,
              e.g. "{url}?pn={page}" or "{url}/page/{page}/")
    """

    source_type = "html"
    required_keys = Source.required_keys + ("item_selector", "title_selector")

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
                break

            items.extend(page_items)

        return items

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
        for match in item.select(self.config["title_selector"]):
            link = match if match.name == "a" else match.select_one("a[href]")

            if link is None:
                continue

            href = (link.get("href") or "").strip()
            title = link.get_text(" ", strip=True)

            if not title or not href or href.startswith(("#", "javascript:")):
                continue

            if title.startswith(("http://", "https://")):
                continue

            return link

        return None

    def select_text(self, item: Tag, key: str) -> str:
        selector = self.config.get(key)

        if not selector:
            return ""

        element = item.select_one(selector)
        return element.get_text(" ", strip=True) if element else ""

    def find_image(self, item: Tag) -> str:
        image = item.select_one(self.config.get("image_selector", "img"))

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
