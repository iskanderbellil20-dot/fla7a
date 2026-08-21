from datetime import datetime

from app.services.tour_eau_service import (
    obtenir_tour_eau,
)


def formater_duree(duree_minutes):
    heures = duree_minutes // 60
    minutes = duree_minutes % 60

    if heures and minutes:
        return f"{heures} h {minutes:02d} min"

    if heures:
        return f"{heures} h"

    return f"{minutes} min"


def formater_date_heure(valeur):
    date = datetime.strptime(
        valeur,
        "%Y-%m-%d %H:%M:%S",
    )

    return date.strftime(
        "%d/%m/%Y %H:%M"
    )


def formater_heure(valeur):
    date = datetime.strptime(
        valeur,
        "%Y-%m-%d %H:%M:%S",
    )

    return date.strftime(
        "%H:%M"
    )


def formater_date(valeur):
    date = datetime.strptime(
        valeur,
        "%Y-%m-%d %H:%M:%S",
    )

    return date.strftime(
        "%d/%m/%Y"
    )


def obtenir_donnees_recu(tour_id):
    tour = obtenir_tour_eau(
        tour_id
    )

    if tour is None:
        raise ValueError(
            "Tour d'eau introuvable."
        )

    return {
        "tour_id": tour["id"],
        "numero_recu":
            tour["numero_recu_formate"],

        "nom": tour["nom"],
        "prenom": tour["prenom"],
        "cin": tour["cin"],
        "telephone": tour["telephone"],

        "numero_lot":
            tour["numero_lot"],

        "superficie_m2":
            tour["superficie_m2"],

        "ressource":
            tour["ressource_nom"],

        "date":
            formater_date(
                tour["date_heure_debut"]
            ),

        "heure_debut":
            formater_heure(
                tour["date_heure_debut"]
            ),

        "heure_fin":
            formater_heure(
                tour["date_heure_fin"]
            ),

        "date_fin":
            formater_date(
                tour["date_heure_fin"]
            ),

        "duree":
            formater_duree(
                tour["duree_minutes"]
            ),

        "statut":
            tour["statut"],

        "date_creation":
            formater_date_heure(
                tour["date_creation"]
            ),

        "remarque":
            tour["remarque"],
    }