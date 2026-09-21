"""SQLite storage for articles.

Use it from one thread only (the UI thread). Fetch in a worker, save here.
"""

import sqlite3
from collections.abc import Iterable
from dataclasses import astuple, fields
from pathlib import Path
from typing import Self

from uninews.article import Article
from uninews.text import fold

SCHEMA_VERSION = 1

ARTICLE_COLUMNS = [field.name for field in fields(Article)]

SCHEMA = f"""
CREATE TABLE articles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    publisher    TEXT NOT NULL,
    category     TEXT NOT NULL,
    source       TEXT NOT NULL,
    title        TEXT NOT NULL,
    link         TEXT NOT NULL UNIQUE,
    published    TEXT,
    published_at TEXT,
    summary      TEXT NOT NULL,
    image_url    TEXT NOT NULL,
    fetched_at   TEXT NOT NULL,
    sort_at      TEXT NOT NULL,   -- see sort_key()
    search_text  TEXT NOT NULL    -- lowercase, accent-free copy for search
);

CREATE INDEX articles_by_date ON articles (sort_at DESC, id DESC);
CREATE INDEX articles_by_source ON articles (category, publisher, source);

-- Links removed by trim(), so they don't come back as new on the next refresh.
CREATE TABLE removed_links (
    link TEXT PRIMARY KEY
);

PRAGMA user_version = {SCHEMA_VERSION};
"""

INSERT_ARTICLE = f"""
INSERT OR IGNORE INTO articles ({", ".join(ARTICLE_COLUMNS)}, sort_at, search_text)
SELECT {", ".join("?" * (len(ARTICLE_COLUMNS) + 2))}
WHERE NOT EXISTS (SELECT 1 FROM removed_links WHERE link = ?)
"""


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._create_or_check_schema()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    # --- writing -----------------------------------------------------------

    def save_articles(self, articles: Iterable[Article]) -> list[Article]:
        """Store articles not seen before. Returns only the new ones."""
        new_articles = []

        with self.connection:
            known_sources = {
                (row[0], row[1])
                for row in self.connection.execute(
                    "SELECT DISTINCT publisher, source FROM articles"
                )
            }

            for article in articles:
                cursor = self.connection.execute(
                    INSERT_ARTICLE,
                    (
                        *astuple(article),
                        sort_key(article, known_sources),
                        search_text(article),
                        article.link,
                    ),
                )

                if cursor.rowcount == 1:
                    new_articles.append(article)

        return new_articles

    def trim(self, max_articles: int) -> int:
        """Keep the newest max_articles. Returns how many were removed."""
        with self.connection:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO removed_links (link)
                SELECT link FROM articles
                ORDER BY sort_at DESC, id DESC
                LIMIT -1 OFFSET ?
                """,
                (max_articles,),
            )
            cursor = self.connection.execute(
                "DELETE FROM articles WHERE link IN (SELECT link FROM removed_links)"
            )

        return cursor.rowcount

    def clear(self) -> None:
        """Delete everything, so the next refresh fetches all articles again."""
        with self.connection:
            self.connection.execute("DELETE FROM articles")
            self.connection.execute("DELETE FROM removed_links")

    # --- reading -----------------------------------------------------------

    def get_articles(
        self,
        *,
        category: str | None = None,
        publisher: str | None = None,
        source: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Article]:
        """Newest first. None means "no filter"."""
        where, params = build_where(category, publisher, source, search)

        rows = self.connection.execute(
            f"""
            SELECT {", ".join(ARTICLE_COLUMNS)}
            FROM articles
            {where}
            ORDER BY sort_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        )

        return [Article(**dict(row)) for row in rows]

    def count_articles(
        self,
        *,
        category: str | None = None,
        publisher: str | None = None,
        source: str | None = None,
        search: str | None = None,
    ) -> int:
        where, params = build_where(category, publisher, source, search)
        row = self.connection.execute(
            f"SELECT COUNT(*) FROM articles {where}", params
        ).fetchone()
        return row[0]

    def get_source_tree(self) -> dict[str, dict[str, list[str]]]:
        """{category: {publisher: [source, ...]}} for the sidebar."""
        tree: dict[str, dict[str, list[str]]] = {}

        rows = self.connection.execute(
            """
            SELECT DISTINCT category, publisher, source
            FROM articles
            ORDER BY category, publisher, source
            """
        )

        for row in rows:
            tree.setdefault(row["category"], {}).setdefault(row["publisher"], []).append(
                row["source"]
            )

        return tree

    # --- schema ------------------------------------------------------------

    def _create_or_check_schema(self) -> None:
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]

        if version == SCHEMA_VERSION:
            return

        if version == 0:
            has_tables = self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table'"
            ).fetchone()

            if has_tables:
                raise RuntimeError(
                    f"{self.path} is a database from the old app. "
                    "Use a new path or delete the file."
                )

            self.connection.executescript(SCHEMA)
            return

        raise RuntimeError(
            f"{self.path} has schema version {version}, "
            f"this app supports {SCHEMA_VERSION}."
        )


def sort_key(article: Article, known_sources: set[tuple[str, str]]) -> str:
    """Where an article goes in the newest-first list.

    - Has a date: its date.
    - No date, source fetched before: fetch time, since it appeared since last refresh.
    - No date, first fetch of this source: bottom, since its real age is unknown.
    """
    if article.published_at:
        return article.published_at

    if (article.publisher, article.source) in known_sources:
        return article.fetched_at

    return ""


def search_text(article: Article) -> str:
    return fold(f"{article.title} {article.summary} {article.publisher} {article.source}")


def build_where(
    category: str | None,
    publisher: str | None,
    source: str | None,
    search: str | None,
) -> tuple[str, list]:
    clauses, params = [], []

    for column, value in (("category", category), ("publisher", publisher), ("source", source)):
        if value:
            clauses.append(f"{column} = ?")
            params.append(value)

    # Every word must appear somewhere, in any order.
    for word in fold(search).split():
        clauses.append("search_text LIKE ? ESCAPE '\\'")
        params.append(f"%{escape_like(word)}%")

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params


def escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
