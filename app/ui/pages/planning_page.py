from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlanningPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titre = QLabel("Planning")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Planning des tours d'eau par ressource."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(titre)
        layout.addWidget(description)
        layout.addStretch()