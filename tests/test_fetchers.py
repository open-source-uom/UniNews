"""Offline tests: config files load, and saved pages still parse.

Run from the repo root:  python -m pytest
"""

from pathlib import Path

from unittest.mock import patch

import pytest

from uninews.fetchers import load_fetchers
from uninews.fetchers.base import Fetcher, FetcherError

from uninews.config import PUBLISHERS_DIR
FIXTURES = Path(__file__).resolve().parent / "fixtures"

# (source label, saved page in tests/fixtures/)
PAGE_FIXTURES = [
    ("UoM Main News", "uom_nea.html"),
    ("UoWM Main News", "uowm_news.html"),
]


def find_source(label: str):
    for source in load_fetchers(PUBLISHERS_DIR):
        if source.label == label:
            return source
    raise LookupError(f"No source labeled {label!r}")


def test_all_source_files_load():
    sources = load_fetchers(PUBLISHERS_DIR)

    assert sources
    keys = [(source.publisher, source.label) for source in sources]
    assert len(keys) == len(set(keys)), "duplicate publisher/label"


@pytest.mark.parametrize("label, fixture", PAGE_FIXTURES)
def test_saved_page_parses(label, fixture):
    path = FIXTURES / fixture

    if not path.exists():
        pytest.skip(f"fixture not saved yet: {fixture}")

    items = find_source(label).parse_page(path.read_text(encoding="utf-8"))

    assert items, "no items found: selectors or parser broke"
    assert all(item["title"] and item["link"] for item in items)


BOT_CHECK_PAGE = """<!DOCTYPE html><html><head><title>Loading...</title>
<script>document.cookie = "x=1"; fetch('/firewall.php');</script></head>
<body><p>System loading...</p></body></html>"""


def test_bot_check_page_fails_instead_of_returning_nothing():
    source = find_source("UoM Main News")

    with patch.object(Fetcher, "get_html", return_value=BOT_CHECK_PAGE):
        with pytest.raises(FetcherError, match="bot-check"):
            source.fetch()


def test_changed_markup_fails_instead_of_returning_nothing():
    source = find_source("UoM Main News")
    page = "<html><body>" + "<div>redesigned</div>" * 500 + "</body></html>"

    with patch.object(Fetcher, "get_html", return_value=page):
        with pytest.raises(FetcherError, match="markup"):
            source.fetch()
