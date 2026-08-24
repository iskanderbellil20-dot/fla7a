from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.ui.dialogs.tour_details_dialog import (
    TourDetailsDialog,
)


class ToursImpactesDialog(QDialog):
    def __init__(
        self,
        tours,
        parent=None,
    ):
        super().__init__(parent)

        self.tours = tours

        self.setWindowTitle(
            "Tours d'eau concernés"
        )

        self.resize(
            850,
            520,
        )

        self.creer_interface()
        self.charger_tours()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        titre = QLabel(
            (
                f"{len(self.tours)} tour(s) "
                "d'eau concerné(s)"
            )
        )

        titre.setObjectName(
            "dialogTitle"
        )

        layout.addWidget(
            titre
        )

        message = QLabel(
            (
                "L'application ne modifie pas "
                "automatiquement ces tours. "
                "Le responsable décide pour "
                "chaque réservation."
            )
        )

        message.setWordWrap(
            True
        )

        layout.addWidget(
            message
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            7
        )

        self.table.setHorizontalHeaderLabels(
            [
                "Reçu",
                "Agriculteur",
                "Lot",
                "Ressource",
                "Début",
                "Fin",
                "Téléphone",
            ]
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.doubleClicked.connect(
            self.ouvrir_tour
        )

        layout.addWidget(
            self.table
        )

        actions = QHBoxLayout()

        ouvrir_button = QPushButton(
            "Examiner le tour"
        )

        ouvrir_button.setObjectName(
            "primaryButton"
        )

        ouvrir_button.clicked.connect(
            self.ouvrir_tour
        )

        fermer_button = QPushButton(
            "Fermer"
        )

        fermer_button.clicked.connect(
            self.accept
        )

        actions.addStretch()

        actions.addWidget(
            ouvrir_button
        )

        actions.addWidget(
            fermer_button
        )

        layout.addLayout(
            actions
        )

    def charger_tours(self):
        self.table.setRowCount(
            len(self.tours)
        )

        for ligne, tour in enumerate(
            self.tours
        ):
            agriculteur = (
                f"{tour['prenom']} "
                f"{tour['nom']}"
            )

            valeurs = [
                tour[
                    "numero_recu_formate"
                ],

                agriculteur,

                str(
                    tour[
                        "numero_lot"
                    ]
                ),

                tour[
                    "ressource_nom"
                ],

                tour[
                    "date_heure_debut"
                ],

                tour[
                    "date_heure_fin"
                ],

                tour[
                    "telephone"
                ],
            ]

            for colonne, valeur in enumerate(
                valeurs
            ):
                item = QTableWidgetItem(
                    str(
                        valeur
                        if valeur is not None
                        else ""
                    )
                )

                if colonne == 0:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        tour["tour_id"],
                    )

                self.table.setItem(
                    ligne,
                    colonne,
                    item,
                )

        self.table.resizeColumnsToContents()

    def obtenir_tour_id(self):
        ligne = self.table.currentRow()

        if ligne < 0:
            return None

        item = self.table.item(
            ligne,
            0,
        )

        if item is None:
            return None

        return item.data(
            Qt.ItemDataRole.UserRole
        )

    def ouvrir_tour(self):
        tour_id = (
            self.obtenir_tour_id()
        )

        if tour_id is None:
            return

        dialog = TourDetailsDialog(
            tour_id=tour_id,
            parent=self,
        )

        dialog.exec()