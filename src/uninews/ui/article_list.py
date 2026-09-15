"""Scrollable list of article cards, with empty and error states."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from uninews.article import Article
from uninews.ui.article_card import ArticleCard


class ArticleList(QScrollArea):
    """Emits article_clicked(link). Call show_articles() or show_message()."""

    article_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setObjectName("ArticleScrollArea")

        self.container = QWidget()
        self.container.setObjectName("ArticleContainer")

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(18)
        self.layout.addStretch()

        self.setWidget(self.container)

    def show_articles(self, articles: list[Article]) -> None:
        self.clear()

        if not articles:
            self.show_message("No articles found.\nTry refreshing or changing the filter.")
            return

        for article in articles:
            card = ArticleCard(article)
            card.clicked.connect(self.article_clicked)
            self.layout.addWidget(card)

        self.layout.addStretch()
        self.scroll_to_top()

    def show_message(self, text: str) -> None:
        """Replace the list with one centred message (empty result, error, loading)."""
        self.clear()

        label = QLabel(text)
        label.setObjectName("StatusLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)

        self.layout.addWidget(label)
        self.layout.addStretch()

    def clear(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def scroll_to_top(self) -> None:
        self.verticalScrollBar().setValue(0)
