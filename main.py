import sys

from PySide6.QtWidgets import QApplication, QLabel


def main():
    app = QApplication(sys.argv)

    window = QLabel("Gestion des ressources d'eau")
    window.setWindowTitle("Gestion Eau")
    window.resize(500, 150)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()