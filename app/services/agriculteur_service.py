import sqlite3

from app.database.connection import get_connection


def valider_cin(cin):
    cin = cin.strip()

    if len(cin) != 8 or not cin.isdigit():
        raise ValueError(
            "Le CIN doit contenir exactement 8 chiffres."
        )

    return cin


def valider_agriculteur(nom, prenom, cin, telephone):
    nom = nom.strip()
    prenom = prenom.strip()
    cin = valider_cin(cin)
    telephone = telephone.strip()

    if not nom:
        raise ValueError("Le nom est obligatoire.")

    if not prenom:
        raise ValueError("Le prénom est obligatoire.")

    if not telephone:
        raise ValueError("Le téléphone est obligatoire.")

    return nom, prenom, cin, telephone


def valider_parcelles(parcelles):
    if not parcelles:
        raise ValueError(
            "L'agriculteur doit avoir au moins une parcelle."
        )

    numeros_lots = set()

    for parcelle in parcelles:
        numero_lot = str(
            parcelle.get("numero_lot", "")
        ).strip()

        if not numero_lot:
            raise ValueError(
                "Le numéro du lot est obligatoire."
            )

        if numero_lot in numeros_lots:
            raise ValueError(
                f"Le lot {numero_lot} est présent plusieurs fois."
            )

        numeros_lots.add(numero_lot)

        try:
            superficie = float(
                parcelle.get("superficie_m2", 0)
            )
        except (TypeError, ValueError):
            raise ValueError(
                f"La superficie du lot {numero_lot} est invalide."
            )

        if superficie <= 0:
            raise ValueError(
                f"La superficie du lot {numero_lot} doit être supérieure à 0."
            )

        ressources = parcelle.get("ressources_ids", [])

        if not ressources:
            raise ValueError(
                f"Le lot {numero_lot} doit avoir au moins une ressource d'eau."
            )


def verifier_ressources(connection, ressources_ids):
    ressources_uniques = set(ressources_ids)

    for ressource_id in ressources_uniques:
        row = connection.execute(
            """
            SELECT id
            FROM ressources_eau
            WHERE id = ?
              AND actif = 1
            """,
            (ressource_id,),
        ).fetchone()

        if row is None:
            raise ValueError(
                f"La ressource d'eau ID {ressource_id} "
                "n'existe pas ou est archivée."
            )


def creer_agriculteur(
    nom,
    prenom,
    cin,
    telephone,
    parcelles,
    remarque=None,
):
    nom, prenom, cin, telephone = valider_agriculteur(
        nom,
        prenom,
        cin,
        telephone,
    )

    valider_parcelles(parcelles)

    connection = get_connection()

    try:
        toutes_ressources = []

        for parcelle in parcelles:
            toutes_ressources.extend(
                parcelle.get("ressources_ids", [])
            )

        verifier_ressources(
            connection,
            toutes_ressources,
        )

        cursor = connection.execute(
            """
            INSERT INTO agriculteurs (
                nom,
                prenom,
                cin,
                telephone,
                remarque
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                nom,
                prenom,
                cin,
                telephone,
                remarque,
            ),
        )

        agriculteur_id = cursor.lastrowid

        for parcelle in parcelles:
            numero_lot = str(
                parcelle["numero_lot"]
            ).strip()

            superficie = float(
                parcelle["superficie_m2"]
            )

            remarque_parcelle = parcelle.get(
                "remarque"
            )

            cursor = connection.execute(
                """
                INSERT INTO parcelles (
                    agriculteur_id,
                    numero_lot,
                    superficie_m2,
                    remarque
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    agriculteur_id,
                    numero_lot,
                    superficie,
                    remarque_parcelle,
                ),
            )

            parcelle_id = cursor.lastrowid

            ressources_ids = set(
                parcelle.get("ressources_ids", [])
            )

            for ressource_id in ressources_ids:
                connection.execute(
                    """
                    INSERT INTO parcelles_ressources (
                        parcelle_id,
                        ressource_id
                    )
                    VALUES (?, ?)
                    """,
                    (
                        parcelle_id,
                        ressource_id,
                    ),
                )

        connection.commit()

        return agriculteur_id

    except sqlite3.IntegrityError as error:
        connection.rollback()

        message = str(error)

        if "agriculteurs.cin" in message:
            raise ValueError(
                "Un agriculteur avec ce CIN existe déjà."
            ) from error

        if "parcelles.numero_lot" in message:
            raise ValueError(
                "Un lot avec ce numéro existe déjà."
            ) from error

        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def lister_agriculteurs(inclure_archives=False):
    connection = get_connection()

    try:
        if inclure_archives:
            rows = connection.execute(
                """
                SELECT
                    id,
                    nom,
                    prenom,
                    cin,
                    telephone,
                    actif
                FROM agriculteurs
                ORDER BY nom, prenom
                """
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT
                    id,
                    nom,
                    prenom,
                    cin,
                    telephone,
                    actif
                FROM agriculteurs
                WHERE actif = 1
                ORDER BY nom, prenom
                """
            ).fetchall()

        return rows

    finally:
        connection.close()


def obtenir_agriculteur(agriculteur_id):
    connection = get_connection()

    try:
        agriculteur = connection.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                cin,
                telephone,
                remarque,
                actif,
                date_creation,
                date_modification
            FROM agriculteurs
            WHERE id = ?
            """,
            (agriculteur_id,),
        ).fetchone()

        if agriculteur is None:
            return None

        parcelles_rows = connection.execute(
            """
            SELECT
                id,
                numero_lot,
                superficie_m2,
                remarque,
                actif
            FROM parcelles
            WHERE agriculteur_id = ?
            ORDER BY numero_lot
            """,
            (agriculteur_id,),
        ).fetchall()

        parcelles = []

        for parcelle in parcelles_rows:
            ressources = connection.execute(
                """
                SELECT
                    r.id,
                    r.nom,
                    r.etat,
                    r.actif
                FROM ressources_eau r
                INNER JOIN parcelles_ressources pr
                    ON pr.ressource_id = r.id
                WHERE pr.parcelle_id = ?
                ORDER BY r.nom
                """,
                (parcelle[0],),
            ).fetchall()

            parcelles.append(
                {
                    "id": parcelle[0],
                    "numero_lot": parcelle[1],
                    "superficie_m2": parcelle[2],
                    "remarque": parcelle[3],
                    "actif": parcelle[4],
                    "ressources": ressources,
                }
            )

        return {
            "id": agriculteur[0],
            "nom": agriculteur[1],
            "prenom": agriculteur[2],
            "cin": agriculteur[3],
            "telephone": agriculteur[4],
            "remarque": agriculteur[5],
            "actif": agriculteur[6],
            "date_creation": agriculteur[7],
            "date_modification": agriculteur[8],
            "parcelles": parcelles,
        }

    finally:
        connection.close()


def archiver_agriculteur(agriculteur_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE agriculteurs
            SET
                actif = 0,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
              AND actif = 1
            """,
            (agriculteur_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Agriculteur introuvable ou déjà archivé."
            )

        connection.execute(
            """
            UPDATE parcelles
            SET
                actif = 0,
                date_modification = CURRENT_TIMESTAMP
            WHERE agriculteur_id = ?
            """,
            (agriculteur_id,),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()