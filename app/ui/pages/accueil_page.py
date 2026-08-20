from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AccueilPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titre = QLabel("Accueil")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Gestion et organisation des tours d'eau"
        )
        description.setObjectName("pageDescription")

        layout.addWidget(titre)
        layout.addWidget(description)
        layout.addStretch()

        layout.setAlignment(Qt.AlignmentFlag.AlignTop)