"""UniNews: university news in one place."""

import sys

from PyQt6.QtWidgets import QApplication

from uninews.ui.main_window import UniNewsWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("UniNews")

    window = UniNewsWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
