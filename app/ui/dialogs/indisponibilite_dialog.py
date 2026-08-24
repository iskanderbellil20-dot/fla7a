from datetime import datetime

from PySide6.QtCore import (
    QDate,
    QTime,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
)

from app.services.indisponibilite_service import (
    creer_indisponibilite,
    rechercher_tours_impactes,
)


class IndisponibiliteDialog(QDialog):
    def __init__(
        self,
        ressource,
        parent=None,
    ):
        super().__init__(parent)

        self.ressource = ressource

        self.indisponibilite_id = None
        self.tours_impactes = []

        self.setWindowTitle(
            "Déclarer une indisponibilité"
        )

        self.resize(
            540,
            500,
        )

        self.creer_interface()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        titre = QLabel(
            "Déclarer une indisponibilité"
        )

        titre.setObjectName(
            "dialogTitle"
        )

        layout.addWidget(
            titre
        )

        ressource_label = QLabel(
            f"Ressource : {self.ressource[1]}"
        )

        ressource_label.setStyleSheet(
            "font-weight: 600;"
        )

        layout.addWidget(
            ressource_label
        )

        formulaire = QFormLayout()

        # --------------------------------
        # Type
        # --------------------------------

        self.type_input = QComboBox()

        self.type_input.addItem(
            "Panne",
            "PANNE",
        )

        self.type_input.addItem(
            "Maintenance",
            "MAINTENANCE",
        )

        self.type_input.addItem(
            "Autre",
            "AUTRE",
        )

        formulaire.addRow(
            "Type * :",
            self.type_input,
        )

        # --------------------------------
        # Début
        # --------------------------------

        self.date_debut = QDateEdit()

        self.date_debut.setCalendarPopup(
            True
        )

        self.date_debut.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.date_debut.setDate(
            QDate.currentDate()
        )

        self.heure_debut = QTimeEdit()

        self.heure_debut.setDisplayFormat(
            "HH:mm"
        )

        self.heure_debut.setTime(
            QTime.currentTime()
        )

        formulaire.addRow(
            "Date début * :",
            self.date_debut,
        )

        formulaire.addRow(
            "Heure début * :",
            self.heure_debut,
        )

        # --------------------------------
        # Fin
        # --------------------------------

        self.fin_inconnue = QCheckBox(
            "Fin inconnue"
        )

        self.fin_inconnue.setChecked(
            True
        )

        self.fin_inconnue.stateChanged.connect(
            self.mettre_a_jour_fin
        )

        formulaire.addRow(
            "",
            self.fin_inconnue,
        )

        self.date_fin = QDateEdit()

        self.date_fin.setCalendarPopup(
            True
        )

        self.date_fin.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.date_fin.setDate(
            QDate.currentDate()
        )

        self.heure_fin = QTimeEdit()

        self.heure_fin.setDisplayFormat(
            "HH:mm"
        )

        self.heure_fin.setTime(
            QTime.currentTime()
        )

        formulaire.addRow(
            "Date fin :",
            self.date_fin,
        )

        formulaire.addRow(
            "Heure fin :",
            self.heure_fin,
        )

        # --------------------------------
        # Motif
        # --------------------------------

        self.motif_input = QTextEdit()

        self.motif_input.setMaximumHeight(
            70
        )

        self.motif_input.setPlaceholderText(
            "Exemple : panne de la pompe"
        )

        formulaire.addRow(
            "Motif :",
            self.motif_input,
        )

        self.remarque_input = QTextEdit()

        self.remarque_input.setMaximumHeight(
            70
        )

        formulaire.addRow(
            "Remarque :",
            self.remarque_input,
        )

        layout.addLayout(
            formulaire
        )

        # --------------------------------
        # Boutons
        # --------------------------------

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self.enregistrer
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(
            buttons
        )

        self.mettre_a_jour_fin()

    def mettre_a_jour_fin(self):
        active = (
            not self.fin_inconnue.isChecked()
        )

        self.date_fin.setEnabled(
            active
        )

        self.heure_fin.setEnabled(
            active
        )

    def construire_datetime(
        self,
        date_widget,
        heure_widget,
    ):
        date = date_widget.date()
        heure = heure_widget.time()

        return datetime(
            date.year(),
            date.month(),
            date.day(),
            heure.hour(),
            heure.minute(),
            0,
        )

    def enregistrer(self):
        debut = self.construire_datetime(
            self.date_debut,
            self.heure_debut,
        )

        if self.fin_inconnue.isChecked():
            fin = None
        else:
            fin = self.construire_datetime(
                self.date_fin,
                self.heure_fin,
            )

            if fin <= debut:
                QMessageBox.warning(
                    self,
                    "Période invalide",
                    (
                        "La fin doit être "
                        "postérieure au début."
                    ),
                )
                return

        type_indisponibilite = (
            self.type_input.currentData()
        )

        motif = (
            self.motif_input
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

        try:
            self.indisponibilite_id = (
                creer_indisponibilite(
                    ressource_id=(
                        self.ressource[0]
                    ),
                    type_indisponibilite=(
                        type_indisponibilite
                    ),
                    date_heure_debut=(
                        debut
                    ),
                    date_heure_fin=(
                        fin
                    ),
                    motif=motif,
                    remarque=remarque,
                )
            )

            self.tours_impactes = (
                rechercher_tours_impactes(
                    ressource_id=(
                        self.ressource[0]
                    ),
                    date_heure_debut=(
                        debut
                    ),
                    date_heure_fin=(
                        fin
                    ),
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Impossible d'enregistrer",
                str(error),
            )
            return

        self.accept()