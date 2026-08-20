from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.services.agriculteur_service import (
    obtenir_agriculteur,
)


class AgriculteurDetailsDialog(QDialog):
    def __init__(
        self,
        agriculteur_id,
        parent=None,
    ):
        super().__init__(parent)

        self.agriculteur_id = agriculteur_id

        self.setWindowTitle(
            "Fiche agriculteur"
        )

        self.resize(760, 520)

        self.creer_interface()
        self.charger_donnees()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        self.nom_label = QLabel()
        self.nom_label.setObjectName(
            "dialogTitle"
        )

        layout.addWidget(self.nom_label)

        informations_box = QGroupBox(
            "Informations personnelles"
        )

        informations_layout = QVBoxLayout(
            informations_box
        )

        self.cin_label = QLabel()
        self.telephone_label = QLabel()
        self.statut_label = QLabel()
        self.remarque_label = QLabel()

        informations_layout.addWidget(
            self.cin_label
        )

        informations_layout.addWidget(
            self.telephone_label
        )

        informations_layout.addWidget(
            self.statut_label
        )

        informations_layout.addWidget(
            self.remarque_label
        )

        layout.addWidget(informations_box)

        parcelles_box = QGroupBox(
            "Parcelles / Lots"
        )

        parcelles_layout = QVBoxLayout(
            parcelles_box
        )

        self.table = QTableWidget()

        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels(
            [
                "N° Lot",
                "Superficie",
                "Ressources autorisées",
                "Statut",
            ]
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()

        header.setStretchLastSection(True)

        parcelles_layout.addWidget(
            self.table
        )

        layout.addWidget(parcelles_box)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

    def charger_donnees(self):
        agriculteur = obtenir_agriculteur(
            self.agriculteur_id
        )

        if agriculteur is None:
            self.nom_label.setText(
                "Agriculteur introuvable"
            )
            return

        self.nom_label.setText(
            f"{agriculteur['prenom']} "
            f"{agriculteur['nom']}"
        )

        self.cin_label.setText(
            f"CIN : {agriculteur['cin']}"
        )

        self.telephone_label.setText(
            f"Téléphone : "
            f"{agriculteur['telephone']}"
        )

        self.statut_label.setText(
            "Statut : "
            + (
                "Actif"
                if agriculteur["actif"] == 1
                else "Archivé"
            )
        )

        self.remarque_label.setText(
            "Remarque : "
            + (
                agriculteur["remarque"]
                or "Aucune"
            )
        )

        parcelles = agriculteur[
            "parcelles"
        ]

        self.table.setRowCount(
            len(parcelles)
        )

        for ligne, parcelle in enumerate(
            parcelles
        ):
            ressources = ", ".join(
                ressource[1]
                for ressource
                in parcelle["ressources"]
            )

            self.table.setItem(
                ligne,
                0,
                QTableWidgetItem(
                    str(
                        parcelle[
                            "numero_lot"
                        ]
                    )
                ),
            )

            superficie = (
                f"{parcelle['superficie_m2']:,.0f}"
                .replace(",", " ")
                + " m²"
            )

            self.table.setItem(
                ligne,
                1,
                QTableWidgetItem(
                    superficie
                ),
            )

            self.table.setItem(
                ligne,
                2,
                QTableWidgetItem(
                    ressources
                ),
            )

            self.table.setItem(
                ligne,
                3,
                QTableWidgetItem(
                    "Actif"
                    if parcelle["actif"] == 1
                    else "Archivé"
                ),
            )

        self.table.resizeColumnsToContents()