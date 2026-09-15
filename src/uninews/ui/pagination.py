"""Pagination bar: summary, previous/next, numbered pages, page size."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton

from uninews.library import PAGE_SIZES, Page


class Pagination(QFrame):
    """Emits page_changed(number) and page_size_changed(size)."""

    page_changed = pyqtSignal(int)
    page_size_changed = pyqtSignal(int)

    def __init__(self, page_size: int, parent=None):
        super().__init__(parent)

        self.setObjectName("PaginationBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.summary = QLabel()
        self.summary.setObjectName("PaginationSummary")

        self.previous_button = self.make_button("‹ Previous", "PaginationButton")
        self.next_button = self.make_button("Next ›", "PaginationButton")

        self.page_buttons_layout = QHBoxLayout()
        self.page_buttons_layout.setSpacing(6)

        self.size_combo = QComboBox()
        self.size_combo.setObjectName("PaginationSize")

        for size in PAGE_SIZES:
            self.size_combo.addItem(f"{size} / page", size)

        self.size_combo.setCurrentIndex(self.size_combo.findData(page_size))
        self.size_combo.currentIndexChanged.connect(
            lambda: self.page_size_changed.emit(self.size_combo.currentData())
        )

        layout.addWidget(self.summary)
        layout.addStretch()
        layout.addWidget(self.previous_button)
        layout.addLayout(self.page_buttons_layout)
        layout.addWidget(self.next_button)
        layout.addSpacing(8)
        layout.addWidget(self.size_combo)

        self.current_page = 1
        self.previous_button.clicked.connect(
            lambda: self.page_changed.emit(self.current_page - 1)
        )
        self.next_button.clicked.connect(
            lambda: self.page_changed.emit(self.current_page + 1)
        )

    def make_button(self, text: str, name: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(name)
        return button

    def update(self, page: Page, buttons: list[int | None]) -> None:
        """Redraw from the current Page. buttons comes from Library.page_buttons()."""
        self.current_page = page.number
        self.setVisible(page.total_articles > 0)

        if not page.total_articles:
            return

        self.summary.setText(
            f"Showing {page.first_index}-{page.last_index} of {page.total_articles}"
        )
        self.previous_button.setEnabled(page.has_previous)
        self.next_button.setEnabled(page.has_next)

        self.clear_page_buttons()

        for number in buttons:
            self.page_buttons_layout.addWidget(
                self.make_gap() if number is None else self.make_page_button(number, page)
            )

    def make_gap(self) -> QLabel:
        label = QLabel("...")
        label.setObjectName("PaginationDots")
        return label

    def make_page_button(self, number: int, page: Page) -> QPushButton:
        button = QPushButton(str(number))

        if number == page.number:
            button.setObjectName("PageButtonActive")
            button.setEnabled(False)
        else:
            button.setObjectName("PageButton")
            button.clicked.connect(lambda _, n=number: self.page_changed.emit(n))

        return button

    def clear_page_buttons(self) -> None:
        while self.page_buttons_layout.count():
            widget = self.page_buttons_layout.takeAt(0).widget()

            if widget is not None:
                widget.deleteLater()
