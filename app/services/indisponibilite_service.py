from datetime import datetime

from app.database.connection import get_connection
from app.services.tour_eau_service import FORMAT_DB


TYPES_INDISPONIBILITE = (
    "PANNE",
    "MAINTENANCE",
    "AUTRE",
)


def convertir_date(valeur, nom_champ):
    if valeur is None:
        return None

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


def creer_indisponibilite(
    ressource_id,
    type_indisponibilite,
    date_heure_debut,
    date_heure_fin=None,
    motif=None,
    remarque=None,
):
    if type_indisponibilite not in TYPES_INDISPONIBILITE:
        raise ValueError(
            "Type d'indisponibilité invalide."
        )

    debut = convertir_date(
        date_heure_debut,
        "La date/heure de début",
    )

    fin = convertir_date(
        date_heure_fin,
        "La date/heure de fin",
    )

    if fin is not None and fin <= debut:
        raise ValueError(
            "La date/heure de fin doit être "
            "postérieure au début."
        )

    connection = get_connection()

    try:
        ressource = connection.execute(
            """
            SELECT
                id,
                nom,
                actif
            FROM ressources_eau
            WHERE id = ?
            """,
            (ressource_id,),
        ).fetchone()

        if ressource is None:
            raise ValueError(
                "Ressource d'eau introuvable."
            )

        if ressource[2] == 0:
            raise ValueError(
                "Impossible de créer une indisponibilité "
                "pour une ressource archivée."
            )

        # Vérifier qu'une autre indisponibilité
        # ne chevauche pas la nouvelle.
        if fin is None:
            conflit = connection.execute(
                """
                SELECT id
                FROM indisponibilites
                WHERE ressource_id = ?
                  AND (
                        date_heure_fin IS NULL
                        OR date_heure_fin > ?
                  )
                LIMIT 1
                """,
                (
                    ressource_id,
                    debut.strftime(FORMAT_DB),
                ),
            ).fetchone()

        else:
            conflit = connection.execute(
                """
                SELECT id
                FROM indisponibilites
                WHERE ressource_id = ?
                  AND date_heure_debut < ?
                  AND (
                        date_heure_fin IS NULL
                        OR date_heure_fin > ?
                  )
                LIMIT 1
                """,
                (
                    ressource_id,
                    fin.strftime(FORMAT_DB),
                    debut.strftime(FORMAT_DB),
                ),
            ).fetchone()

        if conflit is not None:
            raise ValueError(
                "Une indisponibilité existe déjà "
                "sur cette période."
            )

        cursor = connection.execute(
            """
            INSERT INTO indisponibilites (
                ressource_id,
                type,
                date_heure_debut,
                date_heure_fin,
                motif,
                remarque
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ressource_id,
                type_indisponibilite,
                debut.strftime(FORMAT_DB),
                (
                    fin.strftime(FORMAT_DB)
                    if fin is not None
                    else None
                ),
                motif,
                remarque,
            ),
        )

        # Si l'indisponibilité est ouverte,
        # on synchronise aussi l'état actuel.
        if fin is None:
            if type_indisponibilite == "PANNE":
                nouvel_etat = "EN_PANNE"
            elif type_indisponibilite == "MAINTENANCE":
                nouvel_etat = "MAINTENANCE"
            else:
                nouvel_etat = "HORS_SERVICE"

            connection.execute(
                """
                UPDATE ressources_eau
                SET
                    etat = ?,
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    nouvel_etat,
                    ressource_id,
                ),
            )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def terminer_indisponibilite(
    indisponibilite_id,
    date_heure_fin,
):
    fin = convertir_date(
        date_heure_fin,
        "La date/heure de fin",
    )

    connection = get_connection()

    try:
        indisponibilite = connection.execute(
            """
            SELECT
                id,
                ressource_id,
                date_heure_debut,
                date_heure_fin
            FROM indisponibilites
            WHERE id = ?
            """,
            (indisponibilite_id,),
        ).fetchone()

        if indisponibilite is None:
            raise ValueError(
                "Indisponibilité introuvable."
            )

        if indisponibilite[3] is not None:
            raise ValueError(
                "Cette indisponibilité est déjà terminée."
            )

        debut = datetime.strptime(
            indisponibilite[2],
            FORMAT_DB,
        )

        if fin <= debut:
            raise ValueError(
                "La fin doit être postérieure au début."
            )

        connection.execute(
            """
            UPDATE indisponibilites
            SET date_heure_fin = ?
            WHERE id = ?
            """,
            (
                fin.strftime(FORMAT_DB),
                indisponibilite_id,
            ),
        )

        # La ressource redevient disponible.
        connection.execute(
            """
            UPDATE ressources_eau
            SET
                etat = 'DISPONIBLE',
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (indisponibilite[1],),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def lister_indisponibilites(
    ressource_id=None,
    seulement_ouvertes=False,
):
    connection = get_connection()

    try:
        query = """
            SELECT
                i.id,
                i.ressource_id,
                r.nom,
                i.type,
                i.date_heure_debut,
                i.date_heure_fin,
                i.motif,
                i.remarque
            FROM indisponibilites i

            INNER JOIN ressources_eau r
                ON r.id = i.ressource_id

            WHERE 1 = 1
        """

        params = []

        if ressource_id is not None:
            query += " AND i.ressource_id = ?"
            params.append(ressource_id)

        if seulement_ouvertes:
            query += " AND i.date_heure_fin IS NULL"

        query += """
            ORDER BY
                i.date_heure_debut DESC
        """

        return connection.execute(
            query,
            params,
        ).fetchall()

    finally:
        connection.close()

def rechercher_tours_impactes(
    ressource_id,
    date_heure_debut,
    date_heure_fin=None,
):
    debut = convertir_date(
        date_heure_debut,
        "La date/heure de début",
    )

    fin = convertir_date(
        date_heure_fin,
        "La date/heure de fin",
    )

    connection = get_connection()

    try:
        query = """
            SELECT
                t.id,
                t.numero_recu,

                t.date_heure_debut,
                t.date_heure_fin,
                t.duree_minutes,

                p.id,
                p.numero_lot,
                p.superficie_m2,

                a.id,
                a.nom,
                a.prenom,
                a.cin,
                a.telephone,

                r.id,
                r.nom

            FROM tours_eau t

            INNER JOIN parcelles p
                ON p.id = t.parcelle_id

            INNER JOIN agriculteurs a
                ON a.id = p.agriculteur_id

            INNER JOIN ressources_eau r
                ON r.id = t.ressource_id

            WHERE t.ressource_id = ?
              AND t.statut = 'PLANIFIE'
              AND t.date_heure_fin > ?
        """

        params = [
            ressource_id,
            debut.strftime(FORMAT_DB),
        ]

        if fin is not None:
            query += """
                AND t.date_heure_debut < ?
            """
            params.append(
                fin.strftime(FORMAT_DB)
            )

        query += """
            ORDER BY t.date_heure_debut
        """

        rows = connection.execute(
            query,
            params,
        ).fetchall()

        resultat = []

        for row in rows:
            resultat.append(
                {
                    "tour_id": row[0],
                    "numero_recu": row[1],
                    "numero_recu_formate":
                        f"{row[1]:06d}",

                    "date_heure_debut": row[2],
                    "date_heure_fin": row[3],
                    "duree_minutes": row[4],

                    "parcelle_id": row[5],
                    "numero_lot": row[6],
                    "superficie_m2": row[7],

                    "agriculteur_id": row[8],
                    "nom": row[9],
                    "prenom": row[10],
                    "cin": row[11],
                    "telephone": row[12],

                    "ressource_id": row[13],
                    "ressource_nom": row[14],
                }
            )

        return resultat

    finally:
        connection.close()