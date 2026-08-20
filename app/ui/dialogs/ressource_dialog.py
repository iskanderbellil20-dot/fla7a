from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from app.services.ressource_service import (
    ETATS_RESSOURCE,
    creer_ressource,
    modifier_ressource,
    changer_etat_ressource,
)


class RessourceDialog(QDialog):
    def __init__(
        self,
        parent=None,
        ressource=None,
    ):
        super().__init__(parent)

        self.ressource = ressource

        if ressource is None:
            self.setWindowTitle(
                "Ajouter une ressource d'eau"
            )
        else:
            self.setWindowTitle(
                "Modifier la ressource"
            )

        self.setMinimumWidth(480)

        self.creer_interface()
        self.charger_donnees()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        formulaire = QFormLayout()

        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText(
            "Exemple : Puits 4"
        )

        self.etat_input = QComboBox()

        libelles_etats = {
            "DISPONIBLE": "Disponible",
            "EN_PANNE": "En panne",
            "MAINTENANCE": "Maintenance",
            "HORS_SERVICE": "Hors service",
        }

        for etat in ETATS_RESSOURCE:
            self.etat_input.addItem(
                libelles_etats.get(etat, etat),
                etat,
            )

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(90)

        self.remarque_input = QTextEdit()
        self.remarque_input.setMaximumHeight(90)

        formulaire.addRow(
            "Nom * :",
            self.nom_input,
        )

        formulaire.addRow(
            "État :",
            self.etat_input,
        )

        formulaire.addRow(
            "Description :",
            self.description_input,
        )

        formulaire.addRow(
            "Remarque :",
            self.remarque_input,
        )

        layout.addLayout(formulaire)

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

    def charger_donnees(self):
        if self.ressource is None:
            self.etat_input.setCurrentIndex(0)
            return

        self.nom_input.setText(
            self.ressource[1]
        )

        etat = self.ressource[2]

        index = self.etat_input.findData(etat)

        if index >= 0:
            self.etat_input.setCurrentIndex(index)

        if self.ressource[3]:
            self.description_input.setPlainText(
                self.ressource[3]
            )

        if self.ressource[4]:
            self.remarque_input.setPlainText(
                self.ressource[4]
            )

    def enregistrer(self):
        nom = self.nom_input.text().strip()

        description = (
            self.description_input
            .toPlainText()
            .strip()
            or None
        )

        remarque = (
            self.remarque_input
            .toPlainText()
            .strip()
            or None
        )

        etat = self.etat_input.currentData()

        if not nom:
            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Le nom de la ressource est obligatoire.",
            )
            self.nom_input.setFocus()
            return

        try:
            if self.ressource is None:
                ressource_id = creer_ressource(
                    nom=nom,
                    description=description,
                    remarque=remarque,
                )

                if etat != "DISPONIBLE":
                    changer_etat_ressource(
                        ressource_id,
                        etat,
                    )

            else:
                ressource_id = self.ressource[0]

                modifier_ressource(
                    ressource_id=ressource_id,
                    nom=nom,
                    description=description,
                    remarque=remarque,
                )

                if etat != self.ressource[2]:
                    changer_etat_ressource(
                        ressource_id,
                        etat,
                    )

            self.accept()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                str(error),
            )