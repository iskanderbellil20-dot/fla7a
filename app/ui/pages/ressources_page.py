from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class RessourcesPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titre = QLabel("Ressources d'eau")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Gestion des puits et de leur disponibilité."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(titre)
        layout.addWidget(description)
        layout.addStretch()