"""UniNews: university news in one place."""

import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from uninews import config, i18n
from uninews.ui.main_window import UniNewsWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("UniNews")
    app.setDesktopFileName("uninews")          # Wayland matches this to uninews.desktop
    app.setWindowIcon(QIcon(str(config.ICON_FILE)))

    i18n.set_language(config.load_settings().get("language"))

    window = UniNewsWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
