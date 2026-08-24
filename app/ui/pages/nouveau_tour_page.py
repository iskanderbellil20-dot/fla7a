from datetime import datetime

from PySide6.QtCore import (
    QDate,
    QTime,
    Qt,
)
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from app.ui.dialogs.recu_dialog import (
    RecuDialog,
)
from app.services.agriculteur_service import (
    obtenir_agriculteur,
    rechercher_agriculteurs,
)

from app.services.tour_eau_service import (
    creer_tour_eau,
)


class NouveauTourPage(QWidget):
    def __init__(self):
        super().__init__()

        self.agriculteur_selectionne = None
        self.parcelle_selectionnee = None
        self.ressource_planning_id = None
        self.ressource_planning_nom = None
        self.creer_interface()
        self.initialiser_formulaire()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            28,
            25,
            28,
            25,
        )

        layout.setSpacing(16)

        titre = QLabel("Nouveau tour d'eau")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Attribuer un créneau d'irrigation "
            "à un agriculteur."
        )

        description.setObjectName(
            "pageDescription"
        )

        layout.addWidget(titre)
        layout.addWidget(description)

        # ----------------------------------
        # Recherche agriculteur
        # ----------------------------------

        recherche_box = QGroupBox(
            "1. Agriculteur"
        )

        recherche_layout = QVBoxLayout(
            recherche_box
        )

        barre_recherche = QHBoxLayout()

        self.recherche_input = QLineEdit()

        self.recherche_input.setPlaceholderText(
            "CIN, nom, prénom ou numéro de lot..."
        )

        self.rechercher_button = QPushButton(
            "Rechercher"
        )

        self.rechercher_button.setObjectName(
            "primaryButton"
        )

        self.rechercher_button.clicked.connect(
            self.rechercher
        )

        self.recherche_input.returnPressed.connect(
            self.rechercher
        )

        barre_recherche.addWidget(
            self.recherche_input,
            stretch=1,
        )

        barre_recherche.addWidget(
            self.rechercher_button
        )

        recherche_layout.addLayout(
            barre_recherche
        )

        self.resultats_combo = QComboBox()

        self.resultats_combo.setPlaceholderText(
            "Sélectionnez un agriculteur..."
        )

        self.resultats_combo.currentIndexChanged.connect(
            self.selectionner_agriculteur
        )

        recherche_layout.addWidget(
            self.resultats_combo
        )

        self.agriculteur_info = QLabel(
            "Aucun agriculteur sélectionné."
        )

        self.agriculteur_info.setWordWrap(True)

        recherche_layout.addWidget(
            self.agriculteur_info
        )

        layout.addWidget(recherche_box)

        # ----------------------------------
        # Parcelle
        # ----------------------------------

        parcelle_box = QGroupBox(
            "2. Parcelle"
        )

        parcelle_layout = QFormLayout(
            parcelle_box
        )

        self.parcelle_combo = QComboBox()

        self.parcelle_combo.currentIndexChanged.connect(
            self.selectionner_parcelle
        )

        self.superficie_label = QLabel("-")

        self.ressource_combo = QComboBox()

        parcelle_layout.addRow(
            "Parcelle / Lot * :",
            self.parcelle_combo,
        )

        parcelle_layout.addRow(
            "Superficie :",
            self.superficie_label,
        )

        parcelle_layout.addRow(
            "Ressource d'eau * :",
            self.ressource_combo,
        )

        layout.addWidget(parcelle_box)

        # ----------------------------------
        # Horaire
        # ----------------------------------

        horaire_box = QGroupBox(
            "3. Date, heure et durée"
        )

        horaire_layout = QFormLayout(
            horaire_box
        )

        self.date_input = QDateEdit()

        self.date_input.setCalendarPopup(True)

        self.date_input.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.heure_input = QTimeEdit()

        self.heure_input.setDisplayFormat(
            "HH:mm"
        )
        self.heure_input.setTime(
            QTime.currentTime()
        )

        self.duree_heures = QSpinBox()
        self.duree_heures.setRange(0, 240)
        self.duree_heures.setSuffix(" h")

        self.duree_minutes = QSpinBox()

        self.duree_minutes.setRange(
            0,
            30,
        )

        self.duree_minutes.setSingleStep(
            30
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

        horaire_layout.addRow(
            "Date * :",
            self.date_input,
        )

        horaire_layout.addRow(
            "Heure de début * :",
            self.heure_input,
        )

        horaire_layout.addRow(
            "Durée * :",
            duree_layout,
        )

        horaire_layout.addRow(
            "Fin calculée :",
            self.fin_label,
        )

        layout.addWidget(horaire_box)

        # ----------------------------------
        # Remarque
        # ----------------------------------

        remarque_box = QGroupBox(
            "4. Remarque"
        )

        remarque_layout = QVBoxLayout(
            remarque_box
        )

        self.remarque_input = QTextEdit()

        self.remarque_input.setMaximumHeight(
            75
        )

        remarque_layout.addWidget(
            self.remarque_input
        )

        layout.addWidget(remarque_box)

        # ----------------------------------
        # Validation
        # ----------------------------------

        actions = QHBoxLayout()

        actions.addStretch()

        self.valider_button = QPushButton(
            "Valider le tour d'eau"
        )

        self.valider_button.setObjectName(
            "primaryButton"
        )

        self.valider_button.setMinimumHeight(
            42
        )

        self.valider_button.clicked.connect(
            self.enregistrer_tour
        )

        actions.addWidget(
            self.valider_button
        )

        layout.addLayout(actions)

        layout.addStretch()

        # Recalcul automatique.
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

    def initialiser_formulaire(self):
        aujourd_hui = QDate.currentDate()

        maintenant = QTime.currentTime()

        self.date_input.setDate(
            aujourd_hui
        )

        self.heure_input.setTime(
            maintenant
        )

        self.duree_heures.setValue(1)
        self.duree_minutes.setValue(0)

        self.parcelle_combo.setEnabled(
            False
        )

        self.ressource_combo.setEnabled(
            False
        )

        self.valider_button.setEnabled(
            False
        )

        self.calculer_fin()

    def preparer_depuis_planning(
        self,
        date_selectionnee,
        heure,
        minute,
        ressource_id,
        ressource_nom,
    ):
        # Réinitialiser l'ancien formulaire.
        self.reinitialiser_apres_creation()

        # Date venant du planning.
        self.date_input.setDate(
            date_selectionnee
        )

        # Heure correspondant au créneau.
        self.heure_input.setTime(
            QTime(
                heure,
                minute,
            )
        )

        # Garder la ressource demandée
        # en mémoire.
        self.ressource_planning_id = (
            ressource_id
        )

        self.ressource_planning_nom = (
            ressource_nom
        )

        self.agriculteur_info.setText(
            (
                "Création depuis le planning — "
                f"{ressource_nom} — "
                f"{heure:02d}:{minute:02d}\n"
                "Recherchez maintenant "
                "l'agriculteur."
            )
        )

        self.recherche_input.setFocus()

    def rechercher(self):
        terme = (
            self.recherche_input
            .text()
            .strip()
        )

        if not terme:
            QMessageBox.information(
                self,
                "Recherche",
                (
                    "Saisissez un CIN, un nom, "
                    "un prénom ou un numéro de lot."
                ),
            )
            return

        resultats = rechercher_agriculteurs(
            terme
        )

        self.resultats_combo.blockSignals(
            True
        )

        self.resultats_combo.clear()

        for agriculteur in resultats:
            texte = (
                f"{agriculteur[2]} "
                f"{agriculteur[1]} "
                f"— CIN {agriculteur[3]}"
            )

            self.resultats_combo.addItem(
                texte,
                agriculteur[0],
            )

        self.resultats_combo.blockSignals(
            False
        )

        if not resultats:
            self.agriculteur_selectionne = None

            self.agriculteur_info.setText(
                "Aucun agriculteur trouvé."
            )

            self.parcelle_combo.clear()

            self.parcelle_combo.setEnabled(
                False
            )

            self.ressource_combo.clear()

            self.ressource_combo.setEnabled(
                False
            )

            self.valider_button.setEnabled(
                False
            )

            return

        self.resultats_combo.setCurrentIndex(0)

        self.selectionner_agriculteur(0)

    def selectionner_agriculteur(
        self,
        index,
    ):
        if index < 0:
            return

        agriculteur_id = (
            self.resultats_combo
            .itemData(index)
        )

        if agriculteur_id is None:
            return

        agriculteur = obtenir_agriculteur(
            agriculteur_id
        )

        if agriculteur is None:
            return

        if agriculteur["actif"] == 0:
            QMessageBox.warning(
                self,
                "Agriculteur archivé",
                (
                    "Cet agriculteur est archivé "
                    "et ne peut pas recevoir de tour."
                ),
            )
            return

        self.agriculteur_selectionne = (
            agriculteur
        )

        self.agriculteur_info.setText(
            (
                f"{agriculteur['prenom']} "
                f"{agriculteur['nom']}   |   "
                f"CIN : {agriculteur['cin']}   |   "
                f"Tél : {agriculteur['telephone']}"
            )
        )

        self.charger_parcelles()

    def charger_parcelles(self):
        self.parcelle_combo.blockSignals(
            True
        )

        self.parcelle_combo.clear()

        parcelles = [
            parcelle
            for parcelle
            in self.agriculteur_selectionne[
                "parcelles"
            ]
            if parcelle["actif"] == 1
        ]

        for parcelle in parcelles:
            texte = (
                f"Lot {parcelle['numero_lot']} "
                f"— "
                f"{parcelle['superficie_m2']:,.0f} m²"
            )

            self.parcelle_combo.addItem(
                texte,
                parcelle["id"],
            )

        self.parcelle_combo.blockSignals(
            False
        )

        if not parcelles:
            self.parcelle_selectionnee = None

            self.parcelle_combo.setEnabled(
                False
            )

            self.ressource_combo.clear()

            self.ressource_combo.setEnabled(
                False
            )

            self.superficie_label.setText(
                "-"
            )

            self.valider_button.setEnabled(
                False
            )

            return

        self.parcelle_combo.setEnabled(
            True
        )

        self.parcelle_combo.setCurrentIndex(
            0
        )

        self.selectionner_parcelle(0)

    def selectionner_parcelle(
        self,
        index,
    ):
        if (
            index < 0
            or self.agriculteur_selectionne
            is None
        ):
            return

        parcelle_id = (
            self.parcelle_combo
            .itemData(index)
        )

        parcelle = None

        for candidate in (
            self.agriculteur_selectionne[
                "parcelles"
            ]
        ):
            if (
                candidate["id"]
                == parcelle_id
            ):
                parcelle = candidate
                break

        if parcelle is None:
            return

        self.parcelle_selectionnee = (
            parcelle
        )

        superficie = (
            f"{parcelle['superficie_m2']:,.0f}"
            .replace(",", " ")
        )

        self.superficie_label.setText(
            f"{superficie} m²"
        )

        self.ressource_combo.clear()

        index_ressource_planning = -1

        for ressource in parcelle[
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
                texte += (
                    f" — {etat}"
                )

            self.ressource_combo.addItem(
                texte,
                ressource_id,
            )

            # Si on vient du planning,
            # rechercher la ressource demandée.
            if (
                self.ressource_planning_id
                is not None
                and
                ressource_id
                == self.ressource_planning_id
            ):
                index_ressource_planning = (
                    self.ressource_combo.count()
                    - 1
                )

        ressources_disponibles = (
            self.ressource_combo.count()
            > 0
        )

        self.ressource_combo.setEnabled(
            ressources_disponibles
        )

        # ---------------------------------
        # Création venant du planning
        # ---------------------------------

        if (
            self.ressource_planning_id
            is not None
        ):
            if (
                index_ressource_planning
                >= 0
            ):
                self.ressource_combo.setCurrentIndex(
                    index_ressource_planning
                )

                self.valider_button.setEnabled(
                    True
                )

            else:
                self.valider_button.setEnabled(
                    False
                )

                QMessageBox.warning(
                    self,
                    "Ressource non autorisée",
                    (
                        f"Cette parcelle ne peut pas "
                        f"être irriguée par "
                        f"{self.ressource_planning_nom}.\n\n"
                        "Choisissez une autre parcelle "
                        "ou revenez au planning."
                    ),
                )

        else:
            self.valider_button.setEnabled(
                ressources_disponibles
            )

    def obtenir_debut_python(self):
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

    def obtenir_duree_minutes(self):
        return (
            self.duree_heures.value()
            * 60
            + self.duree_minutes.value()
        )

    def calculer_fin(self):
        debut = (
            self.obtenir_debut_python()
        )

        duree = (
            self.obtenir_duree_minutes()
        )

        if duree <= 0:
            self.fin_label.setText(
                "Durée invalide"
            )
            return

        from datetime import timedelta

        fin = debut + timedelta(
            minutes=duree
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

    def enregistrer_tour(self):
        if self.parcelle_selectionnee is None:
            QMessageBox.warning(
                self,
                "Parcelle obligatoire",
                "Sélectionnez une parcelle.",
            )
            return

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

        duree = (
            self.obtenir_duree_minutes()
        )

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

        debut = (
            self.obtenir_debut_python()
        )

        remarque = (
            self.remarque_input
            .toPlainText()
            .strip()
            or None
        )

        try:
            tour = creer_tour_eau(
                parcelle_id=(
                    self.parcelle_selectionnee[
                        "id"
                    ]
                ),
                ressource_id=ressource_id,
                date_heure_debut=debut,
                duree_minutes=duree,
                remarque=remarque,
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Impossible de créer le tour",
                str(error),
            )
            return

        dialog = RecuDialog(
            tour_id=tour["id"],
            parent=self,
        )

        dialog.exec()

        self.reinitialiser_apres_creation()

    def reinitialiser_apres_creation(self):
        self.recherche_input.clear()

        self.resultats_combo.clear()

        self.agriculteur_selectionne = None
        self.parcelle_selectionnee = None

        self.agriculteur_info.setText(
            "Aucun agriculteur sélectionné."
        )

        self.parcelle_combo.clear()

        self.parcelle_combo.setEnabled(
            False
        )

        self.ressource_combo.clear()

        self.ressource_combo.setEnabled(
            False
        )

        self.superficie_label.setText("-")

        self.remarque_input.clear()

        self.duree_heures.setValue(1)
        self.duree_minutes.setValue(0)

        self.valider_button.setEnabled(
            False
        )
        self.ressource_planning_id = None
        self.ressource_planning_nom = None
        self.recherche_input.setFocus()