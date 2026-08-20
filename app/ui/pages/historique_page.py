from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class HistoriquePage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titre = QLabel("Historique")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Consultation des tours d'eau et des modifications."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(titre)
        layout.addWidget(description)
        layout.addStretch()