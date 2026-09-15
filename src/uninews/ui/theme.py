"""All colours and stylesheets. Nothing here knows about articles or sources."""

from dataclasses import dataclass
from pathlib import Path

from uninews import config

LIGHT = "light"
DARK = "dark"


@dataclass(frozen=True)
class Palette:
    background: str
    panel: str
    panel_alt: str
    border: str
    text: str
    muted: str
    accent: str
    accent_hover: str
    input_background: str
    card: str
    card_hover: str
    image_background: str


PALETTES = {
    LIGHT: Palette(
        background="#F4F0FA",
        panel="#FFFFFF",
        panel_alt="#FFFFFF",
        border="#E6DDF3",
        text="#171124",
        muted="#4B5563",
        accent="#A855F7",
        accent_hover="#9333EA",
        input_background="#F9F5FF",
        card="#FFFFFF",
        card_hover="#FBF7FF",
        image_background="#F3E8FF",
    ),
    DARK: Palette(
        background="#080A14",
        panel="#111827",
        panel_alt="#0B1220",
        border="#2A3144",
        text="#F8FAFC",
        muted="#CBD5E1",
        accent="#C084FC",
        accent_hover="#E879F9",
        input_background="#111827",
        card="#111827",
        card_hover="#161F33",
        image_background="#1F2937",
    ),
}

FONT_FAMILY = '"Noto Sans", "Inter", "Arial"'


def palette(theme: str) -> Palette:
    return PALETTES.get(theme, PALETTES[LIGHT])


ARROWS = {
    "down": "M1 1 L5 5.5 L9 1",
    "up": "M1 6 L5 1.5 L9 6",
}


def arrow_file(direction: str, color: str) -> Path:
    """Write (once) a small chevron SVG and return its path.

    Qt stylesheets can only point at image files, so the arrows for combo
    boxes and spin boxes are generated instead of shipped as assets.
    """
    directory = config.CACHE_DIR / "arrows"
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"{direction}-{color.lstrip('#')}.svg"

    if not path.exists():
        path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="7" '
            'viewBox="0 0 10 7">'
            f'<path d="{ARROWS[direction]}" fill="none" stroke="{color}" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
            "</svg>",
            encoding="utf-8",
        )

    return path


