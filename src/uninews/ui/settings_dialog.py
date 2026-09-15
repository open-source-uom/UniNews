"""Preferences dialog. Reads a settings dict, returns a new one."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from uninews import config
from uninews.library import PAGE_SIZES
from uninews.ui.theme import DARK, LIGHT


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)

        self.settings = dict(settings)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.theme = QComboBox()
        self.theme.addItem("Light", LIGHT)
        self.theme.addItem("Dark", DARK)
        self.theme.setCurrentIndex(self.theme.findData(settings.get("theme", LIGHT)))

        self.page_size = QComboBox()
        for size in PAGE_SIZES:
            self.page_size.addItem(f"{size} / page", size)
        self.page_size.setCurrentIndex(self.page_size.findData(settings.get("page_size", 12)))

        self.refresh_on_startup = QCheckBox("Refresh when the app opens")
        self.refresh_on_startup.setChecked(bool(settings.get("refresh_on_startup", True)))

        self.interval = QSpinBox()
        self.interval.setRange(0, 24 * 60)
        self.interval.setSingleStep(15)
        self.interval.setSpecialValueText("Off")
        self.interval.setSuffix(" min")
        self.interval.setValue(int(settings.get("refresh_interval_minutes", 0)))

        self.max_articles = QSpinBox()
        self.max_articles.setRange(50, 10000)
        self.max_articles.setSingleStep(50)
        self.max_articles.setValue(int(settings.get("max_cached_articles", 500)))

        form.addRow("Theme", self.theme)
        form.addRow("Articles per page", self.page_size)
        form.addRow("", self.refresh_on_startup)
        form.addRow("Auto-refresh every", self.interval)
        form.addRow("Keep at most", self.max_articles)

        note = QLabel(
            f"Auto-refresh runs at most every {config.MIN_REFRESH_INTERVAL_MINUTES} "
            "minutes, to avoid overloading university servers."
        )
        note.setObjectName("SettingsNote")
        note.setWordWrap(True)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        for button in buttons.buttons():
            button.setIcon(QIcon())          # drop the desktop theme's icons
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("SaveButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(buttons)

    def result_settings(self) -> dict:
        self.settings.update(
            theme=self.theme.currentData(),
            page_size=self.page_size.currentData(),
            refresh_on_startup=self.refresh_on_startup.isChecked(),
            refresh_interval_minutes=self.interval.value(),
            max_cached_articles=self.max_articles.value(),
        )
        return self.settings
