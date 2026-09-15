"""Fetchers: JSON config in, Article objects out.

    from uninews.config import PUBLISHERS_DIR
    from uninews.fetchers import load_fetchers

    for fetcher in load_fetchers(PUBLISHERS_DIR):
        articles = fetcher.fetch()
"""

import json
from pathlib import Path

from uninews.article import Article
from uninews.fetchers import html, rss  # noqa: F401  importing registers the types
from uninews.fetchers.base import Fetcher

__all__ = ["Article", "Fetcher", "load_fetchers"]


def load_fetchers(path: Path, include_disabled: bool = False) -> list[Fetcher]:
    """Load one JSON file, or every *.json under a directory.

    Sources (or whole files) marked "enabled": false are skipped, so a site
    that blocks us can be parked without deleting its config.
    """
    path = Path(path)
    files = [path] if path.is_file() else sorted(path.rglob("*.json"))
    fetchers = []

    for file in files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"{file}: invalid JSON: {error}") from error

        publisher = data.get("publisher")

        if not publisher:
            raise ValueError(f"{file}: missing 'publisher'")

        if not (data.get("enabled", True) or include_disabled):
            continue

        defaults = data.get("defaults", {})

        for index, entry in enumerate(data.get("sources", []), start=1):
            config = {**defaults, **entry}

            if not (config.get("enabled", True) or include_disabled):
                continue

            fetcher_class = Fetcher.registry.get(config.get("type", ""))

            if fetcher_class is None:
                raise ValueError(
                    f"{file}: source #{index} has unknown type {config.get('type')!r}"
                )

            try:
                fetchers.append(
                    fetcher_class(publisher, data.get("category", ""), config)
                )
            except ValueError as error:
                raise ValueError(f"{file}: source #{index}: {error}") from error

    return fetchers
