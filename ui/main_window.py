import json

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app_settings import load_app_settings
from database import Database
from notifications import send_article_notification, should_notify
from rss_service import fetch_feed
from scrapers.scraper_service import run_scraper
from settings import FEEDS_FILE
from ui.settings_dialog import SettingsDialog

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
        self.selected_university = "All"
        self.selected_source = "All"
        self.search_text = ""

        self.current_page = 1
        self.page_size = 12
        self.total_articles = 0
        self.total_pages = 1

        self.app_settings = load_app_settings()
        self.setup_ui()
        self.apply_theme()
        self.load_cached_articles()

        if self.app_settings.get("refresh_on_startup", True):
            self.refresh_news()
        else:
            QTimer.singleShot(1500, self.refresh_news)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_news)

        self.apply_theme()
        self.apply_refresh_timer()

    def get_theme_stylesheet(self, theme: str) -> str:
        if theme == "dark":
            bg = "#080A14"
            panel = "#111827"
            panel_2 = "#0B1220"
            border = "#2A3144"
            text = "#F8FAFC"
            muted = "#CBD5E1"
            accent = "#C084FC"
            accent_hover = "#E879F9"
            input_bg = "#111827"
            card = "#111827"
            card_hover = "#161F33"
            image_bg = "#1F2937"
        else:
            bg = "#F4F0FA"
            panel = "#FFFFFF"
            panel_2 = "#FFFFFF"
            border = "#E6DDF3"
            text = "#171124"
            muted = "#4B5563"
            accent = "#A855F7"
            accent_hover = "#9333EA"
            input_bg = "#F9F5FF"
            card = "#FFFFFF"
            card_hover = "#FBF7FF"
            image_bg = "#F3E8FF"

        return f"""
        QMainWindow, QDialog {{
            background-color: {bg};
        }}

        QWidget {{
            font-family: "Segoe UI", "Inter", "Arial";
            color: {text};
        }}

        #HeaderCard, #Sidebar {{
            background-color: {panel};
            border: 1px solid {border};
            border-radius: 24px;
        }}

        #TitleLabel {{
            color: {text};
            font-size: 34px;
            font-weight: 900;
        }}

        #SubtitleLabel, #ArticleMeta, #OpenArticleLabel {{
            color: {accent};
            font-weight: 700;
        }}

        QPushButton {{
            background-color: {panel_2};
            color: {text};
            border: 1px solid {border};
            padding: 10px 18px;
            border-radius: 11px;
            font-size: 13px;
            font-weight: 700;
        }}

        QPushButton:hover {{
            background-color: {card_hover};
            border: 1px solid {accent};
        }}

        #RefreshButton, #SaveButton {{
            background-color: {accent};
            color: white;
            border: none;
        }}

        #RefreshButton:hover, #SaveButton:hover {{
            background-color: {accent_hover};
        }}

        QLineEdit, QComboBox, QSpinBox {{
            background-color: {input_bg};
            color: {text};
            border: 1px solid {border};
            border-radius: 10px;
            padding: 8px 10px;
            font-size: 13px;
        }}

        QCheckBox {{
            color: {text};
            spacing: 8px;
        }}

        QScrollArea, QScrollArea > QWidget > QWidget, #ArticleContainer {{
            background-color: {bg};
            border: none;
        }}

        #ArticleCard {{
            background-color: {card};
            border: 1px solid {border};
            border-radius: 24px;
        }}

        #ArticleCard:hover {{
            background-color: {card_hover};
            border: 1px solid {accent};
        }}

        #ArticleImage {{
            background-color: {image_bg};
            border: 1px solid {border};
            border-radius: 18px;
            color: {accent};
            font-size: 24px;
            font-weight: 900;
        }}

        #ArticleTitle, #SidebarTitle {{
            color: {text};
            font-weight: 900;
        }}

        #ArticleSummary {{
            color: {muted};
            font-size: 13px;
        }}

        #SourceList {{
            background-color: transparent;
            border: none;
            outline: none;
        }}

        #SourceList::item {{
            color: {muted};
            padding: 10px 12px;
            border-radius: 10px;
        }}

        #SourceList::item:hover {{
            background-color: {card_hover};
            color: {text};
        }}

        #SourceList::item:selected {{
            background-color: {accent};
            color: white;
            font-weight: 800;
        }}
        """

    def setup_ui(self):
        self.root = QWidget()
        self.root_layout = QVBoxLayout(self.root)
        self.root_layout.setContentsMargins(28, 24, 28, 24)
        self.root_layout.setSpacing(20)

        self.create_header()

        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(20)

        self.create_sidebar()
        self.create_article_list()
        self.create_pagination_bar()

        self.article_area = QWidget()
        self.article_area_layout = QVBoxLayout(self.article_area)
        self.article_area_layout.setContentsMargins(0, 0, 0, 0)
        self.article_area_layout.setSpacing(12)

        self.article_area_layout.addWidget(self.scroll_area, stretch=1)
        self.article_area_layout.addWidget(self.pagination_bar)

        self.content_layout.addWidget(self.sidebar)
        self.content_layout.addWidget(self.article_area, stretch=1)

        self.root_layout.addLayout(self.content_layout)

        self.setCentralWidget(self.root)

    def update_source_list(self):
        self.source_list.clear()

        all_item = QListWidgetItem("All")
        all_item.setData(
            Qt.ItemDataRole.UserRole, {"university": "All", "source": "All"}
        )
        self.source_list.addItem(all_item)

        universities = self.database.get_universities()

        for university in universities:
            university_item = QListWidgetItem(university)
            university_item.setData(
                Qt.ItemDataRole.UserRole,
                {"university": university, "source": "All"},
            )
            self.source_list.addItem(university_item)

            sources = self.database.get_sources_for_university(university)

            for source in sources:
                if source == university:
                    continue

                source_item = QListWidgetItem(f"   └ {source}")
                source_item.setData(
                    Qt.ItemDataRole.UserRole,
                    {"university": university, "source": source},
                )
                self.source_list.addItem(source_item)

        self.source_list.setCurrentRow(0)

    def on_source_selected(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)

        self.selected_university = data.get("university", "All")
        self.selected_source = data.get("source", "All")

        self.current_page = 1
        self.load_filtered_articles()

    def on_search_changed(self, text: str):
        self.search_text = text.strip()
        self.current_page = 1
        self.load_filtered_articles()

    def load_filtered_articles(self):
        self.articles = self.database.get_articles(
            university=self.selected_university,
            source=self.selected_source,
            search_text=self.search_text,
            limit=500,
        )

        self.render_articles()

    def create_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(14)

        title = QLabel("Sources")
        title.setObjectName("SidebarTitle")

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search articles...")
        self.search_input.textChanged.connect(self.on_search_changed)

        self.source_list = QListWidget()
        self.source_list.setObjectName("SourceList")
        self.source_list.itemClicked.connect(self.on_source_selected)

        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(self.search_input)
        sidebar_layout.addWidget(self.source_list)
        sidebar_layout.addStretch()

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

            #Sidebar {
                background-color: #FFFFFF;
                border: 1px solid #E6DDF3;
                border-radius: 22px;
            }

            #SidebarTitle {
                color: #171124;
                font-size: 18px;
                font-weight: 900;
            }

            #SearchInput {
                background-color: #F9F5FF;
                color: #171124;
                border: 1px solid #E9D5FF;
                border-radius: 10px;
                padding: 9px 12px;
                font-size: 13px;
            }

            #SearchInput:focus {
                border: 1px solid #A855F7;
            }

            #SourceList {
                background-color: transparent;
                border: none;
                outline: none;
            }

            #SourceList::item {
                color: #4B5563;
                padding: 10px 12px;
                border-radius: 10px;
            }

            #SourceList::item:hover {
                background-color: #F3E8FF;
                color: #171124;
            }

            #SourceList::item:selected {
                background-color: #A855F7;
                color: white;
                font-weight: 800;
            }

            #PaginationBar {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 16px;
            }

            #PaginationSummary {
                color: #64748b;
                font-size: 13px;
                font-weight: 500;
            }

            #PaginationButton,
            #PageButton {
                background-color: #f8fafc;
                color: #334155;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 7px 12px;
                font-weight: 600;
            }

            #PaginationButton:hover,
            #PageButton:hover {
                background-color: #eef2ff;
                color: #1e293b;
            }

            #PaginationButton:disabled {
                background-color: #f1f5f9;
                color: #94a3b8;
            }

            #PageButtonActive {
                background-color: #111827;
                color: #ffffff;
                border: 1px solid #111827;
                border-radius: 10px;
                padding: 7px 12px;
                font-weight: 700;
            }

            #PaginationDots {
                color: #94a3b8;
                padding-left: 4px;
                padding-right: 4px;
            }

            #PaginationSize {
                background-color: #f8fafc;
                color: #334155;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 6px 10px;
            }
            """
        )

        if hasattr(self, "article_container"):
            self.article_container.setStyleSheet("background-color: #F4F0FA;")

    def apply_dark_theme(self):
        self.setStyleSheet(
            """
            #Sidebar {
                background-color: #0B1220;
                border: 1px solid #1E293B;
                border-radius: 22px;
            }

            #SidebarTitle {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: 900;
            }

            #SearchInput {
                background-color: #111827;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 9px 12px;
                font-size: 13px;
            }

            #SearchInput:focus {
                border: 1px solid #C084FC;
            }

            #SourceList {
                background-color: transparent;
                border: none;
                outline: none;
            }

            #SourceList::item {
                color: #CBD5E1;
                padding: 10px 12px;
                border-radius: 10px;
            }

            #SourceList::item:hover {
                background-color: #1E293B;
                color: #FFFFFF;
            }

            #SourceList::item:selected {
                background-color: #C084FC;
                color: #080A14;
                font-weight: 800;
            }
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

        for feed in feeds:
            university_name = feed.get("name", "Unknown university")
            feed_url = feed.get("url", "")

            try:
                source_type = feed.get("type", "rss")

                if source_type == "scraper":
                    scraper_id = feed.get("scraper")
                    articles = run_scraper(scraper_id)
                else:
                    articles = fetch_feed(university_name, feed_url)

                self.database.save_articles(articles)

            except Exception as error:
                print(f"Could not fetch {university_name}: {error}")

        self.articles = self.database.get_articles()
        print("Articles loaded from DB:", len(self.articles))

        self.render_articles()

        self.update_source_list()
        self.load_filtered_articles()

    def load_cached_articles(self):
        self.update_source_list()
        self.current_page = 1
        self.load_filtered_articles()

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

        source = article.get("source", university)
        published = article.get("published", "Unknown date")

        meta = QLabel(f"{university}  •  {source}  •  {published}")
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
        dialog.setStyleSheet(
            self.get_theme_stylesheet(self.app_settings.get("theme", "light"))
        )

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
        stylesheet = self.get_theme_stylesheet(theme)
        self.setStyleSheet(stylesheet)

        if hasattr(self, "article_container"):
            bg = "#080A14" if theme == "dark" else "#F4F0FA"
            self.article_container.setStyleSheet(f"background-color: {bg};")

    def create_pagination_bar(self):
        self.pagination_bar = QFrame()
        self.pagination_bar.setObjectName("PaginationBar")

        pagination_layout = QHBoxLayout(self.pagination_bar)
        pagination_layout.setContentsMargins(12, 8, 12, 8)
        pagination_layout.setSpacing(8)

        self.page_summary_label = QLabel()
        self.page_summary_label.setObjectName("PaginationSummary")

        self.pagination_prev_button = QPushButton("‹ Previous")
        self.pagination_prev_button.setObjectName("PaginationButton")
        self.pagination_prev_button.clicked.connect(self.go_to_previous_page)

        self.page_buttons_layout = QHBoxLayout()
        self.page_buttons_layout.setSpacing(6)

        self.pagination_next_button = QPushButton("Next ›")
        self.pagination_next_button.setObjectName("PaginationButton")
        self.pagination_next_button.clicked.connect(self.go_to_next_page)

        self.page_size_combo = QComboBox()
        self.page_size_combo.setObjectName("PaginationSize")

        for size in [10, 12, 20, 30, 50]:
            self.page_size_combo.addItem(f"{size} / page", size)

        self.page_size_combo.setCurrentIndex(1)
        self.page_size_combo.currentIndexChanged.connect(self.on_page_size_changed)

        pagination_layout.addWidget(self.page_summary_label)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.pagination_prev_button)
        pagination_layout.addLayout(self.page_buttons_layout)
        pagination_layout.addWidget(self.pagination_next_button)
        pagination_layout.addSpacing(8)
        pagination_layout.addWidget(self.page_size_combo)

    def load_filtered_articles(self):
        self.total_articles = self.database.count_articles(
            university=self.selected_university,
            source=self.selected_source,
            search_text=self.search_text,
        )

        self.total_pages = max(
            1,
            (self.total_articles + self.page_size - 1) // self.page_size,
        )

        if self.current_page > self.total_pages:
            self.current_page = self.total_pages

        offset = (self.current_page - 1) * self.page_size

        self.articles = self.database.get_articles(
            university=self.selected_university,
            source=self.selected_source,
            search_text=self.search_text,
            limit=self.page_size,
            offset=offset,
        )

        self.render_articles()
        self.update_pagination_controls()

    def update_pagination_controls(self):
        self.clear_pagination_page_buttons()

        if self.total_articles == 0:
            self.pagination_bar.setVisible(False)
            return

        self.pagination_bar.setVisible(True)

        first_article = (self.current_page - 1) * self.page_size + 1
        last_article = min(
            self.current_page * self.page_size,
            self.total_articles,
        )

        self.page_summary_label.setText(
            f"Showing {first_article}-{last_article} of {self.total_articles}"
        )

        self.pagination_prev_button.setEnabled(self.current_page > 1)
        self.pagination_next_button.setEnabled(self.current_page < self.total_pages)

        for page in self.get_visible_page_numbers():
            if page == "...":
                label = QLabel("...")
                label.setObjectName("PaginationDots")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.page_buttons_layout.addWidget(label)
                continue

            button = QPushButton(str(page))

            if page == self.current_page:
                button.setObjectName("PageButtonActive")
                button.setEnabled(False)
            else:
                button.setObjectName("PageButton")
                button.clicked.connect(
                    lambda checked=False, selected_page=page: self.go_to_page(
                        selected_page
                    )
                )

            self.page_buttons_layout.addWidget(button)

    def get_visible_page_numbers(self) -> list:
        if self.total_pages <= 7:
            return list(range(1, self.total_pages + 1))

        pages = [1]

        start_page = max(2, self.current_page - 1)
        end_page = min(self.total_pages - 1, self.current_page + 1)

        if start_page > 2:
            pages.append("...")

        for page in range(start_page, end_page + 1):
            pages.append(page)

        if end_page < self.total_pages - 1:
            pages.append("...")

        pages.append(self.total_pages)

        return pages

    def clear_pagination_page_buttons(self):
        while self.page_buttons_layout.count():
            item = self.page_buttons_layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()

    def go_to_page(self, page: int):
        if page < 1 or page > self.total_pages:
            return

        if page == self.current_page:
            return

        self.current_page = page
        self.load_filtered_articles()
        self.scroll_area.verticalScrollBar().setValue(0)

    def go_to_previous_page(self):
        self.go_to_page(self.current_page - 1)

    def go_to_next_page(self):
        self.go_to_page(self.current_page + 1)

    def on_page_size_changed(self):
        self.page_size = self.page_size_combo.currentData()
        self.current_page = 1
        self.load_filtered_articles()
