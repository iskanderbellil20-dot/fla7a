from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.ressource_service import (
    archiver_ressource,
    lister_ressources,
    obtenir_ressource,
    restaurer_ressource,
)

from app.ui.dialogs.ressource_dialog import (
    RessourceDialog,
)


class RessourcesPage(QWidget):
    def __init__(self):
        super().__init__()

        self.ressources = []

        self.creer_interface()
        self.charger_ressources()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            28,
            25,
            28,
            25,
        )

        layout.setSpacing(15)

        titre = QLabel("Ressources d'eau")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Gestion des ressources d'eau "
            "et de leur disponibilité."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(titre)
        layout.addWidget(description)

        barre = QHBoxLayout()

        self.recherche_input = QLineEdit()
        self.recherche_input.setPlaceholderText(
            "Rechercher une ressource..."
        )

        self.recherche_input.textChanged.connect(
            self.appliquer_filtre
        )

        self.afficher_archivees = QCheckBox(
            "Afficher les ressources archivées"
        )

        self.afficher_archivees.stateChanged.connect(
            self.charger_ressources
        )

        ajouter_button = QPushButton(
            "+ Ajouter une ressource"
        )

        ajouter_button.setObjectName(
            "primaryButton"
        )

        ajouter_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        ajouter_button.clicked.connect(
            self.ajouter_ressource
        )

        barre.addWidget(
            self.recherche_input,
            stretch=1,
        )

        barre.addWidget(
            self.afficher_archivees
        )

        barre.addWidget(
            ajouter_button
        )

        layout.addLayout(barre)

        self.table = QTableWidget()

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels(
            [
                "Nom",
                "État",
                "Description",
                "Remarque",
                "Statut",
            ]
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setAlternatingRowColors(True)

        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.table.doubleClicked.connect(
            self.modifier_selection
        )

        layout.addWidget(self.table)

        actions = QHBoxLayout()

        modifier_button = QPushButton(
            "Modifier"
        )

        modifier_button.clicked.connect(
            self.modifier_selection
        )

        self.archive_button = QPushButton(
            "Archiver"
        )

        self.archive_button.clicked.connect(
            self.archiver_ou_restaurer
        )

        actualiser_button = QPushButton(
            "Actualiser"
        )

        actualiser_button.clicked.connect(
            self.charger_ressources
        )

        actions.addWidget(modifier_button)
        actions.addWidget(self.archive_button)
        actions.addWidget(actualiser_button)
        actions.addStretch()

        layout.addLayout(actions)

        self.table.itemSelectionChanged.connect(
            self.mettre_a_jour_actions
        )

        self.mettre_a_jour_actions()

    def charger_ressources(self):
        inclure_archivees = (
            self.afficher_archivees.isChecked()
        )

        self.ressources = lister_ressources(
            inclure_archivees=inclure_archivees
        )

        self.appliquer_filtre()

    def appliquer_filtre(self):
        terme = (
            self.recherche_input
            .text()
            .strip()
            .lower()
        )

        if not terme:
            ressources = self.ressources
        else:
            ressources = [
                r for r in self.ressources
                if terme in str(r[1]).lower()
                or terme in str(r[2]).lower()
                or terme in str(
                    r[3] or ""
                ).lower()
            ]

        self.remplir_tableau(ressources)

    def remplir_tableau(self, ressources):
        self.table.setRowCount(0)

        libelles_etats = {
            "DISPONIBLE": "Disponible",
            "EN_PANNE": "En panne",
            "MAINTENANCE": "Maintenance",
            "HORS_SERVICE": "Hors service",
        }

        for ressource in ressources:
            ligne = self.table.rowCount()
            self.table.insertRow(ligne)

            id_ressource = ressource[0]

            nom_item = QTableWidgetItem(
                ressource[1]
            )

            nom_item.setData(
                Qt.ItemDataRole.UserRole,
                id_ressource,
            )

            etat_item = QTableWidgetItem(
                libelles_etats.get(
                    ressource[2],
                    ressource[2],
                )
            )

            description_item = QTableWidgetItem(
                ressource[3] or ""
            )

            remarque_item = QTableWidgetItem(
                ressource[4] or ""
            )

            statut_item = QTableWidgetItem(
                "Actif"
                if ressource[5] == 1
                else "Archivé"
            )

            self.table.setItem(
                ligne,
                0,
                nom_item,
            )

            self.table.setItem(
                ligne,
                1,
                etat_item,
            )

            self.table.setItem(
                ligne,
                2,
                description_item,
            )

            self.table.setItem(
                ligne,
                3,
                remarque_item,
            )

            self.table.setItem(
                ligne,
                4,
                statut_item,
            )

        self.mettre_a_jour_actions()

    def obtenir_id_selectionne(self):
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

    def ajouter_ressource(self):
        dialog = RessourceDialog(
            parent=self
        )

        if dialog.exec():
            self.charger_ressources()

    def modifier_selection(self):
        ressource_id = (
            self.obtenir_id_selectionne()
        )

        if ressource_id is None:
            QMessageBox.information(
                self,
                "Sélection",
                "Sélectionnez une ressource "
                "à modifier.",
            )
            return

        ressource = obtenir_ressource(
            ressource_id
        )

        if ressource is None:
            QMessageBox.warning(
                self,
                "Erreur",
                "Cette ressource n'existe plus.",
            )
            self.charger_ressources()
            return

        dialog = RessourceDialog(
            parent=self,
            ressource=ressource,
        )

        if dialog.exec():
            self.charger_ressources()

    def archiver_ou_restaurer(self):
        ressource_id = (
            self.obtenir_id_selectionne()
        )

        if ressource_id is None:
            return

        ressource = obtenir_ressource(
            ressource_id
        )

        if ressource is None:
            return

        actif = ressource[5]

        try:
            if actif == 1:
                confirmation = QMessageBox.question(
                    self,
                    "Archiver la ressource",
                    (
                        f"Voulez-vous archiver "
                        f"« {ressource[1]} » ?"
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                )

                if (
                    confirmation
                    != QMessageBox.StandardButton.Yes
                ):
                    return

                archiver_ressource(
                    ressource_id
                )

            else:
                confirmation = QMessageBox.question(
                    self,
                    "Restaurer la ressource",
                    (
                        f"Voulez-vous restaurer "
                        f"« {ressource[1]} » ?"
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                )

                if (
                    confirmation
                    != QMessageBox.StandardButton.Yes
                ):
                    return

                restaurer_ressource(
                    ressource_id
                )

            self.charger_ressources()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                str(error),
            )

    def mettre_a_jour_actions(self):
        ressource_id = (
            self.obtenir_id_selectionne()
        )

        if ressource_id is None:
            self.archive_button.setEnabled(False)
            self.archive_button.setText(
                "Archiver"
            )
            return

        ressource = obtenir_ressource(
            ressource_id
        )

        if ressource is None:
            self.archive_button.setEnabled(False)
            return

        self.archive_button.setEnabled(True)

        if ressource[5] == 1:
            self.archive_button.setText(
                "Archiver"
            )
        else:
            self.archive_button.setText(
                "Restaurer"
            )