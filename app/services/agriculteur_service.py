import sqlite3

from app.database.connection import get_connection
from app.services.historique_service import enregistrer_historique

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

def archiver_parcelle(
    parcelle_id,
    motif=None,
):
    connection = get_connection()

    try:
        parcelle = connection.execute(
            """
            SELECT
                p.id,
                p.numero_lot,
                p.superficie_m2,
                p.actif,
                p.agriculteur_id,
                a.nom,
                a.prenom
            FROM parcelles p

            INNER JOIN agriculteurs a
                ON a.id = p.agriculteur_id

            WHERE p.id = ?
            """,
            (parcelle_id,),
        ).fetchone()

        if parcelle is None:
            raise ValueError(
                "Parcelle introuvable."
            )

        if parcelle[3] == 0:
            raise ValueError(
                "Cette parcelle est déjà archivée."
            )

        tours = connection.execute(
            """
            SELECT COUNT(*)
            FROM tours_eau
            WHERE parcelle_id = ?
              AND statut = 'PLANIFIE'
            """,
            (parcelle_id,),
        ).fetchone()[0]

        if tours > 0:
            raise ValueError(
                f"Impossible d'archiver cette parcelle : "
                f"{tours} tour(s) d'eau planifié(s) "
                "doivent d'abord être traités."
            )

        ancien = {
            "numero_lot": parcelle[1],
            "superficie_m2": parcelle[2],
            "actif": 1,
            "agriculteur_id": parcelle[4],
        }

        connection.execute(
            """
            UPDATE parcelles
            SET
                actif = 0,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (parcelle_id,),
        )

        nouveau = ancien.copy()
        nouveau["actif"] = 0

        from app.services.historique_service import (
            enregistrer_historique,
        )

        enregistrer_historique(
            connection=connection,
            type_objet="PARCELLE",
            objet_id=parcelle_id,
            action="ARCHIVAGE",
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

def restaurer_parcelle(
    parcelle_id,
    motif=None,
):
    connection = get_connection()

    try:
        parcelle = connection.execute(
            """
            SELECT
                p.id,
                p.numero_lot,
                p.superficie_m2,
                p.actif,
                p.agriculteur_id,
                a.actif
            FROM parcelles p

            INNER JOIN agriculteurs a
                ON a.id = p.agriculteur_id

            WHERE p.id = ?
            """,
            (parcelle_id,),
        ).fetchone()

        if parcelle is None:
            raise ValueError(
                "Parcelle introuvable."
            )

        if parcelle[3] == 1:
            raise ValueError(
                "Cette parcelle est déjà active."
            )

        if parcelle[5] == 0:
            raise ValueError(
                "Impossible de restaurer la parcelle : "
                "son agriculteur est archivé."
            )

        # Vérification importante depuis V5.
        conflit = connection.execute(
            """
            SELECT id
            FROM parcelles
            WHERE numero_lot = ?
              AND actif = 1
              AND id != ?
            """,
            (
                parcelle[1],
                parcelle_id,
            ),
        ).fetchone()

        if conflit is not None:
            raise ValueError(
                f"Impossible de restaurer le lot "
                f"{parcelle[1]} : une parcelle active "
                "porte déjà ce numéro."
            )

        ancien = {
            "numero_lot": parcelle[1],
            "superficie_m2": parcelle[2],
            "actif": 0,
            "agriculteur_id": parcelle[4],
        }

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

        nouveau = ancien.copy()
        nouveau["actif"] = 1

        from app.services.historique_service import (
            enregistrer_historique,
        )

        enregistrer_historique(
            connection=connection,
            type_objet="PARCELLE",
            objet_id=parcelle_id,
            action="RESTAURATION",
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
        ancien_agriculteur = connection.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                cin,
                telephone,
                remarque,
                actif
            FROM agriculteurs
            WHERE id = ?
            """,
            (agriculteur_id,),
        ).fetchone()

        if ancien_agriculteur is None:
            raise ValueError(
                "Agriculteur introuvable."
            )

        if ancien_agriculteur[6] == 0:
            raise ValueError(
                "Impossible de modifier un agriculteur archivé."
            )

        # -----------------------------------------
        # Vérifier toutes les ressources
        # avant de commencer les modifications.
        # -----------------------------------------

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

        # -----------------------------------------
        # Anciennes informations agriculteur
        # -----------------------------------------

        anciennes_infos = {
            "nom": ancien_agriculteur[1],
            "prenom": ancien_agriculteur[2],
            "cin": ancien_agriculteur[3],
            "telephone": ancien_agriculteur[4],
            "remarque": ancien_agriculteur[5],
        }

        nouvelles_infos = {
            "nom": nom,
            "prenom": prenom,
            "cin": cin,
            "telephone": telephone,
            "remarque": remarque,
        }

        # -----------------------------------------
        # Modifier l'agriculteur
        # -----------------------------------------

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

        # -----------------------------------------
        # Historique agriculteur
        # -----------------------------------------

        if anciennes_infos != nouvelles_infos:
            enregistrer_historique(
                connection=connection,
                type_objet="AGRICULTEUR",
                objet_id=agriculteur_id,
                action="MODIFICATION",
                ancienne_valeur=anciennes_infos,
                nouvelle_valeur=nouvelles_infos,
                motif=None,
            )

        # -----------------------------------------
        # Modifier les parcelles existantes
        # -----------------------------------------

        for parcelle in parcelles_modifiees:
            parcelle_id = parcelle["id"]

            actuelle = connection.execute(
                """
                SELECT
                    id,
                    numero_lot,
                    superficie_m2,
                    remarque,
                    actif
                FROM parcelles
                WHERE id = ?
                  AND agriculteur_id = ?
                """,
                (
                    parcelle_id,
                    agriculteur_id,
                ),
            ).fetchone()

            if actuelle is None:
                raise ValueError(
                    "Une parcelle à modifier "
                    "est introuvable."
                )

            if actuelle[4] == 0:
                raise ValueError(
                    f"Le lot {actuelle[1]} est archivé "
                    "et ne peut pas être modifié."
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

            ressources_ids = list(
                set(
                    parcelle.get(
                        "ressources_ids",
                        [],
                    )
                )
            )

            if not ressources_ids:
                raise ValueError(
                    f"Le lot {numero_lot} doit avoir "
                    "au moins une ressource d'eau."
                )

            verifier_ressources(
                connection,
                ressources_ids,
            )

            anciennes_ressources = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT ressource_id
                    FROM parcelles_ressources
                    WHERE parcelle_id = ?
                    ORDER BY ressource_id
                    """,
                    (parcelle_id,),
                ).fetchall()
            ]

            ancienne_valeur = {
                "numero_lot": actuelle[1],
                "superficie_m2": actuelle[2],
                "remarque": actuelle[3],
                "ressources_ids": sorted(
                    anciennes_ressources
                ),
            }

            nouvelle_valeur = {
                "numero_lot": numero_lot,
                "superficie_m2": superficie,
                "remarque": parcelle.get(
                    "remarque"
                ),
                "ressources_ids": sorted(
                    ressources_ids
                ),
            }

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

            if ancienne_valeur != nouvelle_valeur:
                enregistrer_historique(
                    connection=connection,
                    type_objet="PARCELLE",
                    objet_id=parcelle_id,
                    action="MODIFICATION",
                    ancienne_valeur=ancienne_valeur,
                    nouvelle_valeur=nouvelle_valeur,
                    motif=None,
                )

        # -----------------------------------------
        # Créer les nouvelles parcelles
        # -----------------------------------------

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

            ressources_ids = list(
                set(
                    parcelle.get(
                        "ressources_ids",
                        [],
                    )
                )
            )

            if not ressources_ids:
                raise ValueError(
                    f"Le lot {numero_lot} doit avoir "
                    "au moins une ressource d'eau."
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
                    superficie,
                    parcelle.get("remarque"),
                ),
            )

            nouvelle_parcelle_id = (
                cursor.lastrowid
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
                        nouvelle_parcelle_id,
                        ressource_id,
                    ),
                )

            enregistrer_historique(
                connection=connection,
                type_objet="PARCELLE",
                objet_id=nouvelle_parcelle_id,
                action="CREATION",
                ancienne_valeur=None,
                nouvelle_valeur={
                    "agriculteur_id":
                        agriculteur_id,
                    "numero_lot":
                        numero_lot,
                    "superficie_m2":
                        superficie,
                    "remarque":
                        parcelle.get(
                            "remarque"
                        ),
                    "ressources_ids":
                        sorted(
                            ressources_ids
                        ),
                },
                motif=None,
            )

        # -----------------------------------------
        # Tout s'est correctement déroulé.
        # -----------------------------------------

        connection.commit()

    except sqlite3.IntegrityError as error:
        connection.rollback()

        message = str(error)

        if "agriculteurs.cin" in message:
            raise ValueError(
                "Un autre agriculteur possède déjà ce CIN."
            ) from error

        if (
            "parcelles.numero_lot" in message
            or
            "idx_parcelle_lot_actif_unique"
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

def lister_tours_planifies_parcelle(
    parcelle_id,
):
    connection = get_connection()

    try:
        return connection.execute(
            """
            SELECT
                t.id,
                t.numero_recu,
                t.date_heure_debut,
                t.date_heure_fin,
                r.nom
            FROM tours_eau t

            INNER JOIN ressources_eau r
                ON r.id = t.ressource_id

            WHERE t.parcelle_id = ?
              AND t.statut = 'PLANIFIE'

            ORDER BY t.date_heure_debut
            """,
            (parcelle_id,),
        ).fetchall()

    finally:
        connection.close()

def transferer_parcelle(
    parcelle_id,
    nouvel_agriculteur_id,
    ressources_ids,
    motif=None,
):
    connection = get_connection()

    try:
        parcelle = connection.execute(
            """
            SELECT
                p.id,
                p.agriculteur_id,
                p.numero_lot,
                p.superficie_m2,
                p.remarque,
                p.actif,
                a.nom,
                a.prenom
            FROM parcelles p

            INNER JOIN agriculteurs a
                ON a.id = p.agriculteur_id

            WHERE p.id = ?
            """,
            (parcelle_id,),
        ).fetchone()

        if parcelle is None:
            raise ValueError(
                "Parcelle introuvable."
            )

        if parcelle[5] == 0:
            raise ValueError(
                "Une parcelle archivée "
                "ne peut pas être transférée."
            )

        ancien_agriculteur_id = parcelle[1]

        if (
            ancien_agriculteur_id
            == nouvel_agriculteur_id
        ):
            raise ValueError(
                "Le nouveau propriétaire doit être "
                "différent de l'ancien propriétaire."
            )

        nouvel_agriculteur = connection.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                actif
            FROM agriculteurs
            WHERE id = ?
            """,
            (nouvel_agriculteur_id,),
        ).fetchone()

        if nouvel_agriculteur is None:
            raise ValueError(
                "Le nouvel agriculteur est introuvable."
            )

        if nouvel_agriculteur[3] == 0:
            raise ValueError(
                "Le nouvel agriculteur est archivé."
            )

        tours_planifies = connection.execute(
            """
            SELECT COUNT(*)
            FROM tours_eau
            WHERE parcelle_id = ?
              AND statut = 'PLANIFIE'
            """,
            (parcelle_id,),
        ).fetchone()[0]

        if tours_planifies > 0:
            raise ValueError(
                f"Impossible de transférer cette parcelle : "
                f"{tours_planifies} tour(s) d'eau planifié(s) "
                "doivent d'abord être traités."
            )

        ressources_ids = sorted(
            set(ressources_ids)
        )

        if not ressources_ids:
            raise ValueError(
                "Sélectionnez au moins une "
                "ressource pour la nouvelle parcelle."
            )

        verifier_ressources(
            connection,
            ressources_ids,
        )

        numero_lot = parcelle[2]
        superficie = parcelle[3]
        remarque = parcelle[4]

        # Archiver l'ancienne occurrence.
        connection.execute(
            """
            UPDATE parcelles
            SET
                actif = 0,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (parcelle_id,),
        )

        # Créer une nouvelle occurrence du même lot
        # pour le nouveau propriétaire.
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
                nouvel_agriculteur_id,
                numero_lot,
                superficie,
                remarque,
            ),
        )

        nouvelle_parcelle_id = (
            cursor.lastrowid
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
                    nouvelle_parcelle_id,
                    ressource_id,
                ),
            )

        ancienne_valeur = {
            "parcelle_id": parcelle_id,
            "agriculteur_id":
                ancien_agriculteur_id,
            "proprietaire":
                f"{parcelle[7]} {parcelle[6]}",
            "numero_lot": numero_lot,
            "superficie_m2": superficie,
            "actif": 1,
        }

        nouvelle_valeur = {
            "parcelle_id":
                nouvelle_parcelle_id,
            "agriculteur_id":
                nouvel_agriculteur_id,
            "proprietaire":
                (
                    f"{nouvel_agriculteur[2]} "
                    f"{nouvel_agriculteur[1]}"
                ),
            "numero_lot": numero_lot,
            "superficie_m2": superficie,
            "ressources_ids": ressources_ids,
            "actif": 1,
        }

        enregistrer_historique(
            connection=connection,
            type_objet="PARCELLE",
            objet_id=parcelle_id,
            action="TRANSFERT",
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            motif=motif,
        )

        enregistrer_historique(
            connection=connection,
            type_objet="PARCELLE",
            objet_id=nouvelle_parcelle_id,
            action="CREATION_PAR_TRANSFERT",
            ancienne_valeur=None,
            nouvelle_valeur=nouvelle_valeur,
            motif=motif,
        )

        connection.commit()

        return nouvelle_parcelle_id

    except sqlite3.IntegrityError as error:
        connection.rollback()

        raise ValueError(
            "Impossible de transférer la parcelle. "
            "Vérifiez notamment le numéro du lot."
        ) from error

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def diviser_parcelle(
    parcelle_id,
    nouvel_agriculteur_id,
    nouvelle_superficie_m2,
    nouveau_numero_lot,
    ressources_ids,
    motif=None,
):
    connection = get_connection()

    try:
        parcelle = connection.execute(
            """
            SELECT
                p.id,
                p.agriculteur_id,
                p.numero_lot,
                p.superficie_m2,
                p.remarque,
                p.actif,
                a.nom,
                a.prenom
            FROM parcelles p

            INNER JOIN agriculteurs a
                ON a.id = p.agriculteur_id

            WHERE p.id = ?
            """,
            (parcelle_id,),
        ).fetchone()

        if parcelle is None:
            raise ValueError(
                "Parcelle introuvable."
            )

        if parcelle[5] == 0:
            raise ValueError(
                "Une parcelle archivée "
                "ne peut pas être divisée."
            )

        superficie_actuelle = float(
            parcelle[3]
        )

        try:
            superficie_cedee = float(
                nouvelle_superficie_m2
            )
        except (TypeError, ValueError):
            raise ValueError(
                "La superficie cédée est invalide."
            )

        if superficie_cedee <= 0:
            raise ValueError(
                "La superficie cédée doit être "
                "supérieure à 0."
            )

        if superficie_cedee >= superficie_actuelle:
            raise ValueError(
                "Pour une division, la superficie "
                "cédée doit être inférieure à la "
                "superficie actuelle. Pour céder "
                "la totalité, utilisez Transférer."
            )

        superficie_restante = (
            superficie_actuelle
            - superficie_cedee
        )

        nouveau_numero_lot = str(
            nouveau_numero_lot
        ).strip()

        if not nouveau_numero_lot:
            raise ValueError(
                "Le numéro du nouveau lot "
                "est obligatoire."
            )

        if (
            nouveau_numero_lot
            == str(parcelle[2])
        ):
            raise ValueError(
                "Le nouveau lot doit avoir "
                "un numéro différent du lot d'origine."
            )

        nouvel_agriculteur = connection.execute(
            """
            SELECT
                id,
                nom,
                prenom,
                actif
            FROM agriculteurs
            WHERE id = ?
            """,
            (nouvel_agriculteur_id,),
        ).fetchone()

        if nouvel_agriculteur is None:
            raise ValueError(
                "Le nouvel agriculteur est introuvable."
            )

        if nouvel_agriculteur[3] == 0:
            raise ValueError(
                "Le nouvel agriculteur est archivé."
            )

        tours_planifies = connection.execute(
            """
            SELECT COUNT(*)
            FROM tours_eau
            WHERE parcelle_id = ?
              AND statut = 'PLANIFIE'
            """,
            (parcelle_id,),
        ).fetchone()[0]

        if tours_planifies > 0:
            raise ValueError(
                f"Impossible de diviser cette parcelle : "
                f"{tours_planifies} tour(s) d'eau planifié(s) "
                "doivent d'abord être traités."
            )

        ressources_ids = sorted(
            set(ressources_ids)
        )

        if not ressources_ids:
            raise ValueError(
                "Sélectionnez au moins une ressource "
                "pour la nouvelle parcelle."
            )

        verifier_ressources(
            connection,
            ressources_ids,
        )

        # Réduire la parcelle d'origine.
        connection.execute(
            """
            UPDATE parcelles
            SET
                superficie_m2 = ?,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                superficie_restante,
                parcelle_id,
            ),
        )

        # Créer la partie cédée comme
        # une nouvelle parcelle.
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
                nouvel_agriculteur_id,
                nouveau_numero_lot,
                superficie_cedee,
                (
                    f"Créée par division du lot "
                    f"{parcelle[2]}"
                ),
            ),
        )

        nouvelle_parcelle_id = (
            cursor.lastrowid
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
                    nouvelle_parcelle_id,
                    ressource_id,
                ),
            )

        ancienne_valeur = {
            "parcelle_id": parcelle_id,
            "proprietaire":
                f"{parcelle[7]} {parcelle[6]}",
            "numero_lot": parcelle[2],
            "superficie_m2":
                superficie_actuelle,
        }

        nouvelle_valeur = {
            "parcelle_origine": {
                "id": parcelle_id,
                "numero_lot": parcelle[2],
                "superficie_m2":
                    superficie_restante,
            },
            "nouvelle_parcelle": {
                "id": nouvelle_parcelle_id,
                "agriculteur_id":
                    nouvel_agriculteur_id,
                "proprietaire":
                    (
                        f"{nouvel_agriculteur[2]} "
                        f"{nouvel_agriculteur[1]}"
                    ),
                "numero_lot":
                    nouveau_numero_lot,
                "superficie_m2":
                    superficie_cedee,
                "ressources_ids":
                    ressources_ids,
            },
        }

        enregistrer_historique(
            connection=connection,
            type_objet="PARCELLE",
            objet_id=parcelle_id,
            action="DIVISION",
            ancienne_valeur=ancienne_valeur,
            nouvelle_valeur=nouvelle_valeur,
            motif=motif,
        )

        enregistrer_historique(
            connection=connection,
            type_objet="PARCELLE",
            objet_id=nouvelle_parcelle_id,
            action="CREATION_PAR_DIVISION",
            ancienne_valeur=None,
            nouvelle_valeur=nouvelle_valeur[
                "nouvelle_parcelle"
            ],
            motif=motif,
        )

        connection.commit()

        return {
            "parcelle_origine_id":
                parcelle_id,
            "superficie_restante":
                superficie_restante,
            "nouvelle_parcelle_id":
                nouvelle_parcelle_id,
            "superficie_cedee":
                superficie_cedee,
        }

    except sqlite3.IntegrityError as error:
        connection.rollback()

        raise ValueError(
            "Impossible de diviser la parcelle. "
            "Le nouveau numéro de lot est "
            "peut-être déjà utilisé."
        ) from error

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()