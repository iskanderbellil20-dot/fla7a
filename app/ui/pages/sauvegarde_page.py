from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SauvegardePage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titre = QLabel("Sauvegarde")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Sauvegarde et restauration des données."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(titre)
        layout.addWidget(description)
        layout.addStretch()