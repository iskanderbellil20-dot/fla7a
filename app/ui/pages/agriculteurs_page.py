from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AgriculteursPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titre = QLabel("Agriculteurs")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Gestion des agriculteurs et de leurs parcelles."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(titre)
        layout.addWidget(description)
        layout.addStretch()