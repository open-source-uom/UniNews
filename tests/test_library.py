"""Paging and filtering, with no UI involved."""

import pytest

from uninews.database import Database
from uninews.library import Library, Page
from uninews.article import Article


def make_article(index, publisher="University of Macedonia", source="UoM Main News"):
    return Article(
        publisher=publisher,
        category="university",
        source=source,
        title=f"Article {index}",
        link=f"https://x.gr/{publisher}/{index}",
        published_at=f"2026-09-{index % 28 + 1:02d} 00:00:00",
        fetched_at="2026-09-11 12:00:00",
    )


@pytest.fixture
def library(tmp_path):
    with Database(tmp_path / "test.db") as database:
        database.save_articles(
            [make_article(i) for i in range(25)]
            + [make_article(i, "MIT", "MIT News") for i in range(5)]
        )
        yield Library(database, page_size=10)


def test_first_page(library):
    page = library.current_page()

    assert len(page.articles) == 10
    assert (page.number, page.total_pages, page.total_articles) == (1, 3, 30)
    assert (page.first_index, page.last_index) == (1, 10)
    assert not page.has_previous and page.has_next


def test_last_page_is_partial(library):
    library.go_to_page(3)
    page = library.current_page()

    assert len(page.articles) == 10
    assert page.has_previous and not page.has_next


def test_filter_returns_to_page_one(library):
    library.go_to_page(3)
    library.set_filter(publisher="MIT")

    page = library.current_page()
    assert page.number == 1
    assert page.total_articles == 5
    assert all(a.publisher == "MIT" for a in page.articles)


def test_page_past_the_end_clamps(library):
    library.go_to_page(99)
    assert library.current_page().number == 3

    library.set_filter(publisher="MIT")   # only 1 page now
    assert library.current_page().number == 1


def test_search_combines_with_filter(library):
    library.set_filter(publisher="MIT", search="article 3")
    assert library.current_page().total_articles == 1


def test_clear_filter(library):
    library.set_filter(publisher="MIT")
    library.clear_filter()

    assert library.filter.is_empty
    assert library.current_page().total_articles == 30


def test_page_size_change_resets_page(library):
    library.go_to_page(3)
    library.set_page_size(30)

    page = library.current_page()
    assert (page.number, page.total_pages, len(page.articles)) == (1, 1, 30)


def test_empty_result(library):
    library.set_filter(search="δεν υπάρχει")
    page = library.current_page()

    assert page.articles == []
    assert (page.total_articles, page.total_pages) == (0, 1)
    assert (page.first_index, page.last_index) == (0, 0)
    assert not page.has_previous and not page.has_next


@pytest.mark.parametrize(
    "current, total_pages, expected",
    [
        (1, 1, [1]),
        (3, 7, [1, 2, 3, 4, 5, 6, 7]),          # small: show all
        (1, 12, [1, 2, None, 12]),              # near the start
        (6, 12, [1, None, 5, 6, 7, None, 12]),  # middle
        (12, 12, [1, None, 11, 12]),            # near the end
    ],
)
def test_page_buttons(library, current, total_pages, expected):
    library.set_page_size(10)
    library.database.clear()
    library.database.save_articles(
        [make_article(i, "Filler", "F") for i in range(total_pages * 10)]
    )
    library.go_to_page(current)

    assert library.page_buttons() == expected


def test_page_knows_its_range_without_a_database():
    page = Page(articles=[], number=2, size=12, total_articles=30)
    assert page.total_pages == 3
