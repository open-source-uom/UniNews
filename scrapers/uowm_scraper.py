from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from scrapers.university_source_loader import load_university_source_config


class UowmNewsScraper(BaseScraper):
    name = "University of Western Macedonia"

    def __init__(self):
        config = load_university_source_config("uowm_sources.json")

        self.name = config["university"]
        self.max_pages_per_source = int(config.get("default_max_pages", 3))
        self.sources = config["sources"]

    def scrape(self) -> list[dict]:
        articles = []
        seen_links = set()

        for source in self.sources:
            max_pages = int(source.get("max_pages", self.max_pages_per_source))

            for page_number in range(1, max_pages + 1):
                page_url = self.build_page_url(source["first_page"], page_number)

                try:
                    html = self.fetch_page(page_url)
                    page_articles = self.parse_page(html, source)

                    if not page_articles:
                        break

                    for article in page_articles:
                        link = article.get("link")

                        if link and link not in seen_links:
                            seen_links.add(link)
                            articles.append(article)

                except Exception as error:
                    print(
                        f"Could not scrape {source['label']} "
                        f"page {page_number}: {error}"
                    )
                    break

        return articles

    def build_page_url(self, first_page_url: str, page_number: int) -> str:
        if page_number == 1:
            return first_page_url

        return f"{first_page_url.rstrip('/')}/page/{page_number}/"

    def fetch_page(self, url: str) -> str:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": (
                    "UniNews/0.1 (+https://github.com/open-source-uom/UniNews)"
                )
            },
        )

        response.raise_for_status()
        response.encoding = response.apparent_encoding

        return response.text

    def parse_page(self, html: str, source: dict) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results = []

        items = soup.select(source["item_selector"])

        for item in items:
            title_link = self.find_title_link(item, source["title_selector"])

            if not title_link:
                continue

            title = self.clean_text(title_link.get_text(" ", strip=True))
            href = title_link.get("href", "")

            if not title or not href or href.startswith("#"):
                continue

            if title.startswith("http://") or title.startswith("https://"):
                continue

            link = urljoin(source["base_url"], href)

            published = self.extract_text(item, source.get("date_selector", ""))
            summary = self.extract_text(item, source.get("summary_selector", ""))
            image_url = self.extract_image_url(item, source["base_url"])

            results.append(
                {
                    "university": self.name,
                    "source": source["label"],
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published": published or "Unknown date",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "image_url": image_url,
                }
            )

        return results

    def find_title_link(self, item, selector: str):
        for link in item.select(selector):
            if link.name != "a":
                link = link.select_one("a")

            if not link:
                continue

            title = self.clean_text(link.get_text(" ", strip=True))
            href = link.get("href", "")

            if title and href and not href.startswith("#"):
                return link

        return None

    def extract_text(self, item, selector: str) -> str:
        if not selector:
            return ""

        element = item.select_one(selector)

        if not element:
            return ""

        return self.clean_text(element.get_text(" ", strip=True))

    def extract_image_url(self, item, base_url: str) -> str:
        image = item.select_one("img")

        if not image:
            return ""

        src = (
            image.get("data-src")
            or image.get("data-lazy-src")
            or image.get("src")
            or ""
        )

        if not src and image.get("srcset"):
            src = image.get("srcset", "").split(",")[0].strip().split(" ")[0]

        if not src or src.startswith("data:image"):
            return ""

        return urljoin(base_url, src)

    def clean_text(self, text: str) -> str:
        cleaned = " ".join(text.split())

        remove_phrases = [
            "Continue reading →",
            "Read more",
            "Περισσότερα",
            "Συνεχίστε την ανάγνωση →",
        ]

        for phrase in remove_phrases:
            cleaned = cleaned.replace(phrase, "")

        return cleaned.strip()
