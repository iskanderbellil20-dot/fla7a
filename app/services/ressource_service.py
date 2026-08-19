from app.database.connection import get_connection


ETATS_RESSOURCE = (
    "DISPONIBLE",
    "EN_PANNE",
    "MAINTENANCE",
    "HORS_SERVICE",
)


def creer_ressource(nom, description=None, remarque=None):
    nom = nom.strip()

    if not nom:
        raise ValueError("Le nom de la ressource est obligatoire.")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO ressources_eau (
                nom,
                description,
                remarque
            )
            VALUES (?, ?, ?)
            """,
            (
                nom,
                description,
                remarque,
            ),
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def lister_ressources(inclure_archivees=False):
    connection = get_connection()

    try:
        if inclure_archivees:
            query = """
                SELECT
                    id,
                    nom,
                    etat,
                    description,
                    remarque,
                    actif
                FROM ressources_eau
                ORDER BY nom
            """
            rows = connection.execute(query).fetchall()

        else:
            query = """
                SELECT
                    id,
                    nom,
                    etat,
                    description,
                    remarque,
                    actif
                FROM ressources_eau
                WHERE actif = 1
                ORDER BY nom
            """
            rows = connection.execute(query).fetchall()

        return rows

    finally:
        connection.close()


def obtenir_ressource(ressource_id):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                id,
                nom,
                etat,
                description,
                remarque,
                actif,
                date_creation,
                date_modification
            FROM ressources_eau
            WHERE id = ?
            """,
            (ressource_id,),
        ).fetchone()

        return row

    finally:
        connection.close()


def modifier_ressource(
    ressource_id,
    nom,
    description=None,
    remarque=None,
):
    nom = nom.strip()

    if not nom:
        raise ValueError("Le nom de la ressource est obligatoire.")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE ressources_eau
            SET
                nom = ?,
                description = ?,
                remarque = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                nom,
                description,
                remarque,
                ressource_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError("Ressource introuvable.")

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def changer_etat_ressource(ressource_id, nouvel_etat):
    if nouvel_etat not in ETATS_RESSOURCE:
        raise ValueError("État de ressource invalide.")

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE ressources_eau
            SET
                etat = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
              AND actif = 1
            """,
            (
                nouvel_etat,
                ressource_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Ressource introuvable ou archivée."
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def archiver_ressource(ressource_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE ressources_eau
            SET
                actif = 0,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
              AND actif = 1
            """,
            (ressource_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Ressource introuvable ou déjà archivée."
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def restaurer_ressource(ressource_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE ressources_eau
            SET
                actif = 1,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
              AND actif = 0
            """,
            (ressource_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Ressource introuvable ou déjà active."
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()