def stylesheet(theme: str) -> str:
    """The whole app's CSS. Set it once on the window; children inherit it."""
    p = palette(theme)

    down = arrow_file("down", p.muted)
    up = arrow_file("up", p.muted)
    down_accent = arrow_file("down", p.accent)
    up_accent = arrow_file("up", p.accent)

    return f"""
    QMainWindow, QDialog {{
        background-color: {p.background};
    }}

    QWidget {{
        font-family: {FONT_FAMILY};
        color: {p.text};
    }}

    #HeaderCard, #Sidebar {{
        background-color: {p.panel};
        border: 1px solid {p.border};
        border-radius: 24px;
    }}

    #TitleLabel {{
        color: {p.text};
        font-size: 34px;
        font-weight: 900;
        letter-spacing: -1px;
    }}

    #SubtitleLabel {{
        color: {p.accent};
        font-size: 14px;
        font-weight: 600;
    }}

    QPushButton {{
        background-color: {p.panel_alt};
        color: {p.text};
        border: 1px solid {p.border};
        padding: 10px 18px;
        border-radius: 11px;
        font-size: 13px;
        font-weight: 700;
    }}

    QPushButton:hover {{
        background-color: {p.card_hover};
        border: 1px solid {p.accent};
    }}

    #RefreshButton, #SaveButton {{
        background-color: {p.accent};
        color: white;
        border: none;
    }}

    #RefreshButton:hover, #SaveButton:hover {{
        background-color: {p.accent_hover};
    }}

    #RefreshButton:disabled {{
        background-color: {p.muted};
        color: {p.panel};
    }}

    QLineEdit, QComboBox, QSpinBox {{
        background-color: {p.input_background};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 10px;
        padding: 8px 10px;
        font-size: 13px;
    }}

    QComboBox, QSpinBox {{
        padding-right: 30px;
    }}

    QComboBox:hover, QSpinBox:hover {{
        border: 1px solid {p.accent};
    }}

    QLineEdit:focus {{
        border: 1px solid {p.accent};
    }}

    QCheckBox {{
        color: {p.text};
        spacing: 10px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {p.border};
        border-radius: 5px;
        background-color: {p.input_background};
    }}

    QCheckBox::indicator:hover {{
        border: 1px solid {p.accent};
    }}

    QCheckBox::indicator:checked {{
        background-color: {p.accent};
        border: 1px solid {p.accent};
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 26px;
        border: none;
        background: transparent;
    }}

    QComboBox::down-arrow {{
        image: url({down});
        width: 10px;
        height: 7px;
        margin-right: 8px;
    }}

    QComboBox::down-arrow:on {{
        image: url({down_accent});
    }}

    QComboBox QAbstractItemView {{
        background-color: {p.panel};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 10px;
        selection-background-color: {p.accent};
        selection-color: white;
        padding: 4px;
        outline: none;
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        subcontrol-origin: border;
        width: 26px;
        height: 16px;
        border: none;
        background: transparent;
    }}

    QSpinBox::up-button {{
        subcontrol-position: top right;
        margin: 5px 6px 0px 0px;
    }}

    QSpinBox::down-button {{
        subcontrol-position: bottom right;
        margin: 0px 6px 5px 0px;
    }}

    QSpinBox::up-arrow {{
        image: url({up});
        width: 10px;
        height: 7px;
    }}

    QSpinBox::down-arrow {{
        image: url({down});
        width: 10px;
        height: 7px;
    }}

    QSpinBox::up-arrow:hover {{
        image: url({up_accent});
    }}

    QSpinBox::down-arrow:hover {{
        image: url({down_accent});
    }}

    QDialogButtonBox QPushButton {{
        min-width: 90px;
    }}

    #SettingsNote {{
        color: {p.muted};
        font-size: 12px;
    }}

    QScrollArea, QScrollArea > QWidget > QWidget, #ArticleContainer {{
        background-color: {p.background};
        border: none;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 4px;
    }}

    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
        background: {p.border};
        border-radius: 5px;
        min-width: 24px;
        min-height: 24px;
    }}

    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
        background: {p.accent};
    }}

    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0px;
        height: 0px;
    }}

    QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
    }}

    #ArticleCard {{
        background-color: {p.card};
        border: 1px solid {p.border};
        border-radius: 24px;
    }}

    #ArticleCard:hover {{
        background-color: {p.card_hover};
        border: 1px solid {p.accent};
    }}

    #ArticleImage {{
        background-color: {p.image_background};
        border: 1px solid {p.border};
        border-radius: 18px;
        color: {p.accent};
        font-size: 24px;
        font-weight: 900;
    }}

    #ArticleTitle {{
        color: {p.text};
        font-size: 17px;
        font-weight: 850;
    }}

    #ArticleMeta, #OpenArticleLabel {{
        color: {p.accent};
        font-size: 12px;
        font-weight: 750;
    }}

    #ArticleSummary {{
        color: {p.muted};
        font-size: 13px;
    }}

    #StatusLabel {{
        color: {p.muted};
        font-size: 16px;
        padding: 60px;
    }}

    #SidebarTitle {{
        color: {p.text};
        font-size: 18px;
        font-weight: 900;
    }}

    #SourceList {{
        background-color: transparent;
        border: none;
        outline: none;
    }}

    #SourceList::item {{
        color: {p.muted};
        padding: 10px 12px;
        border-radius: 10px;
    }}

    #SourceList::item:hover {{
        background-color: {p.card_hover};
        color: {p.text};
    }}

    #SourceList::item:selected {{
        background-color: {p.accent};
        color: white;
        font-weight: 800;
    }}

    #PaginationBar {{
        background-color: {p.panel};
        border: 1px solid {p.border};
        border-radius: 18px;
    }}

    #PaginationSummary {{
        color: {p.muted};
        font-size: 13px;
        font-weight: 650;
    }}

    #PaginationButton, #PageButton {{
        background-color: {p.panel_alt};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 11px;
        padding: 8px 14px;
        font-size: 13px;
        font-weight: 750;
    }}

    #PaginationButton:hover, #PageButton:hover {{
        background-color: {p.card_hover};
        border: 1px solid {p.accent};
    }}

    #PaginationButton:disabled {{
        background-color: {p.panel_alt};
        color: {p.muted};
        border: 1px solid {p.border};
    }}

    #PageButtonActive {{
        background-color: {p.accent};
        color: white;
        border: none;
        border-radius: 11px;
        padding: 8px 14px;
        font-size: 13px;
        font-weight: 850;
    }}

    #PaginationDots {{
        color: {p.muted};
        font-size: 13px;
        font-weight: 700;
        padding: 0px 4px;
    }}

    #PaginationSize {{
        background-color: {p.panel_alt};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 11px;
        padding: 8px 30px 8px 12px;
        font-size: 13px;
        font-weight: 750;
    }}

    #PaginationSize:hover {{
        background-color: {p.card_hover};
        border: 1px solid {p.accent};
    }}

    #PaginationSize QAbstractItemView {{
        background-color: {p.panel};
        color: {p.text};
        border: 1px solid {p.border};
        border-radius: 10px;
        selection-background-color: {p.accent};
        selection-color: white;
        padding: 4px;
        outline: none;
    }}
    """
