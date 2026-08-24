import random
from datetime import datetime, timedelta

from app.database.connection import get_connection
from app.services.agriculteur_service import (
    creer_agriculteur,
)
from app.services.ressource_service import (
    creer_ressource,
)
from app.services.tour_eau_service import (
    creer_tour_eau,
)


random.seed(42)


NOMS = [
    "Ben Ali",
    "Trabelsi",
    "Gharbi",
    "Mansouri",
    "Jlassi",
    "Ayari",
    "Hamdi",
    "Saidi",
    "Bouazizi",
    "Nasri",
    "Mejri",
    "Khelifi",
    "Abidi",
    "Toumi",
    "Dridi",
    "Haddad",
    "Brahmi",
    "Chebbi",
    "Sassi",
    "Ferjani",
]


PRENOMS = [
    "Mohamed",
    "Ali",
    "Ahmed",
    "Hassen",
    "Amor",
    "Sami",
    "Nabil",
    "Mahmoud",
    "Youssef",
    "Walid",
    "Salah",
    "Fethi",
    "Hatem",
    "Khaled",
    "Ridha",
    "Lotfi",
    "Adel",
    "Mounir",
    "Karim",
    "Noureddine",
]


def nettoyer_donnees_demo():
    connection = get_connection()

    try:
        # Supprimer d'abord l'historique.
        connection.execute(
            "DELETE FROM historique"
        )

        # Supprimer les indisponibilités.
        connection.execute(
            "DELETE FROM indisponibilites"
        )

        # Certains tours reportés pointent vers
        # un autre tour via tour_origine_id.
        # On casse d'abord cette auto-référence.
        connection.execute(
            """
            UPDATE tours_eau
            SET tour_origine_id = NULL
            """
        )

        # Maintenant tous les tours peuvent
        # être supprimés.
        connection.execute(
            "DELETE FROM tours_eau"
        )

        # Relations parcelles ↔ ressources.
        connection.execute(
            "DELETE FROM parcelles_ressources"
        )

        # Parcelles.
        connection.execute(
            "DELETE FROM parcelles"
        )

        # Agriculteurs.
        connection.execute(
            "DELETE FROM agriculteurs"
        )

        # Ressources.
        connection.execute(
            "DELETE FROM ressources_eau"
        )

        # Réinitialiser les compteurs AUTOINCREMENT
        # uniquement pour notre base de développement.
        connection.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name IN (
                'agriculteurs',
                'parcelles',
                'ressources_eau',
                'tours_eau',
                'indisponibilites',
                'historique'
            )
            """
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def creer_ressources_demo():
    ids = []

    for numero in range(1, 9):
        ressource_id = creer_ressource(
            nom=f"Puits {numero}",
            description=(
                f"Ressource de démonstration "
                f"n° {numero}"
            ),
        )

        ids.append(
            ressource_id
        )

    return ids


def creer_agriculteurs_demo(
    ressources_ids,
):
    parcelles_creees = []

    numero_lot = 100

    for index in range(20):
        nom = NOMS[index]
        prenom = PRENOMS[index]

        cin = (
            f"{index + 1:08d}"
        )

        telephone = (
            f"2{index + 1:07d}"
        )

        nombre_parcelles = (
            random.choice(
                [1, 1, 2]
            )
        )

        parcelles = []

        for _ in range(
            nombre_parcelles
        ):
            numero_lot += 1

            superficie = random.choice(
                [
                    2000,
                    3000,
                    5000,
                    7500,
                    10000,
                    12000,
                    15000,
                    20000,
                ]
            )

            nombre_ressources = (
                random.randint(
                    2,
                    4,
                )
            )

            ressources_autorisees = (
                random.sample(
                    ressources_ids,
                    nombre_ressources,
                )
            )

            noms_lots = [
                "Olivier Nord",
                "Olivier Sud",
                "Palmeraie",
                "Parcelle Ouest",
                "Parcelle Est",
                "Jardin",
                "Terrain Haut",
                "Terrain Bas",
                "Ancienne Ferme",
                "Nouvelle Ferme",
            ]

            parcelles.append(
                {
                    "nom_lot":
                        random.choice(
                            noms_lots
                        ),

                    "numero_lot":
                        str(numero_lot),

                    "superficie_m2":
                        superficie,

                    "ressources_ids":
                        ressources_autorisees,

                    "remarque":
                        "Donnée de démonstration",
                }
            )

        agriculteur_id = creer_agriculteur(
            nom=nom,
            prenom=prenom,
            cin=cin,
            telephone=telephone,
            parcelles=parcelles,
            remarque="Agriculteur de démonstration",
        )

        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT id
                FROM parcelles
                WHERE agriculteur_id = ?
                  AND actif = 1
                """,
                (agriculteur_id,),
            ).fetchall()

            parcelles_creees.extend(
                row[0]
                for row in rows
            )

        finally:
            connection.close()

    return parcelles_creees


