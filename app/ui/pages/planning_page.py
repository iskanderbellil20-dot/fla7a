
from datetime import datetime, timedelta

from PySide6.QtCore import (
    QDate,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)
from app.services.indisponibilite_service import (
    lister_indisponibilites_pour_jour,
)

from app.services.ressource_service import (
    lister_ressources,
)

from app.services.tour_eau_service import (
    lister_tours_pour_jour,
)

from app.ui.dialogs.tour_details_dialog import (
    TourDetailsDialog,
)


class PlanningPage(QWidget):
    nouveau_tour_demande = Signal(
        QDate,
        int,
        int,
        int,
        str,
    )

    HEURE_DEBUT = 0
    HEURE_FIN = 24
    MINUTES_PAR_CRENEAU = 30

    def __init__(self):
        super().__init__()

        self.ressources = []
        self.tours = []
        self.indisponibilites = []
        self.ressources_par_colonne = {}

        self.creer_interface()
        self.charger_planning()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            28,
            25,
            28,
            25,
        )

        layout.setSpacing(15)

        titre = QLabel("Planning")
        titre.setObjectName("pageTitle")

        description = QLabel(
            "Planning journalier des tours d'eau "
            "par ressource."
        )

        description.setObjectName(
            "pageDescription"
        )

        layout.addWidget(titre)
        layout.addWidget(description)

        navigation = QHBoxLayout()

        precedent_button = QPushButton(
            "← Jour précédent"
        )

        precedent_button.clicked.connect(
            self.jour_precedent
        )

        self.date_input = QDateEdit()

        self.date_input.setCalendarPopup(True)

        self.date_input.setDisplayFormat(
            "dd/MM/yyyy"
        )

        self.date_input.setDate(
            QDate.currentDate()
        )

        self.date_input.dateChanged.connect(
            self.charger_planning
        )

        aujourd_hui_button = QPushButton(
            "Aujourd'hui"
        )

        aujourd_hui_button.clicked.connect(
            self.aujourd_hui
        )

        suivant_button = QPushButton(
            "Jour suivant →"
        )

        suivant_button.clicked.connect(
            self.jour_suivant
        )

        actualiser_button = QPushButton(
            "Actualiser"
        )

        actualiser_button.clicked.connect(
            self.charger_planning
        )

        navigation.addWidget(
            precedent_button
        )

        navigation.addWidget(
            self.date_input
        )

        navigation.addWidget(
            aujourd_hui_button
        )

        navigation.addWidget(
            suivant_button
        )

        navigation.addStretch()

        navigation.addWidget(
            actualiser_button
        )

        layout.addLayout(navigation)

        self.table = QTableWidget()

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectItems
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.setAlternatingRowColors(
            False
        )

        self.table.cellDoubleClicked.connect(
            self.ouvrir_tour
        )

        layout.addWidget(
            self.table,
            stretch=1,
        )

        aide = QLabel(
            "Double-cliquez sur un tour pour "
            "ouvrir sa fiche et son reçu."
        )

        aide.setObjectName(
            "pageDescription"
        )

        layout.addWidget(aide)

    def date_python(self):
        date = self.date_input.date()

        return datetime(
            date.year(),
            date.month(),
            date.day(),
        )

    def charger_planning(self):
        jour = self.date_python()

        self.ressources = (
            lister_ressources()
        )

        self.tours = (
            lister_tours_pour_jour(
                jour
            )
        )

        self.indisponibilites = (
            lister_indisponibilites_pour_jour(
                jour
            )
        )

        self.construire_tableau()

    def construire_tableau(self):
        ressources_actives = [
            r
            for r in self.ressources
            if r[5] == 1
        ]

        nombre_creneaux = (
            24 * 60
            // self.MINUTES_PAR_CRENEAU
        )

        self.table.clear()

        self.table.setRowCount(
            nombre_creneaux
        )

        self.table.setColumnCount(
            1 + len(ressources_actives)
        )

        # =================================
        # ÉTATS DES RESSOURCES
        # =================================

        libelles_etats = {
            "DISPONIBLE":
                "Disponible",

            "EN_PANNE":
                "EN PANNE",

            "MAINTENANCE":
                "Maintenance",

            "HORS_SERVICE":
                "Hors service",
        }

        # =================================
        # EN-TÊTES
        # =================================

        headers = [
            "Créneau"
        ]

        for ressource in ressources_actives:
            nom = ressource[1]
            etat = ressource[2]

            headers.append(
                (
                    f"{nom}\n"
                    f"{libelles_etats.get(etat, etat)}"
                )
            )

        self.table.setHorizontalHeaderLabels(
            headers
        )

        header = (
            self.table.horizontalHeader()
        )

        header.setMinimumHeight(
            48
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        for colonne in range(
            1,
            self.table.columnCount(),
        ):
            header.setSectionResizeMode(
                colonne,
                QHeaderView.ResizeMode.Stretch,
            )

        # =================================
        # RESSOURCES ↔ COLONNES
        # =================================

        ressource_colonnes = {
            ressource[0]: index + 1
            for index, ressource
            in enumerate(
                ressources_actives
            )
        }

        self.ressources_par_colonne = {
            index + 1: {
                "id": ressource[0],
                "nom": ressource[1],
                "etat": ressource[2],
            }
            for index, ressource
            in enumerate(
                ressources_actives
            )
        }

        # =================================
        # DATE AFFICHÉE
        # =================================

        jour = self.date_python()

        debut_jour = jour.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        fin_jour = (
            debut_jour
            + timedelta(days=1)
        )

        aujourd_hui = datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        date_actuelle_ou_future = (
            debut_jour >= aujourd_hui
        )

        # =================================
        # CRÉER LES CRÉNEAUX
        # =================================

        for row in range(
            nombre_creneaux
        ):
            debut_minutes = (
                row
                * self.MINUTES_PAR_CRENEAU
            )

            fin_minutes = (
                debut_minutes
                + self.MINUTES_PAR_CRENEAU
            )

            debut_heure = (
                debut_minutes
                // 60
            )

            debut_minute = (
                debut_minutes
                % 60
            )

            fin_heure = (
                (
                    fin_minutes
                    // 60
                )
                % 24
            )

            fin_minute = (
                fin_minutes
                % 60
            )

            texte_creneau = (
                f"{debut_heure:02d}:"
                f"{debut_minute:02d}"
                " – "
                f"{fin_heure:02d}:"
                f"{fin_minute:02d}"
            )

            heure_item = QTableWidgetItem(
                texte_creneau
            )

            heure_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            font = heure_item.font()

            if debut_minute == 0:
                font.setBold(
                    True
                )

                heure_item.setBackground(
                    QColor("#e4ece9")
                )

                heure_item.setForeground(
                    QColor("#183b32")
                )

            else:
                heure_item.setForeground(
                    QColor("#667085")
                )

            heure_item.setFont(
                font
            )

            self.table.setItem(
                row,
                0,
                heure_item,
            )

            self.table.setRowHeight(
                row,
                36,
            )

            # =================================
            # VALEUR PAR DÉFAUT DE CHAQUE
            # RESSOURCE
            # =================================

            for colonne, ressource in (
                self.ressources_par_colonne.items()
            ):
                etat = ressource["etat"]

                # -----------------------------
                # Pour aujourd'hui/futur :
                # respecter l'état global.
                # -----------------------------

                if (
                    date_actuelle_ou_future
                    and etat == "EN_PANNE"
                ):
                    item = QTableWidgetItem(
                        "En panne"
                    )

                    item.setBackground(
                        QColor("#f8d7da")
                    )

                    item.setForeground(
                        QColor("#842029")
                    )

                    item.setData(
                        Qt.ItemDataRole.UserRole + 1,
                        "INDISPONIBLE",
                    )

                    item.setToolTip(
                        (
                            f"{ressource['nom']} "
                            "est actuellement en panne."
                        )
                    )

                elif (
                    date_actuelle_ou_future
                    and etat == "MAINTENANCE"
                ):
                    item = QTableWidgetItem(
                        "Maintenance"
                    )

                    item.setBackground(
                        QColor("#ffe5b4")
                    )

                    item.setForeground(
                        QColor("#855400")
                    )

                    item.setData(
                        Qt.ItemDataRole.UserRole + 1,
                        "INDISPONIBLE",
                    )

                    item.setToolTip(
                        (
                            f"{ressource['nom']} "
                            "est actuellement "
                            "en maintenance."
                        )
                    )

                elif (
                    date_actuelle_ou_future
                    and etat == "HORS_SERVICE"
                ):
                    item = QTableWidgetItem(
                        "Hors service"
                    )

                    item.setBackground(
                        QColor("#e2e3e5")
                    )

                    item.setForeground(
                        QColor("#41464b")
                    )

                    item.setData(
                        Qt.ItemDataRole.UserRole + 1,
                        "INDISPONIBLE",
                    )

                    item.setToolTip(
                        (
                            f"{ressource['nom']} "
                            "est hors service."
                        )
                    )

                # -----------------------------
                # Ressource normalement libre
                # -----------------------------

                else:
                    item = QTableWidgetItem(
                        "Libre"
                    )

                    item.setBackground(
                        QColor("#e8f6ec")
                    )

                    item.setForeground(
                        QColor("#3c7650")
                    )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.table.setItem(
                    row,
                    colonne,
                    item,
                )

        # =================================
        # COULEURS ALTERNÉES DES TOURS
        # =================================

        couleurs_reservations = [
            {
                "fond": "#fff2c7",
                "texte": "#795d00",
            },
            {
                "fond": "#dceafa",
                "texte": "#244a73",
            },
        ]

        compteur_par_ressource = {}

        # =================================
        # PLACER LES RÉSERVATIONS
        # =================================

        for tour in self.tours:
            ressource_id = (
                tour["ressource_id"]
            )

            colonne = (
                ressource_colonnes.get(
                    ressource_id
                )
            )

            if colonne is None:
                continue

            debut = datetime.strptime(
                tour[
                    "date_heure_debut"
                ],
                "%Y-%m-%d %H:%M:%S",
            )

            fin = datetime.strptime(
                tour[
                    "date_heure_fin"
                ],
                "%Y-%m-%d %H:%M:%S",
            )

            debut_visible = max(
                debut,
                debut_jour,
            )

            fin_visible = min(
                fin,
                fin_jour,
            )

            index_couleur = (
                compteur_par_ressource.get(
                    ressource_id,
                    0,
                )
                % len(
                    couleurs_reservations
                )
            )

            couleur = (
                couleurs_reservations[
                    index_couleur
                ]
            )

            compteur_par_ressource[
                ressource_id
            ] = (
                compteur_par_ressource.get(
                    ressource_id,
                    0,
                )
                + 1
            )

            nom_lot = (
                tour.get("nom_lot")
                or (
                    "Lot "
                    + str(
                        tour[
                            "numero_lot"
                        ]
                    )
                )
            )

            texte_ligne = (
                f"{tour['prenom']} "
                f"{tour['nom']} "
                f"| {nom_lot}"
            )

            tooltip = (
                f"Reçu N° "
                f"{tour['numero_recu_formate']}\n"
                f"{tour['prenom']} "
                f"{tour['nom']}\n"
                f"{nom_lot} "
                f"(Lot {tour['numero_lot']})\n"
                f"{tour['ressource_nom']}\n"
                f"{debut.strftime('%d/%m/%Y %H:%M')}"
                f" → "
                f"{fin.strftime('%d/%m/%Y %H:%M')}"
            )

            for row in range(
                nombre_creneaux
            ):
                creneau_debut = (
                    debut_jour
                    + timedelta(
                        minutes=(
                            row
                            * self.MINUTES_PAR_CRENEAU
                        )
                    )
                )

                creneau_fin = (
                    creneau_debut
                    + timedelta(
                        minutes=(
                            self.MINUTES_PAR_CRENEAU
                        )
                    )
                )

                chevauchement = (
                    debut_visible
                    < creneau_fin
                    and
                    fin_visible
                    > creneau_debut
                )

                if not chevauchement:
                    continue

                item = QTableWidgetItem(
                    texte_ligne
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    tour["id"],
                )

                item.setToolTip(
                    tooltip
                )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                if (
                    tour["statut"]
                    == "PLANIFIE"
                ):
                    item.setBackground(
                        QColor(
                            couleur["fond"]
                        )
                    )

                    item.setForeground(
                        QColor(
                            couleur["texte"]
                        )
                    )

                elif (
                    tour["statut"]
                    == "INTERROMPU"
                ):
                    item.setBackground(
                        QColor("#ffe0b2")
                    )

                    item.setForeground(
                        QColor("#7a4b00")
                    )

                else:
                    item.setBackground(
                        QColor("#e8eaed")
                    )

                    item.setForeground(
                        QColor("#4b5563")
                    )

                self.table.setItem(
                    row,
                    colonne,
                    item,
                )

        # =================================
        # APPLIQUER LES INDISPONIBILITÉS
        # DATÉES EN DERNIER
        # =================================

        self.appliquer_indisponibilites(
            debut_jour=debut_jour,
            nombre_creneaux=nombre_creneaux,
        )

    def appliquer_indisponibilites(
        self,
        debut_jour,
        nombre_creneaux,
    ):
        types_affichage = {
            "PANNE": {
                "texte": "PANNE",
                "fond": "#f8d7da",
                "couleur": "#842029",
            },

            "MAINTENANCE": {
                "texte": "MAINTENANCE",
                "fond": "#ffe5b4",
                "couleur": "#855400",
            },

            "AUTRE": {
                "texte": "INDISPONIBLE",
                "fond": "#e2e3e5",
                "couleur": "#41464b",
            },
        }

        # Inverser notre mapping :
        # colonne -> ressource
        colonne_par_ressource = {
            information["id"]: colonne
            for colonne, information
            in self.ressources_par_colonne.items()
        }

        for indisponibilite in (
            self.indisponibilites
        ):
            ressource_id = (
                indisponibilite[
                    "ressource_id"
                ]
            )

            colonne = (
                colonne_par_ressource.get(
                    ressource_id
                )
            )

            if colonne is None:
                continue

            debut = datetime.strptime(
                indisponibilite[
                    "date_heure_debut"
                ],
                "%Y-%m-%d %H:%M:%S",
            )

            if (
                indisponibilite[
                    "date_heure_fin"
                ]
                is None
            ):
                fin = (
                    debut_jour
                    + timedelta(days=1)
                )

            else:
                fin = datetime.strptime(
                    indisponibilite[
                        "date_heure_fin"
                    ],
                    "%Y-%m-%d %H:%M:%S",
                )

            configuration = (
                types_affichage.get(
                    indisponibilite[
                        "type"
                    ],
                    types_affichage["AUTRE"],
                )
            )

            for row in range(
                nombre_creneaux
            ):
                creneau_debut = (
                    debut_jour
                    + timedelta(
                        minutes=(
                            row
                            * self.MINUTES_PAR_CRENEAU
                        )
                    )
                )

                creneau_fin = (
                    creneau_debut
                    + timedelta(
                        minutes=(
                            self.MINUTES_PAR_CRENEAU
                        )
                    )
                )

                chevauchement = (
                    debut < creneau_fin
                    and
                    fin > creneau_debut
                )

                if not chevauchement:
                    continue

                item_existant = (
                    self.table.item(
                        row,
                        colonne,
                    )
                )

                # Si un tour existe déjà sur ce
                # créneau, la panne est particulièrement
                # importante : on affiche les deux infos.
                tour_id = None

                if item_existant is not None:
                    tour_id = (
                        item_existant.data(
                            Qt.ItemDataRole.UserRole
                        )
                    )

                if tour_id is not None:
                    texte = (
                        f"{configuration['texte']} ⚠\n"
                        f"{item_existant.text()}"
                    )

                else:
                    texte = (
                        configuration[
                            "texte"
                        ]
                    )

                item = QTableWidgetItem(
                    texte
                )
                item.setData(
                Qt.ItemDataRole.UserRole + 1,
                "INDISPONIBLE",
                )

                # Conserver l'ID du tour si
                # une réservation était déjà présente.
                if tour_id is not None:
                    item.setData(
                        Qt.ItemDataRole.UserRole,
                        tour_id,
                    )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                item.setBackground(
                    QColor(
                        configuration[
                            "fond"
                        ]
                    )
                )

                item.setForeground(
                    QColor(
                        configuration[
                            "couleur"
                        ]
                    )
                )

                motif = (
                    indisponibilite[
                        "motif"
                    ]
                    or "Non précisé"
                )

                tooltip = (
                    f"{configuration['texte']}\n"
                    f"Ressource : "
                    f"{indisponibilite['ressource_nom']}\n"
                    f"Début : "
                    f"{indisponibilite['date_heure_debut']}\n"
                    f"Fin : "
                    f"{indisponibilite['date_heure_fin'] or 'Non déterminée'}\n"
                    f"Motif : {motif}"
                )

                item.setToolTip(
                    tooltip
                )

                self.table.setItem(
                    row,
                    colonne,
                    item,
                )
    def ouvrir_tour(
        self,
        row,
        column,
    ):
        if column == 0:
            return

        item = self.table.item(
            row,
            column,
        )

        if item is None:
            return

        tour_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        type_cellule = item.data(
            Qt.ItemDataRole.UserRole + 1
        )

        # =================================
        # TOUR EXISTANT
        # =================================

        if tour_id is not None:
            dialog = TourDetailsDialog(
                tour_id=tour_id,
                parent=self,
            )

            dialog.exec()

            self.charger_planning()
            return

        # =================================
        # INDISPONIBILITÉ
        # =================================

        if (
            type_cellule
            == "INDISPONIBLE"
        ):
            QMessageBox.information(
                self,
                "Ressource indisponible",
                (
                    "Cette ressource est "
                    "indisponible sur ce créneau."
                ),
            )
            return

        # =================================
        # CRÉNEAU LIBRE
        # =================================

        ressource = (
            self.ressources_par_colonne
            .get(column)
        )

        if ressource is None:
            return

        minutes_totales = (
            row
            * self.MINUTES_PAR_CRENEAU
        )

        heure = (
            minutes_totales
            // 60
        )

        minute = (
            minutes_totales
            % 60
        )

        self.nouveau_tour_demande.emit(
            self.date_input.date(),
            heure,
            minute,
            ressource["id"],
            ressource["nom"],
        )

    def jour_precedent(self):
        nouvelle_date = (
            self.date_input
            .date()
            .addDays(-1)
        )

        self.date_input.setDate(
            nouvelle_date
        )

    def jour_suivant(self):
        nouvelle_date = (
            self.date_input
            .date()
            .addDays(1)
        )

        self.date_input.setDate(
            nouvelle_date
        )

    def aujourd_hui(self):
        self.date_input.setDate(
            QDate.currentDate()
        )