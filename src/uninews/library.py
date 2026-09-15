"""Filter and page state for the article list.

Holds what the user is looking at (filter, search, page) and asks the
database for that page. No Qt here, so it can be tested on its own.
"""

from dataclasses import dataclass, replace

from uninews.database import Database
from uninews.article import Article

PAGE_SIZES = (10, 12, 20, 30, 50)


@dataclass(frozen=True)
class Filter:
    """What the user picked in the sidebar. None means "everything"."""

    category: str | None = None
    publisher: str | None = None
    source: str | None = None
    search: str = ""

    @property
    def is_empty(self) -> bool:
        return self == Filter()


@dataclass(frozen=True)
class Page:
    """One page of articles, plus what the pagination bar needs to draw itself."""

    articles: list[Article]
    number: int
    size: int
    total_articles: int

    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total_articles // self.size))  # ceiling division

    @property
    def first_index(self) -> int:
        """1-based index of the first article shown, 0 when the page is empty."""
        return (self.number - 1) * self.size + 1 if self.articles else 0

    @property
    def last_index(self) -> int:
        return self.first_index + len(self.articles) - 1 if self.articles else 0

    @property
    def has_previous(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.total_pages


class Library:
    """The article list the window shows, as one object.

    Change the filter or page, then call current_page(). Changing a filter
    always returns to page 1, which is what keeps the sidebar and the list
    from drifting apart.
    """

    def __init__(self, database: Database, page_size: int = 12):
        self.database = database
        self.filter = Filter()
        self.page_size = page_size
        self.page_number = 1

    # --- changing what is shown -------------------------------------------

    def set_filter(self, **changes) -> None:
        """set_filter(publisher="MIT") or set_filter(search="υποτροφίες")."""
        self.filter = replace(self.filter, **changes)
        self.page_number = 1

    def clear_filter(self) -> None:
        self.filter = Filter()
        self.page_number = 1

    def set_page_size(self, size: int) -> None:
        self.page_size = max(1, size)
        self.page_number = 1

    def go_to_page(self, number: int) -> None:
        self.page_number = max(1, number)

    # --- reading ----------------------------------------------------------

    def current_page(self) -> Page:
        """Fetch the current page, clamping to the last page if it's past the end."""
        total = self.database.count_articles(**vars(self.filter))
        size = self.page_size
        last_page = max(1, -(-total // size))

        self.page_number = min(self.page_number, last_page)

        articles = self.database.get_articles(
            **vars(self.filter),
            limit=size,
            offset=(self.page_number - 1) * size,
        )

        return Page(articles, self.page_number, size, total)

    def page_buttons(self, window: int = 1) -> list[int | None]:
        """Page numbers to draw; None is a gap ("...").

        Always shows the first and last page, plus `window` pages either side
        of the current one: [1, None, 4, 5, 6, None, 12]
        """
        total = self.current_page().total_pages

        if total <= 2 * window + 5:
            return list(range(1, total + 1))

        start = max(2, self.page_number - window)
        end = min(total - 1, self.page_number + window)

        buttons: list[int | None] = [1]

        if start > 2:
            buttons.append(None)

        buttons.extend(range(start, end + 1))

        if end < total - 1:
            buttons.append(None)

        buttons.append(total)
        return buttons
