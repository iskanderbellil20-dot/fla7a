from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.ressource_service import (
    lister_ressources,
)


class ParcelleDialog(QDialog):
    def __init__(
        self,
        parent=None,
        parcelle=None,
    ):
        super().__init__(parent)

        self.parcelle = parcelle
        self.resultat = None
        self.ressource_checkboxes = {}

        if parcelle is None:
            self.setWindowTitle(
                "Ajouter une parcelle"
            )
        else:
            self.setWindowTitle(
                "Modifier la parcelle"
            )

        self.setMinimumWidth(520)
        self.resize(520, 540)

        self.creer_interface()
        self.charger_donnees()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        formulaire = QFormLayout()
        self.nom_lot_input = QLineEdit()

        self.nom_lot_input.setPlaceholderText(
            "Exemple : Olivier Nord"
        )
        self.numero_lot_input = QLineEdit()
        self.numero_lot_input.setPlaceholderText(
            "Exemple : 14"
        )

        self.superficie_input = QLineEdit()
        self.superficie_input.setPlaceholderText(
            "Exemple : 7500"
        )

        self.remarque_input = QTextEdit()
        self.remarque_input.setMaximumHeight(80)
        formulaire.addRow(
            "Nom du lot * :",
            self.nom_lot_input,
        )
        formulaire.addRow(
            "Numéro du lot * :",
            self.numero_lot_input,
        )

        formulaire.addRow(
            "Superficie (m²) * :",
            self.superficie_input,
        )

        formulaire.addRow(
            "Remarque :",
            self.remarque_input,
        )

        layout.addLayout(formulaire)

        titre_ressources = QLabel(
            "Ressources d'eau autorisées *"
        )
        titre_ressources.setStyleSheet(
            "font-weight: 600;"
        )

        layout.addWidget(titre_ressources)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(180)

        contenu = QWidget()
        ressources_layout = QVBoxLayout(
            contenu
        )

        ressources = lister_ressources()

        if not ressources:
            message = QLabel(
                "Aucune ressource active. "
                "Créez d'abord une ressource d'eau."
            )
            message.setWordWrap(True)
            ressources_layout.addWidget(message)

        for ressource in ressources:
            ressource_id = ressource[0]
            nom = ressource[1]
            etat = ressource[2]

            libelle = nom

            if etat != "DISPONIBLE":
                libelle += f" — {etat}"

            checkbox = QCheckBox(libelle)

            checkbox.setProperty(
                "ressource_id",
                ressource_id,
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

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.accepted.connect(
            self.valider
        )

        self.buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(self.buttons)

    def charger_donnees(self):


        if self.parcelle is None:
            return
        self.nom_lot_input.setText(
            str(
                self.parcelle.get(
                    "nom_lot",
                    "",
                )
                or ""
            )
        )

        self.numero_lot_input.setText(
            str(
                self.parcelle.get(
                    "numero_lot",
                    "",
                )
            )
        )

        superficie = self.parcelle.get(
            "superficie_m2",
            "",
        )

        if superficie != "":
            superficie_float = float(superficie)

            if superficie_float.is_integer():
                superficie = str(
                    int(superficie_float)
                )
            else:
                superficie = str(
                    superficie_float
                )

        self.superficie_input.setText(
            str(superficie)
        )

        self.remarque_input.setPlainText(
            self.parcelle.get(
                "remarque",
                "",
            )
            or ""
        )

        ressources_ids = set(
            self.parcelle.get(
                "ressources_ids",
                [],
            )
        )

        for ressource_id, checkbox in (
            self.ressource_checkboxes.items()
        ):
            checkbox.setChecked(
                ressource_id
                in ressources_ids
            )

    def valider(self):
        nom_lot = (
            self.nom_lot_input
            .text()
            .strip()
        )

        numero_lot = (
            self.numero_lot_input
            .text()
            .strip()
        )

        superficie_texte = (
            self.superficie_input
            .text()
            .strip()
            .replace(",", ".")
        )

        if not nom_lot:
            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Le nom du lot est obligatoire.",
            )
            return

        if not numero_lot:
            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Le numéro du lot est obligatoire.",
            )
            return

        try:
            superficie = float(
                superficie_texte
            )
        except ValueError:
            QMessageBox.warning(
                self,
                "Superficie invalide",
                "Saisissez une superficie valide.",
            )
            return

        if superficie <= 0:
            QMessageBox.warning(
                self,
                "Superficie invalide",
                (
                    "La superficie doit être "
                    "supérieure à 0."
                ),
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
                (
                    "Sélectionnez au moins "
                    "une ressource d'eau."
                ),
            )
            return

        self.resultat = {
            "id": (
                self.parcelle.get("id")
                if self.parcelle
                else None
            ),

            "nom_lot":
                nom_lot,

            "numero_lot":
                numero_lot,

            "superficie_m2":
                superficie,

            "ressources_ids":
                ressources_ids,

            "remarque": (
                self.remarque_input
                .toPlainText()
                .strip()
                or None
            ),

            "actif": (
                self.parcelle.get(
                    "actif",
                    1,
                )
                if self.parcelle
                else 1
            ),
        }

        self.accept()