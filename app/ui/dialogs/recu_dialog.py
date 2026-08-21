from PySide6.QtCore import Qt
from PySide6.QtGui import QTextDocument 
from PySide6.QtPrintSupport import (
    QPrintDialog,
    QPrinter,
)
from PySide6.QtGui import (
    QPageLayout,
    QPageSize,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from app.services.recu_service import (
    obtenir_donnees_recu,
)
from PySide6.QtCore import (
    QMarginsF,
    QSizeF,
)


class RecuDialog(QDialog):
    def __init__(
        self,
        tour_id,
        parent=None,
    ):
        super().__init__(parent)

        self.tour_id = tour_id

        self.setWindowTitle(
            "Reçu du tour d'eau"
        )

        self.resize(500, 720)

        self.creer_interface()
        self.charger_recu()

    def creer_interface(self):
        layout = QVBoxLayout(self)

        self.preview = QTextBrowser()

        self.preview.setOpenExternalLinks(
            False
        )

        layout.addWidget(
            self.preview,
            stretch=1,
        )

        actions = QHBoxLayout()

        actions.addStretch()

        imprimer_button = QPushButton(
            "Imprimer"
        )

        imprimer_button.setObjectName(
            "primaryButton"
        )

        imprimer_button.clicked.connect(
            self.imprimer
        )

        fermer_button = QPushButton(
            "Fermer"
        )

        fermer_button.clicked.connect(
            self.accept
        )

        actions.addWidget(
            imprimer_button
        )

        actions.addWidget(
            fermer_button
        )

        layout.addLayout(actions)

    def charger_recu(self):
        try:
            donnees = obtenir_donnees_recu(
                self.tour_id
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                str(error),
            )
            self.reject()
            return

        superficie = (
            f"{donnees['superficie_m2']:,.0f}"
            .replace(",", " ")
        )

        remarque_html = ""

        if donnees["remarque"]:
            remarque_html = (
                "<div class='line'></div>"
                "<div class='row'>"
                "<span>Remarque</span>"
                f"<strong>{donnees['remarque']}</strong>"
                "</div>"
            )

        html = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 10pt;
                color: #111111;
                margin: 4px;
            }}

            .ticket {{
                width: 72mm;
                margin: 0 auto;
            }}

            .center {{
                text-align: center;
            }}

            .association {{
                font-size: 14pt;
                font-weight: bold;
            }}

            .subtitle {{
                font-size: 9pt;
            }}

            .title {{
                font-size: 13pt;
                font-weight: bold;
                margin-top: 8px;
            }}

            .line {{
                border-top: 1px dashed #333333;
                margin: 8px 0;
            }}

            .row {{
                margin: 4px 0;
            }}

            .big {{
                font-size: 12pt;
                font-weight: bold;
            }}

            .footer {{
                margin-top: 14px;
                text-align: center;
                font-size: 8pt;
            }}
        </style>
        </head>

        <body>

        <div class="ticket">

            <div class="center association">
                Association de gestion de l'eau
            </div>

            <div class="center subtitle">
                Gafsa - Tunisie
            </div>

            <div class="line"></div>

            <div class="center title">
                TOUR D'EAU
            </div>

            <div class="center big">
                Reçu N° {donnees['numero_recu']}
            </div>

            <div class="line"></div>

            <div class="row">
                Agriculteur :
                <strong>
                    {donnees['prenom']} {donnees['nom']}
                </strong>
            </div>

            <div class="row">
                CIN :
                <strong>{donnees['cin']}</strong>
            </div>

            <div class="row">
                Téléphone :
                <strong>{donnees['telephone']}</strong>
            </div>

            <div class="row">
                Lot :
                <strong>{donnees['numero_lot']}</strong>
            </div>

            <div class="row">
                Superficie :
                <strong>{superficie} m²</strong>
            </div>

            <div class="line"></div>

            <div class="row">
                Ressource :
                <strong>{donnees['ressource']}</strong>
            </div>

            <div class="row">
                Date :
                <strong>{donnees['date']}</strong>
            </div>

            <div class="row">
                Début :
                <strong>{donnees['heure_debut']}</strong>
            </div>

            <div class="row">
                Fin :
                <strong>
                    {donnees['date_fin']}
                    {donnees['heure_fin']}
                </strong>
            </div>

            <div class="row">
                Durée :
                <strong>{donnees['duree']}</strong>
            </div>

            {remarque_html}

            <div class="line"></div>

            <div class="center subtitle">
                Enregistré le
                {donnees['date_creation']}
            </div>

            <div class="footer">
                Document généré par Gestion Eau
            </div>

        </div>

        </body>
        </html>
        """

        self.preview.setHtml(html)

        self.html = html

    def imprimer(self):
        printer = QPrinter(
            QPrinter.PrinterMode.HighResolution
        )

        # Papier thermique :
        # largeur réelle 80 mm.
        #
        # La hauteur est volontairement assez grande.
        # L'imprimante thermique avance uniquement
        # selon le contenu imprimé.
        taille_ticket = QPageSize(
            QSizeF(
                80.0,
                200.0,
            ),
            QPageSize.Unit.Millimeter,
            "Ticket 80 mm",
        )

        page_layout = QPageLayout(
            taille_ticket,
            QPageLayout.Orientation.Portrait,
            QMarginsF(
                3.0,
                3.0,
                3.0,
                3.0,
            ),
            QPageLayout.Unit.Millimeter,
        )

        printer.setPageLayout(
            page_layout
        )

        dialog = QPrintDialog(
            printer,
            self,
        )

        dialog.setWindowTitle(
            "Imprimer le reçu 80 mm"
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return

        document = QTextDocument()

        document.setHtml(
            self.html
        )

        document.print_(
            printer
        )