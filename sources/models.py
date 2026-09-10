"""The one article shape every source returns."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Article:
    publisher: str
    category: str
    source: str
    title: str
    link: str
    published: str | None = None
    summary: str = ""
    image_url: str = ""
    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
