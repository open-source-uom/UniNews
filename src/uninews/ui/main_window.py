"""The window. Owns the database and the fetch worker, and connects the widgets.

Nothing below this file touches the database or the network.
"""

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from uninews import config
from uninews.database import Database
from uninews.fetchers import load_fetchers
from uninews.library import Library
from uninews.ui.article_list import ArticleList
from uninews.ui.fetch_worker import FetchResult, FetchWorker
from uninews.ui.pagination import Pagination
from uninews.ui.settings_dialog import SettingsDialog
from uninews.ui.sidebar import Sidebar
from uninews.ui.theme import stylesheet


class UniNewsWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = config.load_settings()
        self.database = Database(config.DATABASE_FILE)
        self.library = Library(self.database, self.settings["page_size"])
        self.worker: FetchWorker | None = None
        self.last_results: list[FetchResult] = []

        self.setWindowTitle("UniNews")
        self.resize(1050, 720)
        self.build_ui()
        self.apply_theme()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.apply_refresh_timer()

        self.reload()

        if self.settings.get("refresh_on_startup", True):
            QTimer.singleShot(0, self.refresh)   # after the window is on screen

    # --- building ---------------------------------------------------------

    def build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        self.sidebar = Sidebar()
        self.sidebar.filter_changed.connect(self.on_filter_changed)
        self.sidebar.search_changed.connect(self.on_search_changed)

        self.article_list = ArticleList()
        self.article_list.article_clicked.connect(self.open_article)

        self.pagination = Pagination(self.library.page_size)
        self.pagination.page_changed.connect(self.on_page_changed)
        self.pagination.page_size_changed.connect(self.on_page_size_changed)

        articles_area = QWidget()
        articles_layout = QVBoxLayout(articles_area)
        articles_layout.setContentsMargins(0, 0, 0, 0)
        articles_layout.setSpacing(12)
        articles_layout.addWidget(self.article_list, stretch=1)
        articles_layout.addWidget(self.pagination)

        content = QHBoxLayout()
        content.setSpacing(20)
        content.addWidget(self.sidebar)
        content.addWidget(articles_area, stretch=1)

        layout.addWidget(self.build_header())
        layout.addLayout(content)

        self.setCentralWidget(root)
        self.statusBar()

    def build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("HeaderCard")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        titles = QVBoxLayout()
        titles.setSpacing(4)

        title = QLabel("UniNews")
        title.setObjectName("TitleLabel")

        subtitle = QLabel("University news in one clean place")
        subtitle.setObjectName("SubtitleLabel")

        titles.addWidget(title)
        titles.addWidget(subtitle)

        self.status_button = QPushButton("Sources")
        self.status_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.status_button.clicked.connect(self.show_source_status)

        self.settings_button = QPushButton("Settings")
        self.settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_button.clicked.connect(self.open_settings)

        self.refresh_button = QPushButton("Refresh news")
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.clicked.connect(self.refresh)

        layout.addLayout(titles)
        layout.addStretch()
        layout.addWidget(self.status_button)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.refresh_button)

        return header

    # --- showing articles -------------------------------------------------

    def reload(self) -> None:
        """Redraw the list, sidebar and pagination from the database."""
        page = self.library.current_page()

        self.sidebar.set_sources(self.database.get_source_tree())
        self.article_list.show_articles(page.articles)
        self.pagination.update(page, self.library.page_buttons())

        if not page.articles and self.library.filter.is_empty and not self.last_results:
            self.article_list.show_message(
                "No articles yet.\nPress “Refresh news” to fetch them."
            )

    def on_filter_changed(self, category: str, publisher: str, source: str) -> None:
        self.library.set_filter(
            category=category or None,
            publisher=publisher or None,
            source=source or None,
        )
        self.reload()

    def on_search_changed(self, text: str) -> None:
        self.library.set_filter(search=text)
        self.reload()

    def on_page_changed(self, number: int) -> None:
        self.library.go_to_page(number)
        self.reload()
        self.article_list.scroll_to_top()

    def on_page_size_changed(self, size: int) -> None:
        self.library.set_page_size(size)
        self.settings["page_size"] = size
        config.save_settings(self.settings)
        self.reload()

    def open_article(self, link: str) -> None:
        QDesktopServices.openUrl(QUrl(link))

    # --- fetching ---------------------------------------------------------

    def refresh(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return

        try:
            fetchers = load_fetchers(config.PUBLISHERS_DIR)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Could not load sources", str(error))
            return

        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Refreshing...")

        self.worker = FetchWorker(fetchers, self)
        self.worker.progress.connect(self.on_fetch_progress)
        self.worker.finished_fetching.connect(self.on_fetch_finished)
        self.worker.start()

    def on_fetch_progress(self, done: int, total: int, label: str) -> None:
        self.statusBar().showMessage(f"Fetching {done}/{total}: {label}")

    def on_fetch_finished(self, results: list[FetchResult]) -> None:
        self.last_results = results

        new_articles = []

        for result in results:
            new_articles.extend(self.database.save_articles(result.articles))

        removed = self.database.trim(int(self.settings["max_cached_articles"]))

        self.finish_refresh(results, len(new_articles), removed)

    def finish_refresh(self, results, new_count: int, removed: int) -> None:
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Refresh news")

        failed = [result for result in results if not result.ok]
        message = f"{new_count} new article{'s' if new_count != 1 else ''}"

        if removed:
            message += f", {removed} old removed"

        if failed:
            message += f" — {len(failed)} source{'s' if len(failed) > 1 else ''} failed"

        self.statusBar().showMessage(message, 10000)
        self.reload()

    def show_source_status(self) -> None:
        """What each source did on the last refresh."""
        if not self.last_results:
            QMessageBox.information(
                self, "Sources", "No refresh yet in this session."
            )
            return

        working = [result for result in self.last_results if result.ok]
        failed = [result for result in self.last_results if not result.ok]

        lines = [f"{len(working)} of {len(self.last_results)} sources worked."]

        if failed:
            lines.append("\nFailed:")
            lines += [
                f"  • {result.fetcher.publisher} / {result.fetcher.label}: {result.error}"
                for result in failed
            ]

        QMessageBox.information(self, "Sources", "\n".join(lines))

    # --- settings ---------------------------------------------------------

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)

        if dialog.exec():
            self.settings = dialog.result_settings()
            config.save_settings(self.settings)

            self.library.set_page_size(self.settings["page_size"])
            self.apply_theme()
            self.apply_refresh_timer()
            self.database.trim(int(self.settings["max_cached_articles"]))
            self.reload()

            self.statusBar().showMessage("Settings saved.", 5000)

    def apply_theme(self) -> None:
        self.setStyleSheet(stylesheet(self.settings.get("theme", "light")))

    def apply_refresh_timer(self) -> None:
        self.refresh_timer.stop()
        interval = config.refresh_interval_ms(self.settings)

        if interval:
            self.refresh_timer.start(interval)

    # --- shutdown ---------------------------------------------------------

    def closeEvent(self, event) -> None:
        """Wait for the fetch thread before quitting.

        Destroying a running QThread aborts the process, and a request that is
        already in flight can take up to the HTTP timeout to return. So hide
        the window straight away and quit once the thread has finished.
        """
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.finished.connect(self.quit_now)
            self.hide()
            event.ignore()
            return

        self.quit_now()
        super().closeEvent(event)

    def quit_now(self) -> None:
        self.database.close()
        QApplication.quit()
