"""One article, drawn as a clickable card."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from uninews.article import Article
from uninews.ui.labels import initials, shorten_source

SUMMARY_LIMIT = 230


class ArticleCard(QFrame):
    """Emits clicked(link) when the user clicks anywhere on it."""

    clicked = pyqtSignal(str)

    def __init__(self, article: Article, parent=None):
        super().__init__(parent)

        self.article = article
        self.setObjectName("ArticleCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Keep the card at its natural height; without this the list stretches
        # a few cards to fill the whole viewport.
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(18)

        layout.addWidget(self.build_image(), alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(self.build_content(), stretch=1)

    def build_image(self) -> QLabel:
        image = QLabel(initials(self.article.publisher))
        image.setObjectName("ArticleImage")
        image.setFixedSize(132, 92)
        image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return image

    def build_content(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(8)

        for text, name, wrap in (
            (self.article.title or "Untitled", "ArticleTitle", True),
            (self.meta_text(), "ArticleMeta", True),
            (shorten(self.article.summary), "ArticleSummary", True),
            ("Open article →", "OpenArticleLabel", False),
        ):
            if not text:
                continue

            label = QLabel(text)
            label.setObjectName(name)
            label.setWordWrap(wrap)
            layout.addWidget(label)

        layout.addStretch()     # labels sit at the top, not spread out
        return layout

    def meta_text(self) -> str:
        parts = [self.article.publisher]
        source = shorten_source(self.article.source, self.article.publisher)

        if source != self.article.publisher:
            parts.append(source)

        if self.article.published:
            parts.append(self.article.published)

        return "  •  ".join(part for part in parts if part)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.article.link:
            self.clicked.emit(self.article.link)

        super().mousePressEvent(event)


def shorten(text: str, limit: int = SUMMARY_LIMIT) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit].rstrip() + "..."
