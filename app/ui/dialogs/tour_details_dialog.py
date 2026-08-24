from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.services.recu_service import (
    formater_date,
    formater_duree,
    formater_heure,
)

from app.services.tour_eau_service import (
    annuler_tour_eau,
    obtenir_tour_eau,
)

from app.ui.dialogs.modifier_tour_dialog import (
    ModifierTourDialog,
)

from app.ui.dialogs.recu_dialog import (
    RecuDialog,
)


class TourDetailsDialog(QDialog):
    def __init__(
        self,
        tour_id,
        parent=None,
    ):
        super().__init__(parent)

        self.tour_id = tour_id
        self.tour = None

        self.donnees_modifiees = False

        self.setWindowTitle(
            "Détail du tour d'eau"
        )

        self.resize(590, 650)

        self.creer_interface()
        self.charger_tour()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        self.titre = QLabel(
            "Tour d'eau"
        )

        self.titre.setObjectName(
            "dialogTitle"
        )

        layout.addWidget(
            self.titre
        )

        informations = QGroupBox(
            "Informations"
        )

        formulaire = QFormLayout(
            informations
        )

        self.agriculteur_label = QLabel()
        self.cin_label = QLabel()
        self.lot_label = QLabel()
        self.superficie_label = QLabel()

        self.ressource_label = QLabel()

        self.date_label = QLabel()
        self.debut_label = QLabel()
        self.fin_label = QLabel()
        self.duree_label = QLabel()

        self.statut_label = QLabel()

        self.remarque_label = QLabel()
        self.remarque_label.setWordWrap(
            True
        )

        formulaire.addRow(
            "Agriculteur :",
            self.agriculteur_label,
        )

        formulaire.addRow(
            "CIN :",
            self.cin_label,
        )

        formulaire.addRow(
            "Lot :",
            self.lot_label,
        )

        formulaire.addRow(
            "Superficie :",
            self.superficie_label,
        )

        formulaire.addRow(
            "Ressource :",
            self.ressource_label,
        )

        formulaire.addRow(
            "Date :",
            self.date_label,
        )

        formulaire.addRow(
            "Début :",
            self.debut_label,
        )

        formulaire.addRow(
            "Fin :",
            self.fin_label,
        )

        formulaire.addRow(
            "Durée :",
            self.duree_label,
        )

        formulaire.addRow(
            "Statut :",
            self.statut_label,
        )

        formulaire.addRow(
            "Remarque :",
            self.remarque_label,
        )

        layout.addWidget(
            informations
        )

        # --------------------------------
        # Actions métier
        # --------------------------------

        actions = QHBoxLayout()

        self.modifier_button = QPushButton(
            "Modifier"
        )

        self.modifier_button.clicked.connect(
            self.modifier
        )

        self.reporter_button = QPushButton(
            "Reporter"
        )

        self.reporter_button.clicked.connect(
            self.reporter
        )

        self.annuler_button = QPushButton(
            "Annuler le tour"
        )

        self.annuler_button.clicked.connect(
            self.annuler
        )

        actions.addWidget(
            self.modifier_button
        )

        actions.addWidget(
            self.reporter_button
        )

        actions.addWidget(
            self.annuler_button
        )

        layout.addLayout(actions)

        self.recu_button = QPushButton(
            "Voir / Réimprimer le reçu"
        )

        self.recu_button.setObjectName(
            "primaryButton"
        )

        self.recu_button.clicked.connect(
            self.ouvrir_recu
        )

        layout.addWidget(
            self.recu_button
        )

        layout.addStretch()

        fermer_button = QPushButton(
            "Fermer"
        )

        fermer_button.clicked.connect(
            self.accept
        )

        layout.addWidget(
            fermer_button
        )

    def charger_tour(self):
        self.tour = obtenir_tour_eau(
            self.tour_id
        )

        if self.tour is None:
            QMessageBox.critical(
                self,
                "Erreur",
                "Tour d'eau introuvable.",
            )

            self.reject()
            return

        self.titre.setText(
            (
                "Tour d'eau — Reçu N° "
                f"{self.tour['numero_recu_formate']}"
            )
        )

        self.agriculteur_label.setText(
            (
                f"{self.tour['prenom']} "
                f"{self.tour['nom']}"
            )
        )

        self.cin_label.setText(
            self.tour["cin"] or "-"
        )

        self.lot_label.setText(
            str(
                self.tour[
                    "numero_lot"
                ]
            )
        )

        superficie = (
            f"{float(self.tour['superficie_m2']):,.0f}"
            .replace(",", " ")
        )

        self.superficie_label.setText(
            f"{superficie} m²"
        )

        self.ressource_label.setText(
            self.tour[
                "ressource_nom"
            ]
        )

        self.date_label.setText(
            formater_date(
                self.tour[
                    "date_heure_debut"
                ]
            )
        )

        self.debut_label.setText(
            formater_heure(
                self.tour[
                    "date_heure_debut"
                ]
            )
        )

        self.fin_label.setText(
            (
                formater_date(
                    self.tour[
                        "date_heure_fin"
                    ]
                )
                + " "
                + formater_heure(
                    self.tour[
                        "date_heure_fin"
                    ]
                )
            )
        )

        self.duree_label.setText(
            formater_duree(
                self.tour[
                    "duree_minutes"
                ]
            )
        )

        self.statut_label.setText(
            self.tour["statut"]
        )

        self.remarque_label.setText(
            self.tour["remarque"]
            or "Aucune"
        )

        self.mettre_a_jour_actions()

    def mettre_a_jour_actions(self):
        planifie = (
            self.tour["statut"]
            == "PLANIFIE"
        )

        self.modifier_button.setEnabled(
            planifie
        )

        self.reporter_button.setEnabled(
            planifie
        )

        self.annuler_button.setEnabled(
            planifie
        )

        self.recu_button.setEnabled(
            True
        )

    def modifier(self):
        dialog = ModifierTourDialog(
            tour_id=self.tour_id,
            mode="MODIFIER",
            parent=self,
        )

        if dialog.exec():
            self.donnees_modifiees = True

            self.charger_tour()

            QMessageBox.information(
                self,
                "Tour modifié",
                (
                    "Le tour d'eau a été "
                    "modifié avec succès."
                ),
            )

    def reporter(self):
        confirmation = QMessageBox.question(
            self,
            "Reporter le tour",
            (
                "Le report conservera le tour "
                "actuel avec le statut REPORTÉ "
                "et créera un nouveau tour "
                "avec un nouveau numéro de reçu.\n\n"
                "Continuer ?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if (
            confirmation
            != QMessageBox.StandardButton.Yes
        ):
            return

        dialog = ModifierTourDialog(
            tour_id=self.tour_id,
            mode="REPORTER",
            parent=self,
        )

        if dialog.exec():
            self.donnees_modifiees = True

            self.charger_tour()

            QMessageBox.information(
                self,
                "Tour reporté",
                (
                    "Le tour d'eau a été reporté. "
                    "Un nouveau tour et un nouveau "
                    "numéro de reçu ont été créés."
                ),
            )

    def annuler(self):
        confirmation = QMessageBox.question(
            self,
            "Annuler le tour d'eau",
            (
                "Voulez-vous réellement "
                "annuler ce tour d'eau ?\n\n"
                "Le tour restera dans l'historique."
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
            annuler_tour_eau(
                tour_id=self.tour_id,
                motif=(
                    "Annulation depuis le planning"
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Annulation impossible",
                str(error),
            )
            return

        self.donnees_modifiees = True

        self.charger_tour()

        QMessageBox.information(
            self,
            "Tour annulé",
            (
                "Le tour d'eau a été annulé. "
                "Le créneau est maintenant libéré."
            ),
        )

    def ouvrir_recu(self):
        dialog = RecuDialog(
            tour_id=self.tour_id,
            parent=self,
        )

        dialog.exec()