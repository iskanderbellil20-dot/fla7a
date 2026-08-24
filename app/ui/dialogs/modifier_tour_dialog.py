from datetime import datetime, timedelta

from PySide6.QtCore import (
    QDate,
    QTime,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
)

from app.services.agriculteur_service import (
    obtenir_parcelle_avec_ressources,
)

from app.services.tour_eau_service import (
    modifier_tour_eau,
    obtenir_tour_eau,
    reporter_tour_eau,
)


class ModifierTourDialog(QDialog):
    def __init__(
        self,
        tour_id,
        mode="MODIFIER",
        parent=None,
    ):
        super().__init__(parent)

        self.tour_id = tour_id
        self.mode = mode

        if self.mode not in (
            "MODIFIER",
            "REPORTER",
        ):
            raise ValueError(
                "Mode de modification invalide."
            )

        self.tour = obtenir_tour_eau(
            tour_id
        )

        if self.tour is None:
            raise ValueError(
                "Tour d'eau introuvable."
            )

        self.parcelle = (
            obtenir_parcelle_avec_ressources(
                self.tour["parcelle_id"]
            )
        )

        if self.parcelle is None:
            raise ValueError(
                "Parcelle introuvable."
            )

        if self.mode == "MODIFIER":
            self.setWindowTitle(
                "Modifier le tour d'eau"
            )
        else:
            self.setWindowTitle(
                "Reporter le tour d'eau"
            )

        self.resize(
            560,
            560,
        )

        self.creer_interface()
        self.charger_donnees()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        titre = QLabel(
            (
                "Modifier le tour d'eau"
                if self.mode == "MODIFIER"
                else "Reporter le tour d'eau"
            )
        )

        titre.setObjectName(
            "dialogTitle"
        )

        layout.addWidget(
            titre
        )

        formulaire = QFormLayout()

        self.agriculteur_label = QLabel()
        self.parcelle_label = QLabel()
        self.superficie_label = QLabel()

        self.ressource_combo = QComboBox()

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(
            True
        )
        self.date_input.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.heure_input = QTimeEdit()
        self.heure_input.setDisplayFormat(
            "HH:mm"
        )

        self.duree_heures = QSpinBox()
        self.duree_heures.setRange(
            0,
            240,
        )
        self.duree_heures.setSuffix(
            " h"
        )

        self.duree_minutes = QSpinBox()
        self.duree_minutes.setRange(
            0,
            59,
        )
        self.duree_minutes.setSuffix(
            " min"
        )

        duree_layout = QHBoxLayout()

        duree_layout.addWidget(
            self.duree_heures
        )

        duree_layout.addWidget(
            self.duree_minutes
        )

        duree_layout.addStretch()

        self.fin_label = QLabel("-")
        self.fin_label.setStyleSheet(
            "font-weight: 700;"
        )

        self.remarque_input = QTextEdit()
        self.remarque_input.setMaximumHeight(
            70
        )

        self.motif_input = QTextEdit()
        self.motif_input.setMaximumHeight(
            70
        )

        formulaire.addRow(
            "Agriculteur :",
            self.agriculteur_label,
        )

        formulaire.addRow(
            "Parcelle :",
            self.parcelle_label,
        )

        formulaire.addRow(
            "Superficie :",
            self.superficie_label,
        )

        formulaire.addRow(
            "Ressource * :",
            self.ressource_combo,
        )

        formulaire.addRow(
            "Date * :",
            self.date_input,
        )

        formulaire.addRow(
            "Début * :",
            self.heure_input,
        )

        formulaire.addRow(
            "Durée * :",
            duree_layout,
        )

        formulaire.addRow(
            "Fin calculée :",
            self.fin_label,
        )

        formulaire.addRow(
            "Remarque :",
            self.remarque_input,
        )

        formulaire.addRow(
            "Motif de l'opération :",
            self.motif_input,
        )

        layout.addLayout(
            formulaire
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

        layout.addWidget(
            self.buttons
        )

        self.date_input.dateChanged.connect(
            self.calculer_fin
        )

        self.heure_input.timeChanged.connect(
            self.calculer_fin
        )

        self.duree_heures.valueChanged.connect(
            self.calculer_fin
        )

        self.duree_minutes.valueChanged.connect(
            self.calculer_fin
        )

    def charger_donnees(self):
        self.agriculteur_label.setText(
            (
                f"{self.tour['prenom']} "
                f"{self.tour['nom']}"
            )
        )

        self.parcelle_label.setText(
            (
                f"Lot "
                f"{self.tour['numero_lot']}"
            )
        )

        superficie = (
            f"{float(self.tour['superficie_m2']):,.0f}"
            .replace(",", " ")
        )

        self.superficie_label.setText(
            f"{superficie} m²"
        )

        self.ressource_combo.clear()

        for ressource in self.parcelle[
            "ressources"
        ]:
            ressource_id = ressource[0]
            nom = ressource[1]
            etat = ressource[2]
            actif = ressource[3]

            if actif == 0:
                continue

            texte = nom

            if etat != "DISPONIBLE":
                texte += f" — {etat}"

            self.ressource_combo.addItem(
                texte,
                ressource_id,
            )

        index_ressource = (
            self.ressource_combo.findData(
                self.tour["ressource_id"]
            )
        )

        if index_ressource >= 0:
            self.ressource_combo.setCurrentIndex(
                index_ressource
            )

        debut = datetime.strptime(
            self.tour["date_heure_debut"],
            "%Y-%m-%d %H:%M:%S",
        )

        self.date_input.setDate(
            QDate(
                debut.year,
                debut.month,
                debut.day,
            )
        )

        self.heure_input.setTime(
            QTime(
                debut.hour,
                debut.minute,
            )
        )

        duree = int(
            self.tour["duree_minutes"]
        )

        self.duree_heures.setValue(
            duree // 60
        )

        self.duree_minutes.setValue(
            duree % 60
        )

        self.remarque_input.setPlainText(
            self.tour["remarque"]
            or ""
        )

        self.motif_input.clear()

        self.calculer_fin()

    def obtenir_debut(self):
        date = self.date_input.date()
        heure = self.heure_input.time()

        return datetime(
            date.year(),
            date.month(),
            date.day(),
            heure.hour(),
            heure.minute(),
            0,
        )

    def obtenir_duree(self):
        return (
            self.duree_heures.value()
            * 60
            + self.duree_minutes.value()
        )

    def calculer_fin(self):
        debut = self.obtenir_debut()

        duree = self.obtenir_duree()

        if duree <= 0:
            self.fin_label.setText(
                "Durée invalide"
            )
            return

        fin = (
            debut
            + timedelta(
                minutes=duree
            )
        )

        if fin.date() == debut.date():
            texte = fin.strftime(
                "%H:%M"
            )
        else:
            texte = fin.strftime(
                "%d/%m/%Y à %H:%M"
            )

        self.fin_label.setText(
            texte
        )

    def enregistrer(self):
        ressource_id = (
            self.ressource_combo
            .currentData()
        )

        if ressource_id is None:
            QMessageBox.warning(
                self,
                "Ressource obligatoire",
                "Sélectionnez une ressource.",
            )
            return

        duree = self.obtenir_duree()

        if duree <= 0:
            QMessageBox.warning(
                self,
                "Durée invalide",
                (
                    "La durée doit être "
                    "supérieure à 0 minute."
                ),
            )
            return

        remarque = (
            self.remarque_input
            .toPlainText()
            .strip()
            or None
        )

        motif = (
            self.motif_input
            .toPlainText()
            .strip()
            or None
        )

        try:
            if self.mode == "MODIFIER":
                modifier_tour_eau(
                    tour_id=self.tour_id,

                    parcelle_id=(
                        self.tour[
                            "parcelle_id"
                        ]
                    ),

                    ressource_id=(
                        ressource_id
                    ),

                    date_heure_debut=(
                        self.obtenir_debut()
                    ),

                    duree_minutes=(
                        duree
                    ),

                    remarque=(
                        remarque
                    ),

                    motif=(
                        motif
                    ),
                )

            else:
                reporter_tour_eau(
                    tour_id=self.tour_id,

                    nouvelle_ressource_id=(
                        ressource_id
                    ),

                    nouvelle_date_heure_debut=(
                        self.obtenir_debut()
                    ),

                    nouvelle_duree_minutes=(
                        duree
                    ),

                    motif=(
                        motif
                    ),

                    remarque=(
                        remarque
                    ),
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Opération impossible",
                str(error),
            )
            return

        self.accept()