def obtenir_ressources_parcelle(
    parcelle_id,
):
    connection = get_connection()

    try:
        return [
            row[0]
            for row in connection.execute(
                """
                SELECT ressource_id
                FROM parcelles_ressources
                WHERE parcelle_id = ?
                """,
                (parcelle_id,),
            ).fetchall()
        ]

    finally:
        connection.close()


def creer_planning_demo(
    parcelles_ids,
):
    date_depart = datetime(
        2026,
        8,
        21,
    )

    tours_crees = 0

    for numero_jour in range(15):
        jour = (
            date_depart
            + timedelta(
                days=numero_jour
            )
        )

        # Entre 5 et 10 tentatives
        # de tours par jour.
        nombre_tours = random.randint(
            5,
            10,
        )

        for _ in range(
            nombre_tours
        ):
            parcelle_id = random.choice(
                parcelles_ids
            )

            ressources = (
                obtenir_ressources_parcelle(
                    parcelle_id
                )
            )

            if not ressources:
                continue

            ressource_id = random.choice(
                ressources
            )

            # Début toujours sur 00 ou 30.
            heure = random.randint(
                0,
                21,
            )

            minute = random.choice(
                [0, 30]
            )

            debut = jour.replace(
                hour=heure,
                minute=minute,
                second=0,
                microsecond=0,
            )

            # Durées de démonstration :
            # 1h30 à 6h.
            duree = random.choice(
                [
                    90,
                    120,
                    150,
                    180,
                    210,
                    240,
                    300,
                    360,
                ]
            )

            try:
                creer_tour_eau(
                    parcelle_id=(
                        parcelle_id
                    ),
                    ressource_id=(
                        ressource_id
                    ),
                    date_heure_debut=(
                        debut
                    ),
                    duree_minutes=(
                        duree
                    ),
                    remarque=(
                        "Tour de démonstration"
                    ),
                )

                tours_crees += 1

            except ValueError:
                # Conflit ou créneau impossible :
                # on ignore simplement cette tentative.
                continue

    return tours_crees


def afficher_resume():
    connection = get_connection()

    try:
        agriculteurs = (
            connection.execute(
                """
                SELECT COUNT(*)
                FROM agriculteurs
                WHERE actif = 1
                """
            ).fetchone()[0]
        )

        parcelles = (
            connection.execute(
                """
                SELECT COUNT(*)
                FROM parcelles
                WHERE actif = 1
                """
            ).fetchone()[0]
        )

        ressources = (
            connection.execute(
                """
                SELECT COUNT(*)
                FROM ressources_eau
                WHERE actif = 1
                """
            ).fetchone()[0]
        )

        tours = (
            connection.execute(
                """
                SELECT COUNT(*)
                FROM tours_eau
                """
            ).fetchone()[0]
        )

        print()
        print("===== BASE DEMO =====")
        print(
            f"Agriculteurs : {agriculteurs}"
        )
        print(
            f"Parcelles    : {parcelles}"
        )
        print(
            f"Ressources   : {ressources}"
        )
        print(
            f"Tours        : {tours}"
        )
        print("=====================")

    finally:
        connection.close()


def main():
    print(
        "Nettoyage des données de développement..."
    )

    nettoyer_donnees_demo()

    print(
        "Création des 8 ressources..."
    )

    ressources_ids = (
        creer_ressources_demo()
    )

    print(
        "Création des 20 agriculteurs..."
    )

    parcelles_ids = (
        creer_agriculteurs_demo(
            ressources_ids
        )
    )

    print(
        "Création du planning sur 15 jours..."
    )

    tours_crees = creer_planning_demo(
        parcelles_ids
    )

    print(
        f"{tours_crees} tours créés."
    )

    afficher_resume()


if __name__ == "__main__":
    main()