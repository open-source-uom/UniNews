"""The one article shape every source returns."""

from dataclasses import dataclass, field

from uninews.dates import now_sortable


@dataclass
class Article:
    publisher: str
    category: str
    source: str
    title: str
    link: str
    published: str | None = None      # date text as shown on the site
    published_at: str | None = None   # parsed "YYYY-MM-DD HH:MM:SS", or None
    summary: str = ""
    image_url: str = ""
    fetched_at: str = field(default_factory=now_sortable)
