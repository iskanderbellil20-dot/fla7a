import sqlite3
from datetime import datetime, timedelta

from app.database.connection import get_connection


FORMAT_DB = "%Y-%m-%d %H:%M:%S"

STATUTS_BLOQUANTS = (
    "PLANIFIE",
)


def convertir_datetime(valeur, nom_champ):
    if isinstance(valeur, datetime):
        return valeur

    if isinstance(valeur, str):
        try:
            return datetime.strptime(
                valeur,
                FORMAT_DB,
            )
        except ValueError as error:
            raise ValueError(
                f"{nom_champ} doit respecter le format "
                "AAAA-MM-JJ HH:MM:SS."
            ) from error

    raise ValueError(
        f"{nom_champ} est invalide."
    )


def calculer_fin(date_heure_debut, duree_minutes):
    debut = convertir_datetime(
        date_heure_debut,
        "La date/heure de début",
    )

    try:
        duree_minutes = int(duree_minutes)
    except (TypeError, ValueError):
        raise ValueError(
            "La durée doit être exprimée en minutes."
        )

    if duree_minutes <= 0:
        raise ValueError(
            "La durée doit être supérieure à 0 minute."
        )

    fin = debut + timedelta(
        minutes=duree_minutes
    )

    return debut, fin, duree_minutes


def obtenir_prochain_numero_recu(connection):
    row = connection.execute(
        """
        SELECT COALESCE(MAX(numero_recu), 0) + 1
        FROM tours_eau
        """
    ).fetchone()

    return row[0]


def verifier_parcelle_et_ressource(
    connection,
    parcelle_id,
    ressource_id,
):
    row = connection.execute(
        """
        SELECT
            p.id,
            p.numero_lot,
            p.superficie_m2,

            a.id,
            a.nom,
            a.prenom,
            a.cin,

            r.id,
            r.nom,
            r.etat

        FROM parcelles p

        INNER JOIN agriculteurs a
            ON a.id = p.agriculteur_id

        INNER JOIN parcelles_ressources pr
            ON pr.parcelle_id = p.id

        INNER JOIN ressources_eau r
            ON r.id = pr.ressource_id

        WHERE p.id = ?
          AND r.id = ?
          AND p.actif = 1
          AND a.actif = 1
          AND r.actif = 1
        """,
        (
            parcelle_id,
            ressource_id,
        ),
    ).fetchone()

    if row is None:
        raise ValueError(
            "La parcelle ou la ressource est invalide, "
            "archivée, ou cette ressource n'est pas "
            "autorisée pour cette parcelle."
        )

    if row[9] != "DISPONIBLE":
        raise ValueError(
            f"La ressource {row[8]} n'est pas disponible "
            f"(état actuel : {row[9]})."
        )

    return row


def verifier_indisponibilite(
    connection,
    ressource_id,
    debut,
    fin,
):
    debut_db = debut.strftime(FORMAT_DB)
    fin_db = fin.strftime(FORMAT_DB)

    row = connection.execute(
        """
        SELECT
            id,
            type,
            date_heure_debut,
            date_heure_fin,
            motif
        FROM indisponibilites
        WHERE ressource_id = ?
          AND date_heure_debut < ?
          AND (
                date_heure_fin IS NULL
                OR date_heure_fin > ?
          )
        ORDER BY date_heure_debut
        LIMIT 1
        """,
        (
            ressource_id,
            fin_db,
            debut_db,
        ),
    ).fetchone()

    if row is not None:
        raise ValueError(
            "La ressource possède une indisponibilité "
            "sur le créneau demandé."
        )


def rechercher_conflit(
    connection,
    ressource_id,
    debut,
    fin,
    exclure_tour_id=None,
):
    debut_db = debut.strftime(FORMAT_DB)
    fin_db = fin.strftime(FORMAT_DB)

    placeholders = ", ".join(
        "?" for _ in STATUTS_BLOQUANTS
    )

    query = f"""
        SELECT
            t.id,
            t.numero_recu,
            t.date_heure_debut,
            t.date_heure_fin,

            p.numero_lot,

            a.nom,
            a.prenom

        FROM tours_eau t

        INNER JOIN parcelles p
            ON p.id = t.parcelle_id

        INNER JOIN agriculteurs a
            ON a.id = p.agriculteur_id

        WHERE t.ressource_id = ?
          AND t.statut IN ({placeholders})
          AND t.date_heure_debut < ?
          AND t.date_heure_fin > ?
    """

    params = [
        ressource_id,
        *STATUTS_BLOQUANTS,
        fin_db,
        debut_db,
    ]

    if exclure_tour_id is not None:
        query += " AND t.id != ?"
        params.append(exclure_tour_id)

    query += " ORDER BY t.date_heure_debut LIMIT 1"

    return connection.execute(
        query,
        params,
    ).fetchone()


def creer_tour_eau(
    parcelle_id,
    ressource_id,
    date_heure_debut,
    duree_minutes,
    remarque=None,
):
    debut, fin, duree_minutes = calculer_fin(
        date_heure_debut,
        duree_minutes,
    )

    connection = get_connection()

    try:
        informations = verifier_parcelle_et_ressource(
            connection,
            parcelle_id,
            ressource_id,
        )

        verifier_indisponibilite(
            connection,
            ressource_id,
            debut,
            fin,
        )

        conflit = rechercher_conflit(
            connection,
            ressource_id,
            debut,
            fin,
        )

        if conflit is not None:
            numero_recu = conflit[1]
            ancien_debut = conflit[2]
            ancienne_fin = conflit[3]
            lot = conflit[4]
            nom = conflit[5]
            prenom = conflit[6]

            raise ValueError(
                "Conflit de réservation. "
                f"La ressource est déjà réservée par "
                f"{prenom} {nom}, lot {lot}, "
                f"du {ancien_debut} au {ancienne_fin} "
                f"(reçu N° {numero_recu:06d})."
            )

        numero_recu = obtenir_prochain_numero_recu(
            connection
        )

        cursor = connection.execute(
            """
            INSERT INTO tours_eau (
                numero_recu,
                parcelle_id,
                ressource_id,
                date_heure_debut,
                date_heure_fin,
                duree_minutes,
                statut,
                remarque
            )
            VALUES (?, ?, ?, ?, ?, ?, 'PLANIFIE', ?)
            """,
            (
                numero_recu,
                parcelle_id,
                ressource_id,
                debut.strftime(FORMAT_DB),
                fin.strftime(FORMAT_DB),
                duree_minutes,
                remarque,
            ),
        )

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "numero_recu": numero_recu,
            "numero_recu_formate": f"{numero_recu:06d}",

            "parcelle_id": parcelle_id,
            "numero_lot": informations[1],
            "superficie_m2": informations[2],

            "agriculteur_id": informations[3],
            "nom": informations[4],
            "prenom": informations[5],
            "cin": informations[6],

            "ressource_id": informations[7],
            "ressource_nom": informations[8],

            "date_heure_debut": debut.strftime(
                FORMAT_DB
            ),
            "date_heure_fin": fin.strftime(
                FORMAT_DB
            ),

            "duree_minutes": duree_minutes,
            "statut": "PLANIFIE",
        }

    except sqlite3.IntegrityError as error:
        connection.rollback()
        raise ValueError(
            "Impossible d'enregistrer le tour d'eau."
        ) from error

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()