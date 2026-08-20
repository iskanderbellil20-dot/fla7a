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
from app.ui.dialogs.agriculteur_dialog import (
    AgriculteurDialog,
)
from app.services.agriculteur_service import (
    archiver_agriculteur,
    lister_agriculteurs_avec_resume,
    obtenir_agriculteur,
    rechercher_agriculteurs,
    restaurer_agriculteur,
)

from app.ui.dialogs.agriculteur_details_dialog import (
    AgriculteurDetailsDialog,
)


class AgriculteursPage(QWidget):

    def modifier_agriculteur_selectionne(self):
        agriculteur_id = (
            self.obtenir_id_selectionne()
        )

        if agriculteur_id is None:
            QMessageBox.information(
                self,
                "Sélection",
                "Sélectionnez un agriculteur.",
            )
            return

        agriculteur = obtenir_agriculteur(
            agriculteur_id
        )

        if agriculteur is None:
            return

        if agriculteur["actif"] == 0:
            QMessageBox.information(
                self,
                "Agriculteur archivé",
                (
                    "Restaurez l'agriculteur "
                    "avant de le modifier."
                ),
            )
            return

        dialog = AgriculteurDialog(
            parent=self,
            agriculteur_id=agriculteur_id,
        )

        if dialog.exec():
            self.charger_agriculteurs()

    def __init__(self):
        super().__init__()

        self.agriculteurs = []

        self.creer_interface()
        self.charger_agriculteurs()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            28,
            25,
            28,
            25,
        )

        layout.setSpacing(15)

        titre = QLabel("Agriculteurs")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Gestion des agriculteurs, "
            "de leurs parcelles et des "
            "ressources autorisées."
        )

        description.setObjectName(
            "pageDescription"
        )

        layout.addWidget(titre)
        layout.addWidget(description)

        barre = QHBoxLayout()

        self.recherche_input = QLineEdit()

        self.recherche_input.setPlaceholderText(
            "Rechercher par CIN, nom, "
            "prénom ou numéro de lot..."
        )

        self.recherche_input.textChanged.connect(
            self.appliquer_recherche
        )

        self.afficher_archives = QCheckBox(
            "Afficher les agriculteurs archivés"
        )

        self.afficher_archives.stateChanged.connect(
            self.charger_agriculteurs
        )

        self.ajouter_button = QPushButton(
            "+ Ajouter un agriculteur"
        )

        self.ajouter_button.setObjectName(
            "primaryButton"
        )

        # On connectera ce bouton à l'étape suivante.
        self.ajouter_button.clicked.connect(
            self.ajouter_agriculteur
        )

        barre.addWidget(
            self.recherche_input,
            stretch=1,
        )

        barre.addWidget(
            self.afficher_archives
        )

        barre.addWidget(
            self.ajouter_button
        )

        layout.addLayout(barre)

        self.table = QTableWidget()

        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels(
            [
                "Nom",
                "Prénom",
                "CIN",
                "Téléphone",
                "Parcelles",
                "Statut",
                "",
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
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        for colonne in range(2, 7):
            header.setSectionResizeMode(
                colonne,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        self.table.doubleClicked.connect(
            self.ouvrir_fiche
        )

        layout.addWidget(self.table)

        actions = QHBoxLayout()

        fiche_button = QPushButton(
            "Voir la fiche"
        )
        modifier_button = QPushButton(
            "Modifier"
        )

        modifier_button.clicked.connect(
            self.modifier_agriculteur_selectionne
        )

        fiche_button.clicked.connect(
            self.ouvrir_fiche
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
            self.charger_agriculteurs
        )
        
        actions.addWidget(modifier_button)
        actions.addWidget(fiche_button)
        actions.addWidget(self.archive_button)
        actions.addWidget(actualiser_button)
        actions.addStretch()

        layout.addLayout(actions)

        self.table.itemSelectionChanged.connect(
            self.mettre_a_jour_actions
        )

        self.mettre_a_jour_actions()

    def charger_agriculteurs(self):
        inclure_archives = (
            self.afficher_archives.isChecked()
        )

        self.agriculteurs = (
            lister_agriculteurs_avec_resume(
                inclure_archives
            )
        )

        self.appliquer_recherche()

    def appliquer_recherche(self):
        terme = (
            self.recherche_input
            .text()
            .strip()
        )

        if not terme:
            self.remplir_tableau(
                self.agriculteurs
            )
            return

        resultats = rechercher_agriculteurs(
            terme
        )

        ids = {
            resultat[0]
            for resultat in resultats
        }

        filtres = [
            agriculteur
            for agriculteur
            in self.agriculteurs
            if agriculteur[0] in ids
        ]

        self.remplir_tableau(
            filtres
        )

    def remplir_tableau(
        self,
        agriculteurs,
    ):
        self.table.setRowCount(0)

        for agriculteur in agriculteurs:
            ligne = self.table.rowCount()
            self.table.insertRow(ligne)

            id_agriculteur = agriculteur[0]

            nom_item = QTableWidgetItem(
                agriculteur[1]
            )

            nom_item.setData(
                Qt.ItemDataRole.UserRole,
                id_agriculteur,
            )

            valeurs = [
                nom_item,
                QTableWidgetItem(
                    agriculteur[2]
                ),
                QTableWidgetItem(
                    agriculteur[3]
                ),
                QTableWidgetItem(
                    agriculteur[4]
                ),
                QTableWidgetItem(
                    str(agriculteur[6])
                ),
                QTableWidgetItem(
                    "Actif"
                    if agriculteur[5] == 1
                    else "Archivé"
                ),
                QTableWidgetItem(""),
            ]

            for colonne, item in enumerate(
                valeurs
            ):
                self.table.setItem(
                    ligne,
                    colonne,
                    item,
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

    def ouvrir_fiche(self):
        agriculteur_id = (
            self.obtenir_id_selectionne()
        )

        if agriculteur_id is None:
            QMessageBox.information(
                self,
                "Sélection",
                "Sélectionnez un agriculteur.",
            )
            return

        dialog = AgriculteurDetailsDialog(
            agriculteur_id,
            self,
        )

        dialog.exec()

    def archiver_ou_restaurer(self):
        agriculteur_id = (
            self.obtenir_id_selectionne()
        )

        if agriculteur_id is None:
            return

        agriculteur = obtenir_agriculteur(
            agriculteur_id
        )

        if agriculteur is None:
            return

        try:
            if agriculteur["actif"] == 1:
                confirmation = QMessageBox.question(
                    self,
                    "Archiver",
                    (
                        "Archiver "
                        f"{agriculteur['prenom']} "
                        f"{agriculteur['nom']} ?"
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                )

                if (
                    confirmation
                    != QMessageBox.StandardButton.Yes
                ):
                    return

                archiver_agriculteur(
                    agriculteur_id
                )

            else:
                confirmation = QMessageBox.question(
                    self,
                    "Restaurer",
                    (
                        "Restaurer "
                        f"{agriculteur['prenom']} "
                        f"{agriculteur['nom']} ?"
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                )

                if (
                    confirmation
                    != QMessageBox.StandardButton.Yes
                ):
                    return

                restaurer_agriculteur(
                    agriculteur_id
                )

            self.charger_agriculteurs()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                str(error),
            )

    def mettre_a_jour_actions(self):
        agriculteur_id = (
            self.obtenir_id_selectionne()
        )

        if agriculteur_id is None:
            self.archive_button.setEnabled(
                False
            )
            self.archive_button.setText(
                "Archiver"
            )
            return

        agriculteur = obtenir_agriculteur(
            agriculteur_id
        )

        if agriculteur is None:
            self.archive_button.setEnabled(
                False
            )
            return

        self.archive_button.setEnabled(True)

        if agriculteur["actif"] == 1:
            self.archive_button.setText(
                "Archiver"
            )
        else:
            self.archive_button.setText(
                "Restaurer"
            )
            
    def ajouter_agriculteur(self):
        dialog = AgriculteurDialog(
            parent=self
        )

        if dialog.exec():
            self.charger_agriculteurs()
    