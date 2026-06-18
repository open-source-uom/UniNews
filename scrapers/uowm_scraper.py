from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper


class UowmNewsScraper(BaseScraper):
    name = "University of Western Macedonia"

    def __init__(self, max_pages_per_source: int = 5):
        self.max_pages_per_source = max_pages_per_source

        self.sources = [
            {
                "label": "UoWM Main News",
                "base_url": "https://www.uowm.gr",
                "first_page": "https://www.uowm.gr/en/news/",
                "item_selector": ".post-list-item",
                "title_selector": "h4.post-title a",
                "date_selector": ".post-date span",
                "summary_selector": ".post-item-excerpt",
            },
            {
                "label": "UoWM Electrical and Computer Engineering",
                "base_url": "https://ece.uowm.gr",
                "first_page": (
                    "https://ece.uowm.gr/"
                    "%ce%b3%ce%b5%ce%bd%ce%b9%ce%ba%ce%b5%cf%83-"
                    "%ce%b1%ce%bd%ce%b1%ce%ba%ce%bf%ce%b9%ce%bd%cf%89%cf%83%ce%b5%ce%b9%cf%83/"
                ),
                "item_selector": ".rt-list-item",
                "title_selector": "h3.entry-title a.tpg-post-link",
                "date_selector": ".post-meta-tags .date a",
                "summary_selector": ".tpg-excerpt-inner",
            },
            {
                "label": "UoWM Chemical Engineering",
                "base_url": "https://chemeng.uowm.gr",
                "first_page": "https://chemeng.uowm.gr/enimerosi/",
                "item_selector": "article.post",
                "title_selector": ".entry-title a, .cmsms_post_title a",
                "date_selector": ".published, abbr.published, .cmsms_post_date",
                "summary_selector": ".entry-content, .cmsms_post_content",
            },
            {
                "label": "UoWM Mineral Resources Engineering",
                "base_url": "https://mre.uowm.gr",
                "first_page": "https://mre.uowm.gr/en/category/announcements/",
                "item_selector": ".post, article",
                "title_selector": ".entry-title a, h2 a, h3 a",
                "date_selector": ".entry-date, .posted-on, time",
                "summary_selector": ".entry-summary, .entry-content",
            },
            {
                "label": "UoWM Product and Systems Design Engineering - First Years",
                "base_url": "https://ide.uowm.gr",
                "first_page": "https://ide.uowm.gr/category/protoeteis_25/",
                "item_selector": "article.post",
                "title_selector": "h2.entry-title a, .entry-title a",
                "date_selector": ".entry-date, time, .posted-on",
                "summary_selector": ".entry-summary, .entry-content",
            },
            {
                "label": "UoWM Product and Systems Design Engineering - News",
                "base_url": "https://ide.uowm.gr",
                "first_page": "https://ide.uowm.gr/en/category/news/",
                "item_selector": "article.post",
                "title_selector": "h2.entry-title a, .entry-title a",
                "date_selector": ".entry-date, time, .posted-on",
                "summary_selector": ".entry-summary, .entry-content",
            },
        ]

    def scrape(self) -> list[dict]:
        articles = []
        seen_links = set()

        for source in self.sources:
            for page_number in range(1, self.max_pages_per_source + 1):
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

        return f"{first_page_url}page/{page_number}/"

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
        return response.text

    def parse_page(self, html: str, source: dict) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        results = []

        items = soup.select(source["item_selector"])

        for item in items:
            title_link = item.select_one(source["title_selector"])

            if not title_link:
                continue

            title = title_link.get_text(" ", strip=True)
            link = urljoin(source["base_url"], title_link.get("href", ""))

            date_element = item.select_one(source["date_selector"])
            published = (
                date_element.get_text(" ", strip=True)
                if date_element
                else "Unknown date"
            )

            summary_element = item.select_one(source["summary_selector"])
            summary = (
                summary_element.get_text(" ", strip=True) if summary_element else ""
            )

            image_element = item.select_one("img")
            image_url = ""

            if image_element and image_element.get("src"):
                image_url = urljoin(source["base_url"], image_element.get("src"))

            results.append(
                {
                    "university": self.name,
                    "source": source["label"],
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published": published,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "image_url": image_url,
                }
            )

        return results
