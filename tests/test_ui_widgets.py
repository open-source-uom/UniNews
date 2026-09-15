"""Widget smoke tests. Skipped when PyQt6 or a display is unavailable."""

import os

import pytest

pytest.importorskip("PyQt6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication  # noqa: E402

from uninews.library import Page  # noqa: E402
from uninews.article import Article  # noqa: E402
from uninews.ui.article_card import ArticleCard, shorten  # noqa: E402
from uninews.ui.labels import initials, initialism, shorten_source  # noqa: E402
from uninews.ui.article_list import ArticleList  # noqa: E402
from uninews.ui.pagination import Pagination  # noqa: E402
from uninews.ui.sidebar import ALL_LABEL, Sidebar  # noqa: E402
from uninews.ui.theme import DARK, LIGHT, stylesheet  # noqa: E402


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


def make_article(title="T", publisher="University of Macedonia", source="UoM Main News"):
    return Article(
        publisher=publisher,
        category="university",
        source=source,
        title=title,
        link=f"https://x.gr/{title}",
        published="10 Σεπτεμβρίου 2026",
        summary="Summary text",
    )


@pytest.mark.parametrize("theme", [LIGHT, DARK])
def test_stylesheet_has_no_unresolved_placeholders(theme):
    css = stylesheet(theme)
    assert "{p." not in css and "None" not in css
    assert "#ArticleCard" in css and "#PaginationBar" in css


def test_card_emits_link_on_click(app, qtbot=None):
    from PyQt6.QtCore import QPointF, Qt
    from PyQt6.QtGui import QMouseEvent

    card = ArticleCard(make_article())
    received = []
    card.clicked.connect(received.append)

    card.mousePressEvent(
        QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(1, 1),
            QPointF(1, 1),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
    )

    assert received == ["https://x.gr/T"]


def test_card_meta_skips_repeated_source(app):
    card = ArticleCard(make_article(publisher="MIT", source="MIT"))
    assert card.meta_text() == "MIT  •  10 Σεπτεμβρίου 2026"


def test_initials_and_shorten():
    assert initials("University of Western Macedonia") == "UWM"   # skips "of"
    assert initials("University of Macedonia") == "UM"
    assert initials("MIT") == "MIT"
    assert initials("") == "UN"
    assert shorten("a" * 300).endswith("...")
    assert shorten("  spaced   out  ") == "spaced out"


def test_article_list_shows_cards_then_message(app):
    widget = ArticleList()

    widget.show_articles([make_article("A"), make_article("B")])
    assert count_cards(widget) == 2

    widget.show_articles([])          # empty result replaces the cards
    assert count_cards(widget) == 0

    widget.show_message("Fetching...")
    assert count_cards(widget) == 0


def count_cards(widget: ArticleList) -> int:
    return sum(
        isinstance(widget.layout.itemAt(i).widget(), ArticleCard)
        for i in range(widget.layout.count())
    )


def test_sidebar_rows_and_signal(app):
    sidebar = Sidebar()
    sidebar.set_sources(
        {
            "university": {
                "MIT": ["MIT News"],
                "University of Macedonia": ["UoM Main News", "UoM Economics"],
            }
        }
    )

    labels = [sidebar.tree.item(i).text() for i in range(sidebar.tree.count())]
    assert labels[0] == ALL_LABEL
    assert "MIT" in labels

    row = next(
        i for i in range(sidebar.tree.count())
        if sidebar.tree.item(i).toolTip() == "UoM Economics"
    )
    assert labels[row].strip() == "Economics"      # publisher prefix dropped

    received = []
    sidebar.filter_changed.connect(lambda *args: received.append(args))
    sidebar.on_item_clicked(sidebar.tree.item(row))

    assert received == [("university", "University of Macedonia", "UoM Economics")]


def test_sidebar_keeps_selection_across_refresh(app):
    sidebar = Sidebar()
    tree = {"university": {"MIT": ["MIT News"], "UoM": ["UoM Main News"]}}
    sidebar.set_sources(tree)

    row = next(
        i for i in range(sidebar.tree.count()) if sidebar.tree.item(i).text() == "MIT"
    )
    sidebar.tree.setCurrentRow(row)

    sidebar.set_sources(tree)                                    # refresh
    assert sidebar.current_filter() == ("university", "MIT", "")

    sidebar.set_sources({"university": {"UoM": ["UoM Main News"]}})  # MIT gone
    assert sidebar.current_filter() == ("", "", "")


def test_pagination_summary_and_buttons(app):
    bar = Pagination(page_size=10)
    page = Page(articles=[make_article()] * 10, number=2, size=10, total_articles=95)

    bar.update(page, [1, 2, 3, None, 10])

    assert bar.summary.text() == "Showing 11-20 of 95"
    assert bar.previous_button.isEnabled() and bar.next_button.isEnabled()

    texts = [
        bar.page_buttons_layout.itemAt(i).widget().text()
        for i in range(bar.page_buttons_layout.count())
    ]
    assert texts == ["1", "2", "3", "...", "10"]


def test_pagination_hidden_when_empty(app):
    bar = Pagination(page_size=10)
    bar.update(Page([], 1, 10, 0), [1])
    assert not bar.isVisible()


def test_pagination_emits_requested_page(app):
    bar = Pagination(page_size=10)
    bar.update(Page([make_article()], 3, 10, 95), [1, None, 3, None, 10])

    received = []
    bar.page_changed.connect(received.append)

    bar.previous_button.click()
    bar.next_button.click()

    assert received == [2, 4]


def test_card_meta_drops_publisher_prefix_from_source(app):
    card = ArticleCard(
        make_article(publisher="University of Western Macedonia", source="UoWM Midwifery")
    )
    assert card.meta_text().startswith("University of Western Macedonia  •  Midwifery  •")


def test_long_source_names_do_not_scroll_sideways(app):
    from PyQt6.QtCore import Qt

    sidebar = Sidebar()
    sidebar.set_sources({
        "university": {
            "University of Western Macedonia": [
                "UoWM Product and Systems Design Engineering - First Years",
            ]
        }
    })

    assert sidebar.tree.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    assert sidebar.tree.textElideMode() == Qt.TextElideMode.ElideRight

    item = sidebar.tree.item(sidebar.tree.count() - 1)
    assert item.toolTip().startswith("UoWM Product")     # full name still reachable


def test_publisher_prefix_is_dropped_only_when_it_matches():
    assert initialism("University of Western Macedonia") == "UoWM"

    assert shorten_source("UoWM Midwifery", "University of Western Macedonia") == "Midwifery"
    assert shorten_source("MIT News", "MIT") == "MIT News"
    assert shorten_source("Announcements", "University of Macedonia") == "Announcements"


def test_cards_keep_their_natural_height(app):
    from PyQt6.QtWidgets import QSizePolicy

    card = ArticleCard(make_article())
    assert card.sizePolicy().verticalPolicy() == QSizePolicy.Policy.Maximum
