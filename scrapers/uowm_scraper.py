from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper


class UowmNewsScraper(BaseScraper):
    name = "University of Western Macedonia"

    def __init__(self, max_pages_per_source: int = 3):
        self.max_pages_per_source = max_pages_per_source

        self.sources = [
            {
                "label": "UoWM Main News",
                "base_url": "https://www.uowm.gr",
                "first_page": "https://www.uowm.gr/en/news/",
                "item_selector": ".post-list-item",
                "title_selector": "h4.post-title a, .post-title a",
                "date_selector": ".post-date span, .post-date",
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
                "title_selector": "h3.entry-title a.tpg-post-link, .entry-title a",
                "date_selector": ".post-meta-tags .date a, .date",
                "summary_selector": ".tpg-excerpt-inner",
            },
            {
                "label": "UoWM Chemical Engineering",
                "base_url": "https://chemeng.uowm.gr",
                "first_page": "https://chemeng.uowm.gr/enimerosi/",
                "item_selector": "article.type-post, article.post",
                "title_selector": "h3 a, h2 a, .entry-title a",
                "date_selector": ".date, .entry-date, time, .posted-on",
                "summary_selector": ".entry-summary, .entry-content, p",
            },
            {
                "label": "UoWM Mineral Resources Engineering",
                "base_url": "https://mre.uowm.gr",
                "first_page": "https://mre.uowm.gr/en/category/announcements/",
                "item_selector": ".post.type-post, .type-post",
                "title_selector": "h2 a, .entry-title a",
                "date_selector": ".entry-meta, .entry-date, time",
                "summary_selector": ".entry-summary, .entry-content",
            },
            {
                "label": "UoWM Product and Systems Design Engineering - First Years",
                "base_url": "https://ide.uowm.gr",
                "first_page": "https://ide.uowm.gr/category/protoeteis_25/",
                "item_selector": "article.type-post, article.post",
                "title_selector": "h2 a, .entry-title a",
                "date_selector": "time, .entry-date, .posted-on",
                "summary_selector": ".entry-summary, .entry-content",
            },
            {
                "label": "UoWM Product and Systems Design Engineering - News",
                "base_url": "https://ide.uowm.gr",
                "first_page": "https://ide.uowm.gr/en/category/news/",
                "item_selector": "article.type-post, article.post",
                "title_selector": "h2 a, .entry-title a",
                "date_selector": "time, .entry-date, .posted-on",
                "summary_selector": ".entry-summary, .entry-content",
            },
            {
                "label": "UoWM Early Childhood Education",
                "base_url": "https://nured.uowm.gr",
                "first_page": "https://nured.uowm.gr/news/",
                "item_selector": "article.type-post, article.post",
                "title_selector": "h2 a, .entry-title a",
                "date_selector": "time, .entry-date, .posted-on",
                "summary_selector": ".entry-summary, .entry-content",
            },
            {
                "label": "UoWM Computer Science",
                "base_url": "https://cs.uowm.gr",
                "first_page": "https://cs.uowm.gr/en/home-page/",
                "item_selector": ".latest-news-item",
                "title_selector": ".latest-news-title a, h3 a",
                "date_selector": ".latest-news-date, time, .posted-on",
                "summary_selector": ".latest-news-text-content p, .latest-news-excerpt",
                "max_pages": 1,
            },
            {
                "label": "UoWM Agriculture",
                "base_url": "https://agro.uowm.gr",
                "first_page": "https://agro.uowm.gr/home/",
                "item_selector": ".uael-post-wrapper",
                "title_selector": ".uael-post__title a, h5 a",
                "date_selector": ".uael-post__date, .uael-post__meta-data, time",
                "summary_selector": ".uael-post__excerpt, .uael-post__content-wrap",
                "max_pages": 1,
            },
            {
                "label": "UoWM Regional and Cross-Border Development",
                "base_url": "https://rdcbs.uowm.gr",
                "first_page": "https://rdcbs.uowm.gr/nea/",
                "item_selector": "article.post-list-item, .post-list-item",
                "title_selector": "h3 a, .post-title a",
                "date_selector": ".post-date, time",
                "summary_selector": ".post-excerpt, .entry-summary, p",
            },
            {
                "label": "UoWM International and European Economic Studies",
                "base_url": "https://iees.uowm.gr",
                "first_page": "https://iees.uowm.gr/category/anakoinoseis/",
                "item_selector": ".post.type-post, .type-post",
                "title_selector": "h2 a, .entry-title a",
                "date_selector": ".entry-meta, .entry-date, time",
                "summary_selector": ".entry-summary, .entry-content",
            },
            {
                "label": "UoWM Business Administration",
                "base_url": "https://ba.uowm.gr",
                "first_page": "https://ba.uowm.gr/category/anakoinoseis/",
                "item_selector": "article.type-post, article.post",
                "title_selector": "h3 a, h2 a, .entry-title a",
                "date_selector": ".post-date, .entry-date, time",
                "summary_selector": ".entry-summary, .entry-content, p",
            },
            {
                "label": "UoWM Applied and Fine Arts",
                "base_url": "https://eetf.uowm.gr",
                "first_page": "https://eetf.uowm.gr/en/category/news/",
                "item_selector": ".news-mini-wrap.type-post, .news-mini-wrap",
                "title_selector": "h1 a, h2 a, .entry-title a",
                "date_selector": "time, .news-meta",
                "summary_selector": ".news-summary, .entry-summary, .entry-content",
            },
            {
                "label": "UoWM Occupational Therapy",
                "base_url": "https://ot.uowm.gr",
                "first_page": "https://ot.uowm.gr/",
                "item_selector": "#left-sidebar .widget_text h3",
                "title_selector": "a",
                "date_selector": "",
                "summary_selector": "",
                "max_pages": 1,
            },
            {
                "label": "UoWM Midwifery",
                "base_url": "https://mw.uowm.gr",
                "first_page": "https://mw.uowm.gr/category/genikes-anakoinoseis/",
                "item_selector": "article.type-post, article.post",
                "title_selector": "h2 a, .entry-title a",
                "date_selector": "time, .entry-date, .posted-on",
                "summary_selector": ".entry-summary, .entry-content",
            },
        ]

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
