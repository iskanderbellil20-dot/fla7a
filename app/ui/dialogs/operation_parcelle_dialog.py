from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QCheckBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCompleter,
)


from app.services.agriculteur_service import (
    diviser_parcelle,
    lister_agriculteurs_avec_resume,
    transferer_parcelle,
)

from app.services.ressource_service import (
    lister_ressources,
)


class OperationParcelleDialog(QDialog):
    def __init__(
        self,
        operation,
        parcelle,
        parent=None,
    ):
        super().__init__(parent)

        self.operation = operation
        self.parcelle = parcelle

        self.ressource_checkboxes = {}

        if operation == "TRANSFERT":
            self.setWindowTitle(
                "Transférer la parcelle"
            )
        elif operation == "DIVISION":
            self.setWindowTitle(
                "Diviser / céder une partie"
            )
        else:
            raise ValueError(
                "Opération parcelle inconnue."
            )

        self.resize(600, 650)

        self.creer_interface()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        titre = QLabel(
            (
                "Transfert de parcelle"
                if self.operation == "TRANSFERT"
                else "Division / cession partielle"
            )
        )
        titre.setObjectName("dialogTitle")

        layout.addWidget(titre)

        info = QLabel(
            f"Lot : {self.parcelle['numero_lot']}\n"
            f"Superficie actuelle : "
            f"{float(self.parcelle['superficie_m2']):,.0f} m²"
        )

        layout.addWidget(info)

        # -----------------------------------------
        # Formulaire
        # -----------------------------------------

        formulaire = QFormLayout()

        # Nouveau propriétaire
        self.agriculteur_combo = QComboBox()

        self.agriculteur_combo.setEditable(True)

        self.agriculteur_combo.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert
        )

        agriculteurs = (
            lister_agriculteurs_avec_resume()
        )

        for agriculteur in agriculteurs:
            agriculteur_id = agriculteur[0]

            # Ne pas proposer le propriétaire actuel.
            if (
                agriculteur_id
                == self.parcelle.get(
                    "agriculteur_id"
                )
            ):
                continue

            texte = (
                f"{agriculteur[2]} "
                f"{agriculteur[1]} "
                f"— CIN {agriculteur[3]}"
            )

            self.agriculteur_combo.addItem(
                texte,
                agriculteur_id,
            )

        completer = (
            self.agriculteur_combo.completer()
        )

        completer.setCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive
        )

        completer.setFilterMode(
            Qt.MatchFlag.MatchContains
        )

        self.agriculteur_combo.setCurrentIndex(-1)

        self.agriculteur_combo.lineEdit().setPlaceholderText(
            "Rechercher par nom, prénom ou CIN..."
        )

        formulaire.addRow(
            "Nouveau propriétaire * :",
            self.agriculteur_combo,
        )

        # -----------------------------------------
        # Champs spécifiques à la division
        # -----------------------------------------

        self.numero_lot_input = QLineEdit()
        self.superficie_input = QLineEdit()

        if self.operation == "DIVISION":
            self.numero_lot_input.setPlaceholderText(
                (
                    f"Exemple : "
                    f"{self.parcelle['numero_lot']}-B"
                )
            )

            self.superficie_input.setPlaceholderText(
                "Superficie cédée en m²"
            )

            formulaire.addRow(
                "Nouveau numéro de lot * :",
                self.numero_lot_input,
            )

            formulaire.addRow(
                "Superficie cédée (m²) * :",
                self.superficie_input,
            )

        # -----------------------------------------
        # Motif
        # -----------------------------------------

        self.motif_input = QTextEdit()
        self.motif_input.setMaximumHeight(80)

        formulaire.addRow(
            "Motif / remarque :",
            self.motif_input,
        )

        layout.addLayout(formulaire)

        # -----------------------------------------
        # Ressources
        # -----------------------------------------

        ressources_label = QLabel(
            "Ressources autorisées "
            "pour la nouvelle parcelle *"
        )

        ressources_label.setStyleSheet(
            "font-weight: 600;"
        )

        layout.addWidget(ressources_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(170)

        contenu = QWidget()

        ressources_layout = QVBoxLayout(
            contenu
        )

        ressources = lister_ressources()

        anciennes_ids = set(
            self.parcelle.get(
                "ressources_ids",
                [],
            )
        )

        for ressource in ressources:
            ressource_id = ressource[0]
            nom_ressource = ressource[1]
            etat = ressource[2]

            libelle = nom_ressource

            if etat != "DISPONIBLE":
                libelle += f" — {etat}"

            checkbox = QCheckBox(
                libelle
            )

            checkbox.setChecked(
                ressource_id
                in anciennes_ids
            )

            self.ressource_checkboxes[
                ressource_id
            ] = checkbox

            ressources_layout.addWidget(
                checkbox
            )

        ressources_layout.addStretch()

        scroll.setWidget(contenu)

        layout.addWidget(scroll)

        # -----------------------------------------
        # Boutons
        # -----------------------------------------

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self.executer_operation
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

    def executer_operation(self):
        nouvel_agriculteur_id = (
            self.agriculteur_combo
            .currentData()
        )

        if nouvel_agriculteur_id is None:
            QMessageBox.warning(
                self,
                "Propriétaire obligatoire",
                "Sélectionnez le nouveau propriétaire.",
            )
            return

        ressources_ids = [
            ressource_id
            for ressource_id, checkbox
            in self.ressource_checkboxes.items()
            if checkbox.isChecked()
        ]

        if not ressources_ids:
            QMessageBox.warning(
                self,
                "Ressource obligatoire",
                "Sélectionnez au moins une ressource.",
            )
            return

        motif = (
            self.motif_input
            .toPlainText()
            .strip()
            or None
        )

        try:
            if self.operation == "TRANSFERT":
                transferer_parcelle(
                    parcelle_id=(
                        self.parcelle["id"]
                    ),
                    nouvel_agriculteur_id=(
                        nouvel_agriculteur_id
                    ),
                    ressources_ids=(
                        ressources_ids
                    ),
                    motif=motif,
                )

            else:
                numero_lot = (
                    self.numero_lot_input
                    .text()
                    .strip()
                )

                superficie = (
                    self.superficie_input
                    .text()
                    .strip()
                    .replace(",", ".")
                )

                diviser_parcelle(
                    parcelle_id=(
                        self.parcelle["id"]
                    ),
                    nouvel_agriculteur_id=(
                        nouvel_agriculteur_id
                    ),
                    nouvelle_superficie_m2=(
                        superficie
                    ),
                    nouveau_numero_lot=(
                        numero_lot
                    ),
                    ressources_ids=(
                        ressources_ids
                    ),
                    motif=motif,
                )

            self.accept()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Opération impossible",
                str(error),
            )