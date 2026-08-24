from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from app.ui.pages.nouveau_tour_page import (
    NouveauTourPage,
)
from app.ui.pages.accueil_page import AccueilPage
from app.ui.pages.agriculteurs_page import AgriculteursPage
from app.ui.pages.ressources_page import RessourcesPage
from app.ui.pages.planning_page import PlanningPage
from app.ui.pages.historique_page import HistoriquePage
from app.ui.pages.sauvegarde_page import SauvegardePage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gestion des ressources d'eau")
        self.resize(1250, 760)
        self.setMinimumSize(1000, 650)

        self.creer_interface()

    def creer_interface(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout_principal = QHBoxLayout(central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        sidebar = self.creer_sidebar()

        self.pages = QStackedWidget()
        self.pages.setObjectName("contentArea")

        self.accueil_page = AccueilPage()

        self.nouveau_tour_page = (
            NouveauTourPage()
        )

        self.agriculteurs_page = (
            AgriculteursPage()
        )
        self.ressources_page = RessourcesPage()
        self.planning_page = PlanningPage()
        self.planning_page.nouveau_tour_demande.connect(
            self.ouvrir_nouveau_tour_depuis_planning
        )
        self.historique_page = HistoriquePage()
        self.sauvegarde_page = SauvegardePage()

        self.pages.addWidget(
            self.accueil_page
        )

        self.pages.addWidget(
            self.nouveau_tour_page
        )

        self.pages.addWidget(
            self.agriculteurs_page
        )

        self.pages.addWidget(
            self.ressources_page
        )

        self.pages.addWidget(
            self.planning_page
        )

        self.pages.addWidget(
            self.historique_page
        )

        self.pages.addWidget(
            self.sauvegarde_page
        )
        

        layout_principal.addWidget(sidebar)

        layout_principal.addWidget(
            self.pages,
            stretch=1,
        )

        self.pages.setCurrentIndex(0)

    def ouvrir_nouveau_tour_depuis_planning(
        self,
        date_selectionnee,
        heure,
        minute,
        ressource_id,
        ressource_nom,
    ):
        self.nouveau_tour_page.preparer_depuis_planning(
            date_selectionnee=(
                date_selectionnee
            ),
            heure=heure,
            minute=minute,
            ressource_id=ressource_id,
            ressource_nom=ressource_nom,
        )

        # Nouveau tour est la page index 1.
        self.pages.setCurrentIndex(
            1
        )

        # Mettre également le bouton
        # "Nouveau tour d'eau" en surbrillance.
        if (
            len(self.navigation_buttons)
            > 1
        ):
            self.navigation_buttons[
                1
            ].setChecked(True)

    def creer_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)

        layout.setContentsMargins(
            18,
            25,
            18,
            20,
        )

        layout.setSpacing(8)

        titre = QLabel("Gestion Eau")
        titre.setObjectName("appTitle")

        sous_titre = QLabel(
            "Organisation des tours d'eau"
        )
        sous_titre.setObjectName("appSubtitle")

        layout.addWidget(titre)
        layout.addWidget(sous_titre)
        layout.addSpacing(25)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        noms = [
            "Accueil",
            "+ Nouveau tour d'eau",
            "Agriculteurs",
            "Ressources d'eau",
            "Planning",
            "Historique",
            "Sauvegarde",
        ]

        self.navigation_buttons = []

        for index, nom in enumerate(noms):
            bouton = QPushButton(nom)
            bouton.setObjectName("navigationButton")
            bouton.setCheckable(True)

            bouton.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            bouton.clicked.connect(
                lambda checked, i=index:
                self.pages.setCurrentIndex(i)
            )

            self.button_group.addButton(bouton)
            self.navigation_buttons.append(bouton)

            layout.addWidget(bouton)

        self.navigation_buttons[0].setChecked(True)

        layout.addStretch()

        version = QLabel(
            "Version 0.1 - Développement"
        )
        version.setObjectName("appSubtitle")

        layout.addWidget(version)

        return sidebar