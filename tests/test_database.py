"""Database behaviour, using a temporary file per test."""

import pytest

from uninews.database import Database
from uninews.article import Article


def make_article(title, link, published_at=None, publisher="University of Macedonia",
                 source="UoM Main News", category="university", summary=""):
    return Article(
        publisher=publisher,
        category=category,
        source=source,
        title=title,
        link=link,
        published_at=published_at,
        summary=summary,
        fetched_at="2026-09-11 12:00:00",
    )


@pytest.fixture
def db(tmp_path):
    with Database(tmp_path / "test.db") as database:
        yield database


def test_save_returns_only_new_articles(db):
    first = [make_article("A", "https://x.gr/a"), make_article("B", "https://x.gr/b")]
    assert len(db.save_articles(first)) == 2

    second = [make_article("B", "https://x.gr/b"), make_article("C", "https://x.gr/c")]
    assert [a.title for a in db.save_articles(second)] == ["C"]
    assert db.count_articles() == 3


def test_newest_first_undated_goes_last_on_first_fetch(db):
    db.save_articles([
        make_article("old", "https://x.gr/1", "2026-01-01 00:00:00"),
        make_article("new", "https://x.gr/2", "2026-09-10 00:00:00"),
        make_article("undated", "https://x.gr/3"),  # age unknown: bottom
    ])
    assert [a.title for a in db.get_articles()] == ["new", "old", "undated"]


def test_undated_article_on_later_fetch_goes_on_top(db):
    db.save_articles([make_article("old", "https://x.gr/1", "2026-09-10 00:00:00")])
    db.save_articles([make_article("undated new", "https://x.gr/2")])  # fetched 2026-09-11

    assert [a.title for a in db.get_articles()] == ["undated new", "old"]


def test_greek_search_ignores_case_and_accents(db):
    db.save_articles([
        make_article("ΥΠΟΤΡΟΦΙΕΣ ΜΕΤΑΠΤΥΧΙΑΚΩΝ", "https://x.gr/1"),
        make_article("Πρόγραμμα εξεταστικής", "https://x.gr/2"),
    ])
    assert [a.title for a in db.get_articles(search="υποτροφίες")] == ["ΥΠΟΤΡΟΦΙΕΣ ΜΕΤΑΠΤΥΧΙΑΚΩΝ"]
    assert db.count_articles(search="εξεταστικης προγραμμα") == 1   # any word order
    assert db.count_articles(search="100%") == 0                     # % is literal


def test_filters_and_pages(db):
    db.save_articles([
        make_article(f"UoM {i}", f"https://uom.gr/{i}", f"2026-09-{i + 1:02d} 00:00:00")
        for i in range(5)
    ] + [
        make_article("UoWM", "https://uowm.gr/1", publisher="University of Western Macedonia",
                     source="UoWM Main News"),
    ])
    assert db.count_articles(publisher="University of Macedonia") == 5
    page_two = db.get_articles(publisher="University of Macedonia", limit=2, offset=2)
    assert [a.title for a in page_two] == ["UoM 2", "UoM 1"]


def test_source_tree(db):
    db.save_articles([
        make_article("a", "https://x.gr/1"),
        make_article("b", "https://x.gr/2", source="UoM Economics"),
        make_article("c", "https://x.gr/3", publisher="MIT", source="MIT News"),
    ])
    assert db.get_source_tree() == {
        "university": {
            "MIT": ["MIT News"],
            "University of Macedonia": ["UoM Economics", "UoM Main News"],
        }
    }


def test_trimmed_articles_do_not_return_as_new(db):
    articles = [
        make_article(str(i), f"https://x.gr/{i}", f"2026-09-{i + 1:02d} 00:00:00")
        for i in range(5)
    ]
    db.save_articles(articles)

    assert db.trim(3) == 2
    assert db.count_articles() == 3
    assert db.save_articles(articles) == []      # the 2 trimmed ones stay gone

    db.clear()
    assert len(db.save_articles(articles)) == 5  # clear() allows refetching


def test_articles_round_trip(db):
    article = make_article("T", "https://x.gr/1", "2026-09-10 00:00:00", summary="S")
    db.save_articles([article])
    assert db.get_articles() == [article]


def test_refuses_old_app_database(tmp_path):
    import sqlite3
    path = tmp_path / "old.db"
    sqlite3.connect(path).execute("CREATE TABLE articles (id INTEGER)").connection.commit()

    with pytest.raises(RuntimeError, match="old app"):
        Database(path)
