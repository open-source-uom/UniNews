"""Search box and the category / publisher / source tree."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from uninews.ui.labels import shorten_source

FILTER_ROLE = Qt.ItemDataRole.UserRole
ALL_LABEL = "All sources"
INDENT = "    "


class Sidebar(QFrame):
    """Emits filter_changed(category, publisher, source) and search_changed(text).

    Empty strings mean "no filter".
    """

    filter_changed = pyqtSignal(str, str, str)
    search_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Sidebar")
        self.setFixedWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Sources")
        title.setObjectName("SidebarTitle")

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search articles...")
        self.search_input.textChanged.connect(
            lambda text: self.search_changed.emit(text.strip())
        )

        self.tree = QListWidget()
        self.tree.setObjectName("SourceList")
        self.tree.itemClicked.connect(self.on_item_clicked)

        # Long names are cut with "..." instead of growing a horizontal scrollbar.
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tree.setUniformItemSizes(True)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.tree, stretch=1)

    def set_sources(self, tree: dict[str, dict[str, list[str]]]) -> None:
        """tree is {category: {publisher: [source, ...]}}, from Database.

        Keeps the current selection if it still exists.
        """
        selected = self.current_filter()

        self.tree.blockSignals(True)
        self.tree.clear()

        self.add_row(ALL_LABEL, ("", "", ""))

        for category, publishers in tree.items():
            for publisher, sources in publishers.items():
                self.add_row(publisher, (category, publisher, ""))

                for source in sources:
                    if source != publisher:
                        self.add_row(
                            INDENT + shorten_source(source, publisher),
                            (category, publisher, source),
                            tooltip=source,
                        )

        self.select(selected)
        self.tree.blockSignals(False)

    def add_row(
        self, text: str, value: tuple[str, str, str], tooltip: str = ""
    ) -> None:
        item = QListWidgetItem(text)
        item.setData(FILTER_ROLE, value)
        item.setToolTip(tooltip or text)
        self.tree.addItem(item)

    def current_filter(self) -> tuple[str, str, str]:
        item = self.tree.currentItem()
        return item.data(FILTER_ROLE) if item else ("", "", "")

    def select(self, value: tuple[str, str, str]) -> None:
        for row in range(self.tree.count()):
            if self.tree.item(row).data(FILTER_ROLE) == value:
                self.tree.setCurrentRow(row)
                return

        self.tree.setCurrentRow(0)   # selection disappeared: fall back to "All"

    def on_item_clicked(self, item: QListWidgetItem) -> None:
        self.filter_changed.emit(*item.data(FILTER_ROLE))
