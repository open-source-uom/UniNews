import json

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget, QScrollArea,
)
from PyQt6.QtGui import QDesktopServices

from database import Database
from settings import FEEDS_FILE
from rss_service import fetch_feed
from ui.settings_dialog import SettingsDialog
from app_settings import load_app_settings
from PyQt6.QtCore import QTimer
from notifications import should_notify, send_article_notification

ARTICLE_LINK_ROLE = 1000

class UniNewsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UniNews")
        self.resize(1050, 720)

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.open_settings)

        self.database = Database()
        self.articles = []

        self.app_settings = load_app_settings()
        self.setup_ui()
        self.apply_theme()
        self.load_cached_articles()

        if self.app_settings.get("refresh_on_startup", True):
            self.refresh_news()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_news)

        self.apply_theme()
        self.apply_refresh_timer()

    def setup_ui(self):
        self.root = QWidget()
        self.root_layout = QVBoxLayout(self.root)
        self.root_layout.setContentsMargins(28, 24, 28, 24)
        self.root_layout.setSpacing(20)

        self.create_header()
        self.create_article_list()

        self.setCentralWidget(self.root)

    def create_header(self):
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")

        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(20)

        title_area = QVBoxLayout()
        title_area.setSpacing(4)

        self.title_label = QLabel("UniNews")
        self.title_label.setObjectName("TitleLabel")

        self.subtitle_label = QLabel("University news in one clean place")
        self.subtitle_label.setObjectName("SubtitleLabel")

        title_area.addWidget(self.title_label)
        title_area.addWidget(self.subtitle_label)

        self.refresh_button = QPushButton("Refresh news")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.clicked.connect(self.refresh_news)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.clicked.connect(self.open_settings)

        header_layout.addLayout(title_area)
        header_layout.addStretch()
        header_layout.addWidget(self.settings_button)
        header_layout.addWidget(self.refresh_button)

        self.root_layout.addWidget(header_card)

    def create_article_list(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("ArticleScrollArea")
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #080A14;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
                background-color: #080A14;
            }
        """)

        self.article_container = QWidget()
        self.article_container.setStyleSheet("background-color: #080A14;")
        self.article_container.setObjectName("ArticleContainer")
        self.article_layout = QVBoxLayout(self.article_container)
        self.article_layout.setContentsMargins(0, 0, 0, 0)
        self.article_layout.setSpacing(18)
        self.article_layout.addStretch()

        self.scroll_area.setWidget(self.article_container)
        self.root_layout.addWidget(self.scroll_area)

    def apply_light_theme(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #F4F0FA;
            }

            QWidget {
                font-family: "Segoe UI", "Inter", "Arial";
                color: #1F2937;
            }

            #HeaderCard {
                background-color: #FFFFFF;
                border-radius: 24px;
                border: 1px solid #E5D9F2;
            }

            #TitleLabel {
                color: #171124;
                font-size: 34px;
                font-weight: 900;
                letter-spacing: -1px;
            }

            #SubtitleLabel {
                color: #7E3AF2;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton {
                background-color: #FFFFFF;
                color: #2D1B45;
                border: 1px solid #D8C7EF;
                padding: 10px 18px;
                border-radius: 11px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton:hover {
                background-color: #F3E8FF;
                border: 1px solid #A855F7;
            }

            QPushButton:pressed {
                background-color: #E9D5FF;
            }

            #RefreshButton {
                background-color: #A855F7;
                color: #FFFFFF;
                border: none;
            }

            #RefreshButton:hover {
                background-color: #9333EA;
            }

            #RefreshButton:disabled {
                background-color: #C4B5FD;
                color: #FFFFFF;
            }

            QScrollArea {
                background-color: #F4F0FA;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
                background-color: #F4F0FA;
            }

            #ArticleCard {
                background-color: #FFFFFF;
                border: 1px solid #E6DDF3;
                border-radius: 24px;
            }

            #ArticleCard:hover {
                background-color: #FBF7FF;
                border: 1px solid #A855F7;
            }

            #ArticleImage {
                background-color: #F3E8FF;
                border: 1px solid #E9D5FF;
                border-radius: 18px;
                color: #7E22CE;
                font-size: 24px;
                font-weight: 900;
            }

            #ArticleTitle {
                color: #171124;
                font-size: 17px;
                font-weight: 850;
            }

            #ArticleMeta {
                color: #7E22CE;
                font-size: 12px;
                font-weight: 750;
            }

            #ArticleSummary {
                color: #4B5563;
                font-size: 13px;
            }

            #OpenArticleLabel {
                color: #A21CAF;
                font-size: 12px;
                font-weight: 850;
            }

            #EmptyLabel {
                color: #6B7280;
                font-size: 16px;
                padding: 60px;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 4px;
            }

            QScrollBar::handle:vertical {
                background: #D8B4FE;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #A855F7;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

        if hasattr(self, "article_container"):
            self.article_container.setStyleSheet("background-color: #F4F0FA;")

    def apply_dark_theme(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #080A14;
            }

            QWidget {
                font-family: "Segoe UI", "Inter", "Arial";
                color: #F8FAFC;
            }

            #HeaderCard {
                background-color: #111827;
                border-radius: 24px;
                border: 1px solid #2A3144;
            }

            #TitleLabel {
                color: #FFFFFF;
                font-size: 34px;
                font-weight: 900;
                letter-spacing: -1px;
            }

            #SubtitleLabel {
                color: #D8B4FE;
                font-size: 14px;
                font-weight: 500;
            }

            QPushButton {
                background-color: #1F2937;
                color: #F8FAFC;
                border: 1px solid #374151;
                padding: 10px 18px;
                border-radius: 11px;
                font-size: 13px;
                font-weight: 700;
            }

            QPushButton:hover {
                background-color: #312E81;
                border: 1px solid #C084FC;
            }

            QPushButton:pressed {
                background-color: #581C87;
            }

            #RefreshButton {
                background-color: #C084FC;
                color: #080A14;
                border: none;
            }

            #RefreshButton:hover {
                background-color: #E879F9;
            }

            #RefreshButton:disabled {
                background-color: #475569;
                color: #CBD5E1;
            }

            #ArticleScrollArea {
                background-color: transparent;
                border: none;
            }

            #ArticleCard {
                background-color: #111827;
                border: 1px solid #2A3144;
                border-radius: 22px;
            }

            #ArticleCard:hover {
                background-color: #161F33;
                border: 1px solid #C084FC;
            }

            #ArticleTitle {
                color: #FFFFFF;
                font-size: 17px;
                font-weight: 800;
                line-height: 1.3;
            }

            #ArticleMeta {
                color: #C084FC;
                font-size: 12px;
                font-weight: 700;
            }

            #ArticleSummary {
                color: #CBD5E1;
                font-size: 13px;
                line-height: 1.5;
            }

            #OpenArticleLabel {
                color: #F0ABFC;
                font-size: 12px;
                font-weight: 800;
            }

            #EmptyLabel {
                color: #94A3B8;
                font-size: 16px;
                padding: 60px;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 4px;
            }

            QScrollBar::handle:vertical {
                background: #374151;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #C084FC;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

    def load_feeds(self) -> list[dict]:
        try:
            with open(FEEDS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "Missing feeds file",
                f"Could not find:\n{FEEDS_FILE}",
            )
            return []
        except json.JSONDecodeError as error:
            QMessageBox.critical(
                self,
                "Invalid feeds file",
                f"Your feeds.json file has invalid JSON:\n{error}",
            )
            return []

    def refresh_news(self):
        self.clear_article_cards()

        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Refreshing...")

        feeds = self.load_feeds()
        print("Feeds loaded:", feeds)

        for feed in feeds:
            university_name = feed.get("name", "Unknown university")
            feed_url = feed.get("url", "")

            print("Fetching:", university_name, feed_url)

            try:
                articles = fetch_feed(university_name, feed_url)
                print("Fetched articles:", len(articles))

                self.database.save_articles(articles)
                print("Saved articles. DB now has:", len(self.database.get_articles(limit=5000)))

            except Exception as error:
                print(f"Could not fetch {university_name}: {error}")

        self.articles = self.database.get_articles()
        print("Articles loaded from DB:", len(self.articles))

        self.render_articles()

        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Refresh news")

    def load_cached_articles(self):
        self.articles = self.database.get_articles()
        self.render_articles()

    def open_article(self, item: QListWidgetItem):
        url = item.data(ARTICLE_LINK_ROLE)

        if url:
            QDesktopServices.openUrl(QUrl(url))

    def clear_article_cards(self):
        while self.article_layout.count():
            item = self.article_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def render_articles(self):
        self.clear_article_cards()

        if not self.articles:
            empty_label = QLabel("No articles found.\nTry refreshing your feeds.")
            empty_label.setObjectName("EmptyLabel")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.article_layout.addWidget(empty_label)
            self.article_layout.addStretch()
            return

        for article in self.articles:
            card = self.create_article_card(article)
            self.article_layout.addWidget(card)

        self.article_layout.addStretch()

    def create_article_card(self, article: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("ArticleCard")
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(18)

        image_box = QLabel()
        image_box.setObjectName("ArticleImage")
        image_box.setFixedSize(132, 92)
        image_box.setAlignment(Qt.AlignmentFlag.AlignCenter)

        university = article.get("university", "UniNews")
        initials = "".join(word[0] for word in university.split()[:2]).upper()

        image_box.setText(initials)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)

        title = QLabel(article.get("title", "Untitled"))
        title.setObjectName("ArticleTitle")
        title.setWordWrap(True)

        published = article.get("published", "Unknown date")

        meta = QLabel(f"{university}  •  {published}")
        meta.setObjectName("ArticleMeta")
        meta.setWordWrap(True)

        summary_text = self.clean_text(article.get("summary", ""))

        if len(summary_text) > 230:
            summary_text = summary_text[:230].strip() + "..."

        summary = QLabel(summary_text)
        summary.setObjectName("ArticleSummary")
        summary.setWordWrap(True)

        open_label = QLabel("Open article →")
        open_label.setObjectName("OpenArticleLabel")

        content_layout.addWidget(title)
        content_layout.addWidget(meta)
        content_layout.addWidget(summary)
        content_layout.addWidget(open_label)

        card_layout.addWidget(image_box)
        card_layout.addLayout(content_layout)

        link = article.get("link", "")

        def open_link(event):
            if link:
                QDesktopServices.openUrl(QUrl(link))

        card.mousePressEvent = open_link

        return card

    def clean_text(self, text: str) -> str:
        clean = text.replace("\n", " ").replace("\r", " ").strip()
        return " ".join(clean.split())

    def open_settings(self):
        dialog = SettingsDialog(self)

        if dialog.exec():
            self.app_settings = load_app_settings()
            self.apply_theme()
            self.apply_refresh_timer()

            max_cached_articles = self.app_settings.get("max_cached_articles", 500)
            self.database.enforce_article_limit(max_cached_articles)

            self.articles = self.database.get_articles()
            self.render_articles()

            self.statusBar().showMessage("Settings saved.")

    def handle_notifications(self, new_articles: list[dict]) -> None:
        if not self.app_settings.get("notifications_enabled", False):
            return

        keywords = self.app_settings.get("notification_keywords", [])

        for article in new_articles:
            if should_notify(article, keywords):
                send_article_notification(article)

    def apply_refresh_timer(self) -> None:
        interval_minutes = self.app_settings.get("refresh_interval_minutes", 0)

        self.refresh_timer.stop()

        if interval_minutes and interval_minutes > 0:
            self.refresh_timer.start(interval_minutes * 60 * 1000)

    def apply_theme(self) -> None:
        theme = self.app_settings.get("theme", "light")

        if theme == "dark":
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
