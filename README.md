# UniNews

UniNews is a desktop application that brings news and announcements from
universities into a single place.

It started as a way to avoid visiting a dozen university and department pages
every day. Instead of opening several tabs, UniNews collects everything into one
window, stores it locally, and lets you search and filter it.

Written in Python with PyQt6. Publishers are plain JSON files: adding a
university usually means adding a few lines of configuration, not writing code.

## Features

- News from multiple universities in one window
- RSS/Atom feeds and selector-driven HTML scraping
- Local SQLite cache, so articles stay readable when a site is down
- Search that ignores case and accents (`υποτροφιες` finds `ΥΠΟΤΡΟΦΙΕΣ`)
- Filter by publisher or by individual source
- Articles sorted by publication date, across many different date formats
- Light and dark themes
- Background fetching: the window stays responsive while sources load
- A "Sources" view showing which sources failed on the last refresh, and why
- Configurable auto-refresh, article cache size and page size

## Install

### Arch Linux

```bash
makepkg -si
```

### Debian / Ubuntu

Download the `.deb` from the releases page, then:

```bash
sudo apt install ./uninews_0.2.0-1_all.deb
```

### From source

```bash
git clone https://github.com/open-source-uom/UniNews.git
cd UniNews
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running

```bash
uninews              # installed
python3 -m uninews   # from a source checkout
```

## Project structure

```text
UniNews/
├── pyproject.toml            build definition and dependencies
├── PKGBUILD                  Arch package
├── debian/                   Debian/Ubuntu package
├── packaging/                desktop entry and icon
├── src/uninews/
│   ├── __main__.py           entry point
│   ├── config.py             paths (XDG) and user settings
│   ├── database.py           SQLite storage, filtering, paging
│   ├── library.py            what the window is currently showing
│   ├── article.py            the Article record
│   ├── dates.py              many date formats -> one sortable format
│   ├── text.py               whitespace and accent handling
│   ├── fetchers/             how articles are retrieved
│   │   ├── base.py           Fetcher: HTTP, cleanup, deduplication
│   │   ├── html.py           HtmlFetcher: CSS-selector scraping
│   │   ├── rss.py            RssFetcher: RSS and Atom
│   │   └── __main__.py       command-line checker
│   ├── resources/publishers/ one JSON file per publisher
│   └── ui/                   widgets; only this layer imports Qt
└── tests/
```

Dependencies point one way: `ui -> library -> database -> fetchers`. Nothing
below `ui/` imports Qt, and only the main window touches the database.

## Adding a publisher

Create `src/uninews/resources/publishers/<name>.json`. Check for an RSS feed
first; it is more reliable than scraping.

```json
{
  "publisher": "MIT",
  "category": "university",
  "sources": [
    { "label": "MIT News", "type": "rss", "url": "https://news.mit.edu/rss/feed" }
  ]
}
```

For a site without a feed, describe its markup with CSS selectors. Open the
page, inspect one article, and find the repeating container and the title link
inside it.

```json
{
  "publisher": "Example University",
  "category": "university",
  "defaults": {
    "type": "html",
    "item_selector": "article.post",
    "title_selector": "h2.entry-title a",
    "date_selector": "time, .entry-date",
    "summary_selector": ".entry-summary",
    "page_url": "{url}/page/{page}/"
  },
  "sources": [
    { "label": "Example Main News", "url": "https://example.edu/news/", "pages": 3 }
  ]
}
```

| Key | Meaning |
|---|---|
| `type` | `rss` or `html` |
| `label` | Shown in the sidebar |
| `url` | First page of the list, or the feed |
| `item_selector` | Repeating element, one per article |
| `title_selector` | The title link inside an item |
| `date_selector`, `summary_selector`, `image_selector` | Optional |
| `pages`, `page_url` | Pagination; `{url}` and `{page}` are substituted |
| `enabled` | Set to `false` to park a source without deleting it |

Comma-separated selectors are tried left to right, and the first match wins.

Check your work before opening the app:

```bash
python3 -m uninews.fetchers src/uninews/resources/publishers/example.json
python3 -m uninews.fetchers          # or check every publisher
```

`OK` means articles were found, `EMPTY` means the selectors matched nothing, and
`FAIL` prints the reason (blocked, offline, or changed markup).

## Sites that need code

If selectors are not enough (a JSON API, dates only on the article page), add a
module to `src/uninews/fetchers/` that subclasses `HtmlFetcher` or `Fetcher`:

```python
from uninews.fetchers.html import HtmlFetcher


class ExampleAnnouncements(HtmlFetcher):
    fetcher_type = "example_announcements"

    def parse_item(self, item):
        raw = super().parse_item(item)
        ...
        return raw
```

Import it in `fetchers/__init__.py` so it registers itself, then reference it in
JSON with `"type": "example_announcements"`.

## Where data is stored

| What | Path |
|---|---|
| Settings | `~/.config/uninews/settings.json` |
| Article cache | `~/.local/share/uninews/uninews.db` |
| Generated UI assets | `~/.cache/uninews/` |

Deleting the database makes the next refresh fetch everything again.

## Development

```bash
python3 -m pytest -q          # tests: no network, no display needed
ruff check .
ruff check . --fix
```

Tests run against saved pages in `tests/fixtures/`, so a failure means the code
broke. To find out whether a *site* changed, run the fetcher checker instead.

## Being a good citizen

University servers are not free to hit. UniNews fetches at most six sites in
parallel and never more than one request at a time to the same site,
auto-refresh is limited to once every 15 minutes, and every request identifies
the application. If a site asks not to be fetched, remove it or set
`"enabled": false`.

## Roadmap

- More publishers, including news sites
- Managing sources from the UI
- Source health history across sessions
- Export and backup

## Contributing

The easiest contribution is a new publisher: add a JSON file, verify it with the
fetcher checker, and open a pull request.

Before opening a pull request:

1. `python3 -m pytest -q` passes.
2. `ruff check .` is clean.
3. Changes stay focused and easy to review.

## License

GNU General Public License v3.0.
