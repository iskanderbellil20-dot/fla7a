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
                "Une parcelle active avec ce numéro de lot existe déjà."
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
def modifier_agriculteur(
    agriculteur_id,
    nom,
    prenom,
    cin,
    telephone,
    remarque=None,
):
    nom, prenom, cin, telephone = valider_agriculteur(
        nom,
        prenom,
        cin,
        telephone,
    )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE agriculteurs
            SET
                nom = ?,
                prenom = ?,
                cin = ?,
                telephone = ?,
                remarque = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
              AND actif = 1
            """,
            (
                nom,
                prenom,
                cin,
                telephone,
                remarque,
                agriculteur_id,
            ),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Agriculteur introuvable ou archivé."
            )

        connection.commit()

    except sqlite3.IntegrityError as error:
        connection.rollback()

        if "agriculteurs.cin" in str(error):
            raise ValueError(
                "Un autre agriculteur possède déjà ce CIN."
            ) from error

        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def ajouter_parcelle(
    agriculteur_id,
    numero_lot,
    superficie_m2,
    ressources_ids,
    remarque=None,
):
    numero_lot = str(numero_lot).strip()

    if not numero_lot:
        raise ValueError(
            "Le numéro du lot est obligatoire."
        )

    try:
        superficie_m2 = float(superficie_m2)
    except (TypeError, ValueError):
        raise ValueError(
            "La superficie est invalide."
        )

    if superficie_m2 <= 0:
        raise ValueError(
            "La superficie doit être supérieure à 0."
        )

    if not ressources_ids:
        raise ValueError(
            "La parcelle doit avoir au moins une ressource d'eau."
        )

    connection = get_connection()

    try:
        agriculteur = connection.execute(
            """
            SELECT id
            FROM agriculteurs
            WHERE id = ?
              AND actif = 1
            """,
            (agriculteur_id,),
        ).fetchone()

        if agriculteur is None:
            raise ValueError(
                "Agriculteur introuvable ou archivé."
            )

        verifier_ressources(
            connection,
            ressources_ids,
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
                superficie_m2,
                remarque,
            ),
        )

        parcelle_id = cursor.lastrowid

        for ressource_id in set(ressources_ids):
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

        return parcelle_id

    except sqlite3.IntegrityError as error:
        connection.rollback()

        if "parcelles.numero_lot" in str(error):
            raise ValueError(
                "Une parcelle active avec ce numéro de lot existe déjà."
            ) from error

        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
def modifier_parcelle(
    parcelle_id,
    numero_lot,
    superficie_m2,
    ressources_ids,
    remarque=None,
):
    numero_lot = str(numero_lot).strip()

    if not numero_lot:
        raise ValueError(
            "Le numéro du lot est obligatoire."
        )

    try:
        superficie_m2 = float(superficie_m2)
    except (TypeError, ValueError):
        raise ValueError(
            "La superficie est invalide."
        )

    if superficie_m2 <= 0:
        raise ValueError(
            "La superficie doit être supérieure à 0."
        )

    if not ressources_ids:
        raise ValueError(
            "La parcelle doit avoir au moins une ressource d'eau."
        )

    connection = get_connection()

    try:
        parcelle = connection.execute(
            """
            SELECT id
            FROM parcelles
            WHERE id = ?
              AND actif = 1
            """,
            (parcelle_id,),
        ).fetchone()

        if parcelle is None:
            raise ValueError(
                "Parcelle introuvable ou archivée."
            )

        verifier_ressources(
            connection,
            ressources_ids,
        )

        connection.execute(
            """
            UPDATE parcelles
            SET
                numero_lot = ?,
                superficie_m2 = ?,
                remarque = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                numero_lot,
                superficie_m2,
                remarque,
                parcelle_id,
            ),
        )

        # On remplace les anciennes ressources autorisées
        # par la nouvelle sélection du responsable.
        connection.execute(
            """
            DELETE FROM parcelles_ressources
            WHERE parcelle_id = ?
            """,
            (parcelle_id,),
        )

        for ressource_id in set(ressources_ids):
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

    except sqlite3.IntegrityError as error:
        connection.rollback()

        if "parcelles.numero_lot" in str(error):
            raise ValueError(
                "Une autre parcelle active possède déjà ce numéro de lot."
            ) from error

        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def archiver_parcelle(parcelle_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE parcelles
            SET
                actif = 0,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
              AND actif = 1
            """,
            (parcelle_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Parcelle introuvable ou déjà archivée."
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def restaurer_parcelle(parcelle_id):
    connection = get_connection()

    try:
        parcelle = connection.execute(
            """
            SELECT
                p.id,
                p.agriculteur_id,
                a.actif
            FROM parcelles p
            INNER JOIN agriculteurs a
                ON a.id = p.agriculteur_id
            WHERE p.id = ?
              AND p.actif = 0
            """,
            (parcelle_id,),
        ).fetchone()

        if parcelle is None:
            raise ValueError(
                "Parcelle introuvable ou déjà active."
            )

        if parcelle[2] == 0:
            raise ValueError(
                "Impossible de restaurer cette parcelle : "
                "l'agriculteur est archivé."
            )

        connection.execute(
            """
            UPDATE parcelles
            SET
                actif = 1,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (parcelle_id,),
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def restaurer_agriculteur(agriculteur_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE agriculteurs
            SET
                actif = 1,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
              AND actif = 0
            """,
            (agriculteur_id,),
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Agriculteur introuvable ou déjà actif."
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
def rechercher_agriculteurs(terme):
    terme = str(terme).strip()

    if not terme:
        return []

    recherche = f"%{terme}%"

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT DISTINCT
                a.id,
                a.nom,
                a.prenom,
                a.cin,
                a.telephone
            FROM agriculteurs a

            LEFT JOIN parcelles p
                ON p.agriculteur_id = a.id
               AND p.actif = 1

            WHERE a.actif = 1
              AND (
                    a.cin LIKE ?
                    OR a.nom LIKE ?
                    OR a.prenom LIKE ?
                    OR p.numero_lot LIKE ?
              )

            ORDER BY
                a.nom,
                a.prenom
            """,
            (
                recherche,
                recherche,
                recherche,
                recherche,
            ),
        ).fetchall()

        return rows

    finally:
        connection.close()

def lister_agriculteurs_avec_resume(
    inclure_archives=False,
):
    connection = get_connection()

    try:
        query = """
            SELECT
                a.id,
                a.nom,
                a.prenom,
                a.cin,
                a.telephone,
                a.actif,

                COUNT(
                    CASE
                        WHEN p.actif = 1
                        THEN 1
                    END
                ) AS nombre_parcelles

            FROM agriculteurs a

            LEFT JOIN parcelles p
                ON p.agriculteur_id = a.id
        """

        params = []

        if not inclure_archives:
            query += """
                WHERE a.actif = 1
            """

        query += """
            GROUP BY
                a.id,
                a.nom,
                a.prenom,
                a.cin,
                a.telephone,
                a.actif

            ORDER BY
                a.nom,
                a.prenom
        """

        return connection.execute(
            query,
            params,
        ).fetchall()

    finally:
        connection.close()

def modifier_agriculteur_complet(
    agriculteur_id,
    nom,
    prenom,
    cin,
    telephone,
    remarque,
    parcelles_modifiees,
    nouvelles_parcelles,
):
    nom, prenom, cin, telephone = valider_agriculteur(
        nom,
        prenom,
        cin,
        telephone,
    )

    connection = get_connection()

    try:
        agriculteur = connection.execute(
            """
            SELECT id
            FROM agriculteurs
            WHERE id = ?
              AND actif = 1
            """,
            (agriculteur_id,),
        ).fetchone()

        if agriculteur is None:
            raise ValueError(
                "Agriculteur introuvable ou archivé."
            )

        # Vérifier toutes les ressources AVANT
        # d'effectuer les modifications.
        toutes_ressources = []

        for parcelle in parcelles_modifiees:
            toutes_ressources.extend(
                parcelle["ressources_ids"]
            )

        for parcelle in nouvelles_parcelles:
            toutes_ressources.extend(
                parcelle["ressources_ids"]
            )

        verifier_ressources(
            connection,
            toutes_ressources,
        )

        # Modifier les informations personnelles.
        connection.execute(
            """
            UPDATE agriculteurs
            SET
                nom = ?,
                prenom = ?,
                cin = ?,
                telephone = ?,
                remarque = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                nom,
                prenom,
                cin,
                telephone,
                remarque,
                agriculteur_id,
            ),
        )

        # Modifier les parcelles existantes.
        for parcelle in parcelles_modifiees:
            parcelle_id = parcelle["id"]

            actuelle = connection.execute(
                """
                SELECT id
                FROM parcelles
                WHERE id = ?
                  AND agriculteur_id = ?
                  AND actif = 1
                """,
                (
                    parcelle_id,
                    agriculteur_id,
                ),
            ).fetchone()

            if actuelle is None:
                raise ValueError(
                    "Une parcelle à modifier "
                    "est introuvable ou archivée."
                )

            numero_lot = str(
                parcelle["numero_lot"]
            ).strip()

            if not numero_lot:
                raise ValueError(
                    "Le numéro du lot est obligatoire."
                )

            try:
                superficie = float(
                    parcelle["superficie_m2"]
                )
            except (TypeError, ValueError):
                raise ValueError(
                    f"La superficie du lot "
                    f"{numero_lot} est invalide."
                )

            if superficie <= 0:
                raise ValueError(
                    f"La superficie du lot "
                    f"{numero_lot} doit être "
                    "supérieure à 0."
                )

            if not parcelle["ressources_ids"]:
                raise ValueError(
                    f"Le lot {numero_lot} doit avoir "
                    "au moins une ressource."
                )

            connection.execute(
                """
                UPDATE parcelles
                SET
                    numero_lot = ?,
                    superficie_m2 = ?,
                    remarque = ?,
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    numero_lot,
                    superficie,
                    parcelle.get("remarque"),
                    parcelle_id,
                ),
            )

            connection.execute(
                """
                DELETE FROM parcelles_ressources
                WHERE parcelle_id = ?
                """,
                (parcelle_id,),
            )

            for ressource_id in set(
                parcelle["ressources_ids"]
            ):
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

        # Créer les nouvelles parcelles.
        for parcelle in nouvelles_parcelles:
            numero_lot = str(
                parcelle["numero_lot"]
            ).strip()

            if not numero_lot:
                raise ValueError(
                    "Le numéro du lot est obligatoire."
                )

            try:
                superficie = float(
                    parcelle["superficie_m2"]
                )
            except (TypeError, ValueError):
                raise ValueError(
                    f"La superficie du lot "
                    f"{numero_lot} est invalide."
                )

            if superficie <= 0:
                raise ValueError(
                    f"La superficie du lot "
                    f"{numero_lot} doit être "
                    "supérieure à 0."
                )

            if not parcelle["ressources_ids"]:
                raise ValueError(
                    f"Le lot {numero_lot} doit avoir "
                    "au moins une ressource."
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
                    parcelle.get("remarque"),
                ),
            )

            nouvelle_parcelle_id = (
                cursor.lastrowid
            )

            for ressource_id in set(
                parcelle["ressources_ids"]
            ):
                connection.execute(
                    """
                    INSERT INTO parcelles_ressources (
                        parcelle_id,
                        ressource_id
                    )
                    VALUES (?, ?)
                    """,
                    (
                        nouvelle_parcelle_id,
                        ressource_id,
                    ),
                )

        connection.commit()

    except sqlite3.IntegrityError as error:
        connection.rollback()

        message = str(error)

        if (
            "agriculteurs.cin"
            in message
        ):
            raise ValueError(
                "Un autre agriculteur possède déjà ce CIN."
            ) from error

        if (
            "parcelles.numero_lot"
            in message
            or "idx_parcelle_lot_actif_unique"
            in message
        ):
            raise ValueError(
                "Une autre parcelle active possède "
                "déjà ce numéro de lot."
            ) from error

        raise

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()