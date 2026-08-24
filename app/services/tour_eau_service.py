import sqlite3
from datetime import datetime, timedelta
from app.services.historique_service import enregistrer_historique
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
            p.nom_lot,
            p.superficie_m2,

            a.id,
            a.nom,
            a.prenom,
            a.cin,
            a.telephone,

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

    if row[11] != "DISPONIBLE":
        raise ValueError(
            f"La ressource {row[10]} "
            "n'est pas disponible "
            f"(état actuel : {row[11]})."
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
    debut, fin, duree_minutes = (
        calculer_fin(
            date_heure_debut,
            duree_minutes,
        )
    )

    connection = get_connection()

    try:
        informations = (
            verifier_parcelle_et_ressource(
                connection,
                parcelle_id,
                ressource_id,
            )
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
            raise ValueError(
                "Conflit de réservation. "
                f"La ressource est déjà réservée "
                f"du {conflit[2]} au {conflit[3]} "
                f"(reçu N° {conflit[1]:06d})."
            )

        numero_recu = (
            obtenir_prochain_numero_recu(
                connection
            )
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
                remarque,

                nom_agriculteur_snapshot,
                prenom_agriculteur_snapshot,
                cin_snapshot,
                telephone_snapshot,

                numero_lot_snapshot,
                nom_lot_snapshot,
                superficie_m2_snapshot,

                ressource_nom_snapshot
            )
            VALUES (
                ?, ?, ?,
                ?, ?, ?,
                'PLANIFIE', ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?
            )
            """,
            (
                numero_recu,
                parcelle_id,
                ressource_id,

                debut.strftime(FORMAT_DB),
                fin.strftime(FORMAT_DB),
                duree_minutes,

                remarque,

                informations[5],
                informations[6],
                informations[7],
                informations[8],

                informations[1],
                informations[2],
                informations[3],

                informations[10],
            ),
        )

        connection.commit()

        return {
            "id":
                cursor.lastrowid,

            "numero_recu":
                numero_recu,

            "numero_recu_formate":
                f"{numero_recu:06d}",

            "parcelle_id":
                parcelle_id,

            "numero_lot":
                informations[1],

            "nom_lot":
                informations[2],

            "superficie_m2":
                informations[3],

            "agriculteur_id":
                informations[4],

            "nom":
                informations[5],

            "prenom":
                informations[6],

            "cin":
                informations[7],

            "telephone":
                informations[8],

            "ressource_id":
                informations[9],

            "ressource_nom":
                informations[10],

            "date_heure_debut":
                debut.strftime(
                    FORMAT_DB
                ),

            "date_heure_fin":
                fin.strftime(
                    FORMAT_DB
                ),

            "duree_minutes":
                duree_minutes,

            "statut":
                "PLANIFIE",

            "remarque":
                remarque,
        }

    except sqlite3.IntegrityError as error:
        connection.rollback()

        raise ValueError(
            "Impossible d'enregistrer "
            "le tour d'eau."
        ) from error

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()



def obtenir_tour_eau(
    tour_id,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                t.id,
                t.numero_recu,

                t.parcelle_id,
                t.ressource_id,

                t.date_heure_debut,
                t.date_heure_fin,
                t.duree_minutes,

                t.statut,
                t.remarque,

                t.nom_agriculteur_snapshot,
                t.prenom_agriculteur_snapshot,
                t.cin_snapshot,
                t.telephone_snapshot,

                t.numero_lot_snapshot,
                t.nom_lot_snapshot,
                t.superficie_m2_snapshot,

                t.ressource_nom_snapshot,

                t.date_creation,
                t.date_modification,

                t.tour_origine_id

            FROM tours_eau t

            WHERE t.id = ?
            """,
            (tour_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "id":
                row[0],

            "numero_recu":
                row[1],

            "numero_recu_formate":
                f"{row[1]:06d}",

            "parcelle_id":
                row[2],

            "ressource_id":
                row[3],

            "date_heure_debut":
                row[4],

            "date_heure_fin":
                row[5],

            "duree_minutes":
                row[6],

            "statut":
                row[7],

            "remarque":
                row[8],

            "nom":
                row[9],

            "prenom":
                row[10],

            "cin":
                row[11],

            "telephone":
                row[12],

            "numero_lot":
                row[13],

            "nom_lot":
                row[14],

            "superficie_m2":
                row[15],

            "ressource_nom":
                row[16],

            "date_creation":
                row[17],

            "date_modification":
                row[18],

            "tour_origine_id":
                row[19],
        }

    finally:
        connection.close()

def annuler_tour_eau(
    tour_id,
    motif=None,
):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                numero_recu,
                statut,
                date_heure_debut,
                date_heure_fin,
                ressource_id,
                parcelle_id,
                remarque
            FROM tours_eau
            WHERE id = ?
            """,
            (tour_id,),
        ).fetchone()

        if row is None:
            raise ValueError(
                "Tour d'eau introuvable."
            )

        if row[2] == "ANNULE":
            raise ValueError(
                "Ce tour est déjà annulé."
            )

        if row[2] == "REPORTE":
            raise ValueError(
                "Ce tour a déjà été reporté."
            )

        ancien = {
            "numero_recu": row[1],
            "statut": row[2],
            "date_heure_debut": row[3],
            "date_heure_fin": row[4],
            "ressource_id": row[5],
            "parcelle_id": row[6],
            "remarque": row[7],
        }

        connection.execute(
            """
            UPDATE tours_eau
            SET
                statut = 'ANNULE',
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (tour_id,),
        )

        nouveau = ancien.copy()
        nouveau["statut"] = "ANNULE"

        enregistrer_historique(
            connection=connection,
            type_objet="TOUR_EAU",
            objet_id=tour_id,
            action="ANNULATION",
            ancienne_valeur=ancien,
            nouvelle_valeur=nouveau,
            motif=motif,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def modifier_tour_eau(
    tour_id,
    parcelle_id,
    ressource_id,
    date_heure_debut,
    duree_minutes,
    remarque=None,
    motif=None,
):
    debut, fin, duree_minutes = calculer_fin(
        date_heure_debut,
        duree_minutes,
    )

    connection = get_connection()

    try:
        ancien_row = connection.execute(
            """
            SELECT
                numero_recu,
                parcelle_id,
                ressource_id,
                date_heure_debut,
                date_heure_fin,
                duree_minutes,
                statut,
                remarque,

                nom_agriculteur_snapshot,
                prenom_agriculteur_snapshot,
                cin_snapshot,
                telephone_snapshot,
                numero_lot_snapshot,
                nom_lot_snapshot,
                superficie_m2_snapshot,
                ressource_nom_snapshot

            FROM tours_eau
            WHERE id = ?
            """,
            (tour_id,),
        ).fetchone()

        if ancien_row is None:
            raise ValueError(
                "Tour d'eau introuvable."
            )

        if ancien_row[6] != "PLANIFIE":
            raise ValueError(
                "Seul un tour planifié "
                "peut être modifié."
            )

        # Informations actuelles correctes
        # de la parcelle + ressource.
        informations = (
            verifier_parcelle_et_ressource(
                connection,
                parcelle_id,
                ressource_id,
            )
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
            exclure_tour_id=tour_id,
        )

        if conflit is not None:
            raise ValueError(
                "Impossible de modifier ce tour : "
                "le nouveau créneau est déjà occupé."
            )

        ancienne_valeur = {
            "numero_recu": ancien_row[0],
            "parcelle_id": ancien_row[1],
            "ressource_id": ancien_row[2],
            "date_heure_debut": ancien_row[3],
            "date_heure_fin": ancien_row[4],
            "duree_minutes": ancien_row[5],
            "statut": ancien_row[6],
            "remarque": ancien_row[7],

            "nom":
                ancien_row[8],

            "prenom":
                ancien_row[9],

            "cin":
                ancien_row[10],

            "telephone":
                ancien_row[11],

            "numero_lot":
                ancien_row[12],

            "nom_lot":
                ancien_row[13],

            "superficie_m2":
                ancien_row[14],

            "ressource_nom":
                ancien_row[15],
        }

        # ---------------------------------
        # IMPORTANT :
        # index après V7
        #
        # 1 numero_lot
        # 2 nom_lot
        # 3 superficie
        # 5 nom
        # 6 prénom
        # 7 CIN
        # 8 téléphone
        # 10 nom ressource
        # ---------------------------------

        connection.execute(
            """
            UPDATE tours_eau
            SET
                parcelle_id = ?,
                ressource_id = ?,

                date_heure_debut = ?,
                date_heure_fin = ?,
                duree_minutes = ?,

                remarque = ?,

                nom_agriculteur_snapshot = ?,
                prenom_agriculteur_snapshot = ?,
                cin_snapshot = ?,
                telephone_snapshot = ?,

                numero_lot_snapshot = ?,
                nom_lot_snapshot = ?,
                superficie_m2_snapshot = ?,

                ressource_nom_snapshot = ?,

                date_modification =
                    CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                parcelle_id,
                ressource_id,

                debut.strftime(FORMAT_DB),
                fin.strftime(FORMAT_DB),
                duree_minutes,

                remarque,

                informations[5],
                informations[6],
                informations[7],
                informations[8],

                informations[1],
                informations[2],
                informations[3],

                informations[10],

                tour_id,
            ),
        )

        nouvelle_valeur = {
            "numero_recu":
                ancien_row[0],

            "parcelle_id":
                parcelle_id,

            "ressource_id":
                ressource_id,

            "date_heure_debut":
                debut.strftime(
                    FORMAT_DB
                ),

            "date_heure_fin":
                fin.strftime(
                    FORMAT_DB
                ),

            "duree_minutes":
                duree_minutes,

            "statut":
                "PLANIFIE",

            "remarque":
                remarque,

            "nom":
                informations[5],

            "prenom":
                informations[6],

            "cin":
                informations[7],

            "telephone":
                informations[8],

            "numero_lot":
                informations[1],

            "nom_lot":
                informations[2],

            "superficie_m2":
                informations[3],

            "ressource_nom":
                informations[10],
        }

        enregistrer_historique(
            connection=connection,
            type_objet="TOUR_EAU",
            objet_id=tour_id,
            action="MODIFICATION",
            ancienne_valeur=(
                ancienne_valeur
            ),
            nouvelle_valeur=(
                nouvelle_valeur
            ),
            motif=motif,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def reporter_tour_eau(
    tour_id,
    nouvelle_ressource_id,
    nouvelle_date_heure_debut,
    nouvelle_duree_minutes,
    motif=None,
    remarque=None,
):
    debut, fin, duree_minutes = calculer_fin(
        nouvelle_date_heure_debut,
        nouvelle_duree_minutes,
    )

    connection = get_connection()

    try:
        ancien_row = connection.execute(
            """
            SELECT
                id,
                numero_recu,
                parcelle_id,
                ressource_id,
                date_heure_debut,
                date_heure_fin,
                duree_minutes,
                statut,
                remarque
            FROM tours_eau
            WHERE id = ?
            """,
            (tour_id,),
        ).fetchone()

        if ancien_row is None:
            raise ValueError(
                "Tour d'eau introuvable."
            )

        if ancien_row[7] != "PLANIFIE":
            raise ValueError(
                "Seul un tour planifié "
                "peut être reporté."
            )

        parcelle_id = ancien_row[2]

        informations = (
            verifier_parcelle_et_ressource(
                connection,
                parcelle_id,
                nouvelle_ressource_id,
            )
        )

        verifier_indisponibilite(
            connection,
            nouvelle_ressource_id,
            debut,
            fin,
        )

        conflit = rechercher_conflit(
            connection,
            nouvelle_ressource_id,
            debut,
            fin,
            exclure_tour_id=tour_id,
        )

        if conflit is not None:
            raise ValueError(
                "Impossible de reporter ce tour : "
                "le nouveau créneau est déjà occupé."
            )

        nouveau_numero_recu = (
            obtenir_prochain_numero_recu(
                connection
            )
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
                remarque,

                tour_origine_id,

                nom_agriculteur_snapshot,
                prenom_agriculteur_snapshot,
                cin_snapshot,
                telephone_snapshot,

                numero_lot_snapshot,
                nom_lot_snapshot,
                superficie_m2_snapshot,

                ressource_nom_snapshot
            )
            VALUES (
                ?, ?, ?,
                ?, ?, ?,
                'PLANIFIE', ?,
                ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?
            )
            """,
            (
                nouveau_numero_recu,
                parcelle_id,
                nouvelle_ressource_id,

                debut.strftime(FORMAT_DB),
                fin.strftime(FORMAT_DB),
                duree_minutes,

                remarque,

                tour_id,

                informations[5],
                informations[6],
                informations[7],
                informations[8],

                informations[1],
                informations[2],
                informations[3],

                informations[10],
            ),
        )

        nouveau_tour_id = (
            cursor.lastrowid
        )

        connection.execute(
            """
            UPDATE tours_eau
            SET
                statut = 'REPORTE',
                date_modification =
                    CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (tour_id,),
        )

        ancien = {
            "numero_recu":
                ancien_row[1],

            "parcelle_id":
                ancien_row[2],

            "ressource_id":
                ancien_row[3],

            "date_heure_debut":
                ancien_row[4],

            "date_heure_fin":
                ancien_row[5],

            "duree_minutes":
                ancien_row[6],

            "statut":
                ancien_row[7],

            "remarque":
                ancien_row[8],
        }

        nouveau = {
            "tour_id":
                nouveau_tour_id,

            "numero_recu":
                nouveau_numero_recu,

            "parcelle_id":
                parcelle_id,

            "ressource_id":
                nouvelle_ressource_id,

            "date_heure_debut":
                debut.strftime(
                    FORMAT_DB
                ),

            "date_heure_fin":
                fin.strftime(
                    FORMAT_DB
                ),

            "duree_minutes":
                duree_minutes,

            "statut":
                "PLANIFIE",

            "remarque":
                remarque,

            "tour_origine_id":
                tour_id,

            "nom_lot":
                informations[2],

            "superficie_m2":
                informations[3],

            "ressource_nom":
                informations[10],
        }

        enregistrer_historique(
            connection=connection,
            type_objet="TOUR_EAU",
            objet_id=tour_id,
            action="REPORT",
            ancienne_valeur=ancien,
            nouvelle_valeur=nouveau,
            motif=motif,
        )

        enregistrer_historique(
            connection=connection,
            type_objet="TOUR_EAU",
            objet_id=nouveau_tour_id,
            action="CREATION_PAR_REPORT",
            ancienne_valeur=None,
            nouvelle_valeur=nouveau,
            motif=motif,
        )

        connection.commit()

        return {
            "ancien_tour_id":
                tour_id,

            "ancien_numero_recu":
                ancien_row[1],

            "nouveau_tour_id":
                nouveau_tour_id,

            "nouveau_numero_recu":
                nouveau_numero_recu,

            "nouveau_numero_recu_formate":
                f"{nouveau_numero_recu:06d}",
        }

    except sqlite3.IntegrityError as error:
        connection.rollback()

        raise ValueError(
            "Impossible d'enregistrer "
            "le report du tour d'eau."
        ) from error

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def lister_tours_pour_jour(
    date_jour,
):
    if isinstance(
        date_jour,
        str,
    ):
        try:
            jour = datetime.strptime(
                date_jour,
                "%Y-%m-%d",
            )
        except ValueError as error:
            raise ValueError(
                "La date doit respecter "
                "le format AAAA-MM-JJ."
            ) from error

    elif isinstance(
        date_jour,
        datetime,
    ):
        jour = date_jour

    else:
        raise ValueError(
            "Date du planning invalide."
        )

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

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                t.id,
                t.numero_recu,

                t.ressource_id,
                t.ressource_nom_snapshot,

                t.parcelle_id,
                t.numero_lot_snapshot,
                t.nom_lot_snapshot,
                t.superficie_m2_snapshot,

                t.nom_agriculteur_snapshot,
                t.prenom_agriculteur_snapshot,
                t.cin_snapshot,

                t.date_heure_debut,
                t.date_heure_fin,
                t.duree_minutes,

                t.statut,
                t.remarque

            FROM tours_eau t

            WHERE t.date_heure_debut < ?
              AND t.date_heure_fin > ?
              AND t.statut != 'ANNULE'
              AND t.statut != 'REPORTE'

            ORDER BY
                t.ressource_id,
                t.date_heure_debut
            """,
            (
                fin_jour.strftime(
                    FORMAT_DB
                ),
                debut_jour.strftime(
                    FORMAT_DB
                ),
            ),
        ).fetchall()

        resultat = []

        for row in rows:
            resultat.append(
                {
                    "id":
                        row[0],

                    "numero_recu":
                        row[1],

                    "numero_recu_formate":
                        f"{row[1]:06d}",

                    "ressource_id":
                        row[2],

                    "ressource_nom":
                        row[3],

                    "parcelle_id":
                        row[4],

                    "numero_lot":
                        row[5],

                    "nom_lot":
                        row[6],

                    "superficie_m2":
                        row[7],

                    "nom":
                        row[8],

                    "prenom":
                        row[9],

                    "cin":
                        row[10],

                    "date_heure_debut":
                        row[11],

                    "date_heure_fin":
                        row[12],

                    "duree_minutes":
                        row[13],

                    "statut":
                        row[14],

                    "remarque":
                        row[15],
                }
            )

        return resultat

    finally:
        connection.close()