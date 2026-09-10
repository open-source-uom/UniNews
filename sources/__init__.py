"""News sources: JSON config in, Article objects out.

    from sources import load_sources

    for source in load_sources(Path("data/sources")):
        articles = source.fetch()
"""

import importlib
import json
import pkgutil
from pathlib import Path

from sources import custom, html, rss  # noqa: F401  importing registers the types
from sources.base import Source
from sources.models import Article

for _module in pkgutil.iter_modules(custom.__path__):
    importlib.import_module(f"{custom.__name__}.{_module.name}")

__all__ = ["Article", "Source", "load_sources"]


def load_sources(path: Path) -> list[Source]:
    """Load one JSON file, or every *.json under a directory."""
    path = Path(path)
    files = [path] if path.is_file() else sorted(path.rglob("*.json"))
    sources = []

    for file in files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"{file}: invalid JSON: {error}") from error

        publisher = data.get("publisher")

        if not publisher:
            raise ValueError(f"{file}: missing 'publisher'")

        defaults = data.get("defaults", {})

        for index, entry in enumerate(data.get("sources", []), start=1):
            config = {**defaults, **entry}
            source_class = Source.registry.get(config.get("type", ""))

            if source_class is None:
                raise ValueError(
                    f"{file}: source #{index} has unknown type {config.get('type')!r}"
                )

            try:
                sources.append(source_class(publisher, data.get("category", ""), config))
            except ValueError as error:
                raise ValueError(f"{file}: source #{index}: {error}") from error

    return sources
