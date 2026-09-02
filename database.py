import sqlite3
from pathlib import Path

import settings


class Database:
    def __init__(self, database_path: Path | None = None):
        if database_path is None:
            database_path = settings.DATABASE_PATH

        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row

        self.create_tables()

    def create_tables(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university TEXT NOT NULL,
                source TEXT,
                title TEXT NOT NULL,
                summary TEXT,
                link TEXT NOT NULL UNIQUE,
                published TEXT,
                fetched_at TEXT NOT NULL,
                image_url TEXT
            );
            """
        )
        self.connection.commit()

        try:
            self.connection.execute("ALTER TABLE articles ADD COLUMN image_url TEXT;")
            self.connection.commit()
        except sqlite3.OperationalError:
            pass

        try:
            self.connection.execute("ALTER TABLE articles ADD COLUMN source TEXT;")
            self.connection.commit()
        except sqlite3.OperationalError:
            pass

    def save_article(self, article: dict) -> None:
        query = """
        INSERT OR IGNORE INTO articles (
            university,
            source,
            title,
            summary,
            link,
            published,
            fetched_at,
            image_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        self.connection.execute(
            query,
            (
                article.get("university", "Unknown university"),
                article.get("source", article.get("university", "Unknown source")),
                article.get("title", "Untitled"),
                article.get("summary", ""),
                article.get("link", ""),
                article.get("published", "Unknown date"),
                article.get("fetched_at", ""),
                article.get("image_url", ""),
            ),
        )

        self.connection.commit()

    def save_articles(self, articles: list[dict]) -> None:
        for article in articles:
            self.save_article(article)

    def build_article_filters(
        self,
        university=None,
        source=None,
        search_text=None,
    ) -> tuple[str, list]:
        filters = ["1 = 1"]
        params = []

        if university and university != "All":
            filters.append("university = ?")
            params.append(university)

        if source and source != "All":
            filters.append("source = ?")
            params.append(source)

        if search_text:
            filters.append(
                """
                (
                    title LIKE ?
                    OR summary LIKE ?
                    OR university LIKE ?
                    OR source LIKE ?
                )
                """
            )
            search_pattern = f"%{search_text}%"
            params.extend(
                [
                    search_pattern,
                    search_pattern,
                    search_pattern,
                    search_pattern,
                ]
            )

        return " AND ".join(filters), params

    def get_articles(
        self,
        university=None,
        source=None,
        search_text=None,
        limit: int = 12,
        offset: int = 0,
    ) -> list[dict]:
        where_clause, params = self.build_article_filters(
            university=university,
            source=source,
            search_text=search_text,
        )

        query = f"""
        SELECT
            id,
            university,
            source,
            title,
            summary,
            link,
            published,
            fetched_at,
            image_url
        FROM articles
        WHERE {where_clause}
        ORDER BY id DESC
        LIMIT ?
        OFFSET ?;
        """

        params.extend([limit, offset])

        cursor = self.connection.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def count_articles(
        self,
        university=None,
        source=None,
        search_text=None,
    ) -> int:
        where_clause, params = self.build_article_filters(
            university=university,
            source=source,
            search_text=search_text,
        )

        query = f"""
        SELECT COUNT(*) AS total
        FROM articles
        WHERE {where_clause};
        """

        cursor = self.connection.execute(query, params)
        row = cursor.fetchone()

        return row["total"] if row else 0

    def delete_all_articles(self) -> None:
        self.connection.execute("DELETE FROM articles;")
        self.connection.commit()

    def enforce_article_limit(self, max_articles: int) -> None:
        query = """
        DELETE FROM articles
        WHERE id NOT IN (
            SELECT id
            FROM articles
            ORDER BY id DESC
            LIMIT ?
        );
        """

        self.connection.execute(query, (max_articles,))
        self.connection.commit()

    def get_universities(self) -> list[str]:
        query = """
        SELECT DISTINCT university
        FROM articles
        ORDER BY university ASC;
        """

        cursor = self.connection.execute(query)
        rows = cursor.fetchall()

        return [row["university"] for row in rows]

    def get_sources_for_university(self, university: str) -> list[str]:
        cursor = self.connection.execute(
            """
            SELECT DISTINCT source
            FROM articles
            WHERE university = ?
            ORDER BY source ASC;
            """,
            (university,),
        )

        return [row["source"] for row in cursor.fetchall() if row["source"]]

    def close(self) -> None:
        self.connection.close()
