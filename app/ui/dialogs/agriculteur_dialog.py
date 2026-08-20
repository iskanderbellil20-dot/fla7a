from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from app.services.agriculteur_service import (
    archiver_parcelle,
    creer_agriculteur,
    modifier_agriculteur_complet,
    obtenir_agriculteur,
    restaurer_parcelle,
)

from app.ui.dialogs.parcelle_dialog import (
    ParcelleDialog,
)
from app.ui.dialogs.operation_parcelle_dialog import (
    OperationParcelleDialog,
)


class AgriculteurDialog(QDialog):
    def __init__(
        self,
        parent=None,
        agriculteur_id=None,
    ):
        super().__init__(parent)

        self.agriculteur_id = agriculteur_id
        self.agriculteur = None

        # Parcelles ajoutées uniquement dans le formulaire.
        self.nouvelles_parcelles = []
        self.parcelles_modifiees = {}

        if agriculteur_id is None:
            self.setWindowTitle(
                "Ajouter un agriculteur"
            )
        else:
            self.setWindowTitle(
                "Modifier l'agriculteur"
            )

        self.resize(900, 700)
        self.setMinimumSize(780, 600)

        self.creer_interface()
        self.charger_agriculteur()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        titre = QLabel(
            "Nouvel agriculteur"
            if self.agriculteur_id is None
            else "Modifier l'agriculteur"
        )

        titre.setObjectName(
            "dialogTitle"
        )

        layout.addWidget(titre)

        informations_box = QGroupBox(
            "Informations personnelles"
        )

        formulaire = QFormLayout(
            informations_box
        )

        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()

        self.cin_input = QLineEdit()
        self.cin_input.setMaxLength(8)
        self.cin_input.setPlaceholderText(
            "8 chiffres"
        )

        self.telephone_input = QLineEdit()

        self.remarque_input = QTextEdit()
        self.remarque_input.setMaximumHeight(
            70
        )

        formulaire.addRow(
            "Nom * :",
            self.nom_input,
        )

        formulaire.addRow(
            "Prénom * :",
            self.prenom_input,
        )

        formulaire.addRow(
            "CIN * :",
            self.cin_input,
        )

        formulaire.addRow(
            "Téléphone * :",
            self.telephone_input,
        )

        formulaire.addRow(
            "Remarque :",
            self.remarque_input,
        )

        layout.addWidget(
            informations_box
        )

        parcelles_box = QGroupBox(
            "Parcelles / Lots"
        )

        parcelles_layout = QVBoxLayout(
            parcelles_box
        )

        barre_parcelles = QHBoxLayout()

        ajouter_parcelle_button = QPushButton(
            "+ Ajouter une parcelle"
        )

        ajouter_parcelle_button.setObjectName(
            "primaryButton"
        )

        ajouter_parcelle_button.clicked.connect(
            self.ajouter_parcelle_formulaire
        )

        modifier_parcelle_button = QPushButton(
            "Modifier la parcelle"
        )

        modifier_parcelle_button.clicked.connect(
            self.modifier_parcelle_selectionnee
        )

        self.archive_parcelle_button = QPushButton(
            "Archiver la parcelle"
        )
        self.transferer_button = QPushButton(
            "Transférer"
        )

        self.transferer_button.clicked.connect(
            self.transferer_parcelle_selectionnee
        )

        self.diviser_button = QPushButton(
            "Diviser / céder"
        )

        self.diviser_button.clicked.connect(
            self.diviser_parcelle_selectionnee
        )
        self.archive_parcelle_button.clicked.connect(
            self.archiver_ou_restaurer_parcelle
        )

        barre_parcelles.addWidget(
            ajouter_parcelle_button
        )

        barre_parcelles.addWidget(
            modifier_parcelle_button
        )

        barre_parcelles.addWidget(
            self.archive_parcelle_button
        )
        barre_parcelles.addWidget(
            self.transferer_button
        )

        barre_parcelles.addWidget(
            self.diviser_button
        )

        barre_parcelles.addStretch()

        parcelles_layout.addLayout(
            barre_parcelles
        )

        self.table_parcelles = QTableWidget()

        self.table_parcelles.setColumnCount(4)

        self.table_parcelles.setHorizontalHeaderLabels(
            [
                "N° Lot",
                "Superficie",
                "Ressources autorisées",
                "Statut",
            ]
        )

        self.table_parcelles.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table_parcelles.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table_parcelles.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table_parcelles.verticalHeader().setVisible(
            False
        )

        header = (
            self.table_parcelles
            .horizontalHeader()
        )

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
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.table_parcelles.doubleClicked.connect(
            self.modifier_parcelle_selectionnee
        )

        self.table_parcelles.itemSelectionChanged.connect(
            self.mettre_a_jour_action_parcelle
        )

        parcelles_layout.addWidget(
            self.table_parcelles
        )

        layout.addWidget(
            parcelles_box,
            stretch=1,
        )

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.accepted.connect(
            self.enregistrer
        )

        self.buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(self.buttons)

    def charger_agriculteur(self):
        if self.agriculteur_id is None:
            self.actualiser_parcelles()
            return

        self.agriculteur = obtenir_agriculteur(
            self.agriculteur_id
        )

        if self.agriculteur is None:
            QMessageBox.critical(
                self,
                "Erreur",
                "Agriculteur introuvable.",
            )
            self.reject()
            return

        self.nom_input.setText(
            self.agriculteur["nom"]
        )

        self.prenom_input.setText(
            self.agriculteur["prenom"]
        )

        self.cin_input.setText(
            self.agriculteur["cin"]
        )

        self.telephone_input.setText(
            self.agriculteur["telephone"]
        )

        self.remarque_input.setPlainText(
            self.agriculteur["remarque"]
            or ""
        )

        self.actualiser_parcelles()

    def obtenir_parcelles_affichees(self):
        parcelles = []

        if self.agriculteur:
            for parcelle in self.agriculteur[
                "parcelles"
            ]:
                parcelle_id = parcelle["id"]

                # Si elle a été modifiée dans
                # le formulaire, afficher la version
                # temporaire et non celle de SQLite.
                if (
                    parcelle_id
                    in self.parcelles_modifiees
                ):
                    parcelles.append(
                        self.parcelles_modifiees[
                            parcelle_id
                        ]
                    )
                    continue

                ressources_ids = [
                    r[0]
                    for r
                    in parcelle["ressources"]
                ]

                ressources_noms = [
                    r[1]
                    for r
                    in parcelle["ressources"]
                ]

                parcelles.append(
                    {
                        "id": parcelle_id,
                        "agriculteur_id":
                            self.agriculteur_id,
                        "numero_lot":
                            parcelle["numero_lot"],
                        "superficie_m2":
                            parcelle["superficie_m2"],
                        "remarque":
                            parcelle["remarque"],
                        "actif":
                            parcelle["actif"],
                        "ressources_ids":
                            ressources_ids,
                        "ressources_noms":
                            ressources_noms,
                        "nouvelle": False,
                    }
                )

        parcelles.extend(
            self.nouvelles_parcelles
        )

        return parcelles

    def actualiser_parcelles(self):
        parcelles = (
            self.obtenir_parcelles_affichees()
        )

        self.table_parcelles.setRowCount(0)

        for parcelle in parcelles:
            ligne = (
                self.table_parcelles.rowCount()
            )

            self.table_parcelles.insertRow(
                ligne
            )

            lot_item = QTableWidgetItem(
                str(parcelle["numero_lot"])
            )

            lot_item.setData(
                Qt.ItemDataRole.UserRole,
                parcelle,
            )

            superficie = (
                f"{float(parcelle['superficie_m2']):,.0f}"
                .replace(",", " ")
                + " m²"
            )

            ressources = ", ".join(
                parcelle.get(
                    "ressources_noms",
                    [],
                )
            )

            if parcelle.get("nouvelle"):
                statut = "Nouveau"

            elif parcelle.get("actif", 1) == 1:
                statut = "Actif"

            else:
                statut = "Archivé"

            self.table_parcelles.setItem(
                ligne,
                0,
                lot_item,
            )

            self.table_parcelles.setItem(
                ligne,
                1,
                QTableWidgetItem(
                    superficie
                ),
            )

            self.table_parcelles.setItem(
                ligne,
                2,
                QTableWidgetItem(
                    ressources
                ),
            )

            self.table_parcelles.setItem(
                ligne,
                3,
                QTableWidgetItem(
                    statut
                ),
            )

        self.mettre_a_jour_action_parcelle()

    def ajouter_parcelle_formulaire(self):
        dialog = ParcelleDialog(
            parent=self
        )

        if not dialog.exec():
            return

        parcelle = dialog.resultat

        ressources = (
            lister_ressources_pour_noms(
                parcelle[
                    "ressources_ids"
                ]
            )
        )

        parcelle[
            "ressources_noms"
        ] = ressources

        parcelle["nouvelle"] = True

        self.nouvelles_parcelles.append(
            parcelle
        )

        self.actualiser_parcelles()

    def modifier_parcelle_selectionnee(self):
        ligne = (
            self.table_parcelles
            .currentRow()
        )

        if ligne < 0:
            QMessageBox.information(
                self,
                "Sélection",
                "Sélectionnez une parcelle.",
            )
            return

        item = self.table_parcelles.item(
            ligne,
            0,
        )

        parcelle = item.data(
            Qt.ItemDataRole.UserRole
        )

        if parcelle.get("actif", 1) == 0:
            QMessageBox.information(
                self,
                "Parcelle archivée",
                (
                    "Restaurez la parcelle "
                    "avant de la modifier."
                ),
            )
            return

        dialog = ParcelleDialog(
            parent=self,
            parcelle=parcelle,
        )

        if not dialog.exec():
            return

        resultat = dialog.resultat

        resultat[
            "ressources_noms"
        ] = lister_ressources_pour_noms(
            resultat["ressources_ids"]
        )

        if parcelle.get("nouvelle"):
            index = (
                self.nouvelles_parcelles
                .index(parcelle)
            )

            resultat["nouvelle"] = True

            self.nouvelles_parcelles[
                index
            ] = resultat

        else:
            resultat["nouvelle"] = False

            self.parcelles_modifiees[
                resultat["id"]
            ] = resultat

        # IMPORTANT :
        # aucune écriture SQLite ici.
        self.actualiser_parcelles()

    def valider_informations(self):
        nom = self.nom_input.text().strip()
        prenom = (
            self.prenom_input
            .text()
            .strip()
        )
        cin = self.cin_input.text().strip()
        telephone = (
            self.telephone_input
            .text()
            .strip()
        )

        if not nom:
            raise ValueError(
                "Le nom est obligatoire."
            )

        if not prenom:
            raise ValueError(
                "Le prénom est obligatoire."
            )

        if (
            len(cin) != 8
            or not cin.isdigit()
        ):
            raise ValueError(
                "Le CIN doit contenir exactement 8 chiffres."
            )

        if not telephone:
            raise ValueError(
                "Le téléphone est obligatoire."
            )

        return {
            "nom": nom,
            "prenom": prenom,
            "cin": cin,
            "telephone": telephone,
            "remarque": (
                self.remarque_input
                .toPlainText()
                .strip()
                or None
            ),
        }

    def enregistrer(self):
        try:
            infos = (
                self.valider_informations()
            )

            if self.agriculteur_id is None:
                if not self.nouvelles_parcelles:
                    raise ValueError(
                        "Ajoutez au moins une parcelle."
                    )

                parcelles = []

                for parcelle in (
                    self.nouvelles_parcelles
                ):
                    parcelles.append(
                        {
                            "numero_lot":
                                parcelle[
                                    "numero_lot"
                                ],
                            "superficie_m2":
                                parcelle[
                                    "superficie_m2"
                                ],
                            "ressources_ids":
                                parcelle[
                                    "ressources_ids"
                                ],
                            "remarque":
                                parcelle[
                                    "remarque"
                                ],
                        }
                    )

                creer_agriculteur(
                    nom=infos["nom"],
                    prenom=infos["prenom"],
                    cin=infos["cin"],
                    telephone=infos[
                        "telephone"
                    ],
                    remarque=infos[
                        "remarque"
                    ],
                    parcelles=parcelles,
                )

            else:
                modifier_agriculteur_complet(
                    agriculteur_id=self.agriculteur_id,
                    nom=infos["nom"],
                    prenom=infos["prenom"],
                    cin=infos["cin"],
                    telephone=infos["telephone"],
                    remarque=infos["remarque"],
                    parcelles_modifiees=list(
                        self.parcelles_modifiees.values()
                    ),
                    nouvelles_parcelles=(
                        self.nouvelles_parcelles
                    ),
                )

            self.accept()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Impossible d'enregistrer",
                str(error),
            )


    

    def archiver_ou_restaurer_parcelle(self):
        ligne = self.table_parcelles.currentRow()

        if ligne < 0:
            QMessageBox.information(
                self,
                "Sélection",
                "Sélectionnez une parcelle.",
            )
            return

        item = self.table_parcelles.item(
            ligne,
            0,
        )

        if item is None:
            return

        parcelle = item.data(
            Qt.ItemDataRole.UserRole
        )

        if parcelle is None:
            return

        # ---------------------------------------
        # Parcelle créée dans le formulaire
        # mais pas encore enregistrée.
        # ---------------------------------------

        if parcelle.get("nouvelle"):
            confirmation = QMessageBox.question(
                self,
                "Retirer la parcelle",
                (
                    f"Le lot {parcelle['numero_lot']} "
                    "n'est pas encore enregistré.\n\n"
                    "Voulez-vous le retirer "
                    "du formulaire ?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if (
                confirmation
                != QMessageBox.StandardButton.Yes
            ):
                return

            try:
                self.nouvelles_parcelles.remove(
                    parcelle
                )
            except ValueError:
                return

            self.actualiser_parcelles()
            return

        parcelle_id = parcelle["id"]

        # ---------------------------------------
        # Parcelle active → archivage
        # ---------------------------------------

        if parcelle.get("actif", 1) == 1:
            confirmation = QMessageBox.question(
                self,
                "Archiver la parcelle",
                (
                    f"Voulez-vous archiver "
                    f"le lot {parcelle['numero_lot']} ?\n\n"
                    "La parcelle ne sera plus proposée "
                    "pour les nouveaux tours d'eau."
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if (
                confirmation
                != QMessageBox.StandardButton.Yes
            ):
                return

            try:
                archiver_parcelle(
                    parcelle_id=parcelle_id,
                    motif=(
                        "Archivage depuis "
                        "la fiche agriculteur"
                    ),
                )

            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Archivage impossible",
                    str(error),
                )
                return

        # ---------------------------------------
        # Parcelle archivée → restauration
        # ---------------------------------------

        else:
            confirmation = QMessageBox.question(
                self,
                "Restaurer la parcelle",
                (
                    f"Voulez-vous restaurer "
                    f"le lot {parcelle['numero_lot']} ?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if (
                confirmation
                != QMessageBox.StandardButton.Yes
            ):
                return

            try:
                restaurer_parcelle(
                    parcelle_id=parcelle_id,
                    motif=(
                        "Restauration depuis "
                        "la fiche agriculteur"
                    ),
                )

            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Restauration impossible",
                    str(error),
                )
                return

        # ---------------------------------------
        # Recharger l'agriculteur depuis SQLite
        # ---------------------------------------

        self.agriculteur = obtenir_agriculteur(
            self.agriculteur_id
        )

        # Une ancienne modification en mémoire
        # concernant cette parcelle ne doit
        # plus être appliquée ensuite.
        self.parcelles_modifiees.pop(
            parcelle_id,
            None,
        )

        self.actualiser_parcelles()

    def mettre_a_jour_action_parcelle(self):
        parcelle = (
            self.obtenir_parcelle_selectionnee()
        )

        if parcelle is None:
            self.archive_parcelle_button.setText(
                "Archiver la parcelle"
            )

            self.archive_parcelle_button.setEnabled(
                False
            )

            self.transferer_button.setEnabled(
                False
            )

            self.diviser_button.setEnabled(
                False
            )

            return

        self.archive_parcelle_button.setEnabled(
            True
        )

        if parcelle.get("nouvelle"):
            self.archive_parcelle_button.setText(
                "Retirer du formulaire"
            )

            self.transferer_button.setEnabled(
                False
            )

            self.diviser_button.setEnabled(
                False
            )

            return

        if parcelle.get("actif", 1) == 0:
            self.archive_parcelle_button.setText(
                "Restaurer la parcelle"
            )

            self.transferer_button.setEnabled(
                False
            )

            self.diviser_button.setEnabled(
                False
            )

            return

        self.archive_parcelle_button.setText(
            "Archiver la parcelle"
        )

        parcelle_modifiee = (
            parcelle["id"]
            in self.parcelles_modifiees
        )

        self.transferer_button.setEnabled(
            not parcelle_modifiee
        )

        self.diviser_button.setEnabled(
            not parcelle_modifiee
        )

    def obtenir_parcelle_selectionnee(self):
        ligne = self.table_parcelles.currentRow()

        if ligne < 0:
            return None

        item = self.table_parcelles.item(
            ligne,
            0,
        )

        if item is None:
            return None

        return item.data(
            Qt.ItemDataRole.UserRole
        )
    
    def transferer_parcelle_selectionnee(self):
        parcelle = (
            self.obtenir_parcelle_selectionnee()
        )

        if parcelle is None:
            QMessageBox.information(
                self,
                "Sélection",
                "Sélectionnez une parcelle.",
            )
            return

        if parcelle.get("nouvelle"):
            QMessageBox.information(
                self,
                "Parcelle non enregistrée",
                (
                    "Cette parcelle n'est pas encore "
                    "enregistrée.\n\n"
                    "Enregistrez d'abord l'agriculteur."
                ),
            )
            return

        parcelle_id = parcelle["id"]

        if (
            parcelle_id
            in self.parcelles_modifiees
        ):
            QMessageBox.warning(
                self,
                "Modifications non enregistrées",
                (
                    "Cette parcelle contient des "
                    "modifications non enregistrées.\n\n"
                    "Cliquez d'abord sur Enregistrer "
                    "avant de la transférer."
                ),
            )
            return

        if parcelle.get("actif", 1) == 0:
            QMessageBox.information(
                self,
                "Parcelle archivée",
                "Une parcelle archivée ne peut pas être transférée.",
            )
            return

        dialog = OperationParcelleDialog(
            operation="TRANSFERT",
            parcelle=parcelle,
            parent=self,
        )

        if dialog.exec():
            self.agriculteur = (
                obtenir_agriculteur(
                    self.agriculteur_id
                )
            )

            self.parcelles_modifiees.pop(
                parcelle_id,
                None,
            )

            self.actualiser_parcelles()


    def diviser_parcelle_selectionnee(self):
        parcelle = (
            self.obtenir_parcelle_selectionnee()
        )

        if parcelle is None:
            QMessageBox.information(
                self,
                "Sélection",
                "Sélectionnez une parcelle.",
            )
            return

        if parcelle.get("nouvelle"):
            QMessageBox.information(
                self,
                "Parcelle non enregistrée",
                (
                    "Cette parcelle n'est pas encore "
                    "enregistrée.\n\n"
                    "Enregistrez d'abord l'agriculteur."
                ),
            )
            return

        parcelle_id = parcelle["id"]

        if (
            parcelle_id
            in self.parcelles_modifiees
        ):
            QMessageBox.warning(
                self,
                "Modifications non enregistrées",
                (
                    "Cette parcelle contient des "
                    "modifications non enregistrées.\n\n"
                    "Cliquez d'abord sur Enregistrer "
                    "avant de la diviser."
                ),
            )
            return

        if parcelle.get("actif", 1) == 0:
            QMessageBox.information(
                self,
                "Parcelle archivée",
                "Une parcelle archivée ne peut pas être divisée.",
            )
            return

        dialog = OperationParcelleDialog(
            operation="DIVISION",
            parcelle=parcelle,
            parent=self,
        )

        if dialog.exec():
            self.agriculteur = (
                obtenir_agriculteur(
                    self.agriculteur_id
                )
            )

            self.parcelles_modifiees.pop(
                parcelle_id,
                None,
            )

            self.actualiser_parcelles()


def lister_ressources_pour_noms(
    ressources_ids,
):
    from app.services.ressource_service import (
        lister_ressources,
    )

    ressources = lister_ressources()

    mapping = {
        r[0]: r[1]
        for r in ressources
    }

    return [
        mapping[ressource_id]
        for ressource_id
        in ressources_ids
        if ressource_id in mapping
    ]