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

from uninews import config, i18n
from uninews.i18n import tr
from uninews.library import PAGE_SIZES
from uninews.ui.theme import DARK, LIGHT


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, universities: list[str] | None = None, parent=None):
        super().__init__(parent)

        self.settings = dict(settings)
        self.setWindowTitle(tr("settings.title"))
        self.setMinimumWidth(420)

        self.language = combo(
            [
                (tr("settings.language_system"), i18n.SYSTEM),
                *((name, code) for code, name in i18n.LANGUAGES.items()),
            ],
            settings.get("language", i18n.SYSTEM),
        )
        self.theme = combo(
            [(tr("settings.theme_light"), LIGHT), (tr("settings.theme_dark"), DARK)],
            settings.get("theme", LIGHT),
        )
        self.page_size = combo(
            [(tr("pagination.per_page", size=size), size) for size in PAGE_SIZES],
            settings.get("page_size", 12),
        )
        self.home_university = combo(
            [
                (tr("settings.open_with_profile"), ""),
                (tr("sidebar.all"), config.HOME_UNIVERSITY_ALL),
                *((name, name) for name in universities or []),
            ],
            settings.get("home_university", ""),
        )

        self.refresh_on_startup = QCheckBox(tr("settings.refresh_on_startup"))
        self.refresh_on_startup.setChecked(bool(settings.get("refresh_on_startup", True)))

        self.interval = QSpinBox()
        self.interval.setRange(0, 24 * 60)
        self.interval.setSingleStep(15)
        self.interval.setSpecialValueText(tr("settings.interval_off"))
        self.interval.setSuffix(tr("settings.minutes_suffix"))
        self.interval.setValue(int(settings.get("refresh_interval_minutes", 0)))

        self.max_articles = QSpinBox()
        self.max_articles.setRange(50, 10000)
        self.max_articles.setSingleStep(50)
        self.max_articles.setValue(int(settings.get("max_cached_articles", 500)))

        form = QFormLayout()
        form.setSpacing(10)
        form.addRow(tr("settings.language"), self.language)
        form.addRow(tr("settings.theme"), self.theme)
        form.addRow(tr("settings.open_with"), self.home_university)
        form.addRow(tr("settings.per_page"), self.page_size)
        form.addRow("", self.refresh_on_startup)
        form.addRow(tr("settings.interval"), self.interval)
        form.addRow(tr("settings.keep_at_most"), self.max_articles)

        note = QLabel(tr("settings.note", minutes=config.MIN_REFRESH_INTERVAL_MINUTES))
        note.setObjectName("SettingsNote")
        note.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(note)
        layout.addWidget(self.build_buttons())

    def build_buttons(self) -> QDialogButtonBox:
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        for button in buttons.buttons():
            button.setIcon(QIcon())          # drop the desktop theme's icons
            button.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set explicitly: Qt's own labels stay English without a qtbase translation.
        save = buttons.button(QDialogButtonBox.StandardButton.Save)
        save.setObjectName("SaveButton")
        save.setText(tr("settings.save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("settings.cancel"))

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        return buttons

    def result_settings(self) -> dict:
        self.settings.update(
            language=self.language.currentData(),
            theme=self.theme.currentData(),
            page_size=self.page_size.currentData(),
            refresh_on_startup=self.refresh_on_startup.isChecked(),
            refresh_interval_minutes=self.interval.value(),
            max_cached_articles=self.max_articles.value(),
            home_university=self.home_university.currentData(),
        )
        return self.settings


def combo(items, current) -> QComboBox:
    """A combo box of (text, value) pairs, with current selected (or the first item)."""
    box = QComboBox()

    for text, value in items:
        box.addItem(text, value)

    box.setCurrentIndex(max(0, box.findData(current)))
    return box
