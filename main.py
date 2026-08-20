import sys

from PySide6.QtWidgets import QApplication

from app.database.migrations import run_migrations
from app.ui.main_window import MainWindow
from app.ui.styles import APP_STYLE


def main():
    run_migrations()

    application = QApplication(sys.argv)

    application.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(application.exec())


if __name__ == "__main__":
    main()