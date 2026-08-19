import json

from app.database.connection import get_connection


def enregistrer_historique(
    connection,
    type_objet,
    objet_id,
    action,
    ancienne_valeur=None,
    nouvelle_valeur=None,
    motif=None,
):
    ancienne_json = (
        json.dumps(
            ancienne_valeur,
            ensure_ascii=False,
        )
        if ancienne_valeur is not None
        else None
    )

    nouvelle_json = (
        json.dumps(
            nouvelle_valeur,
            ensure_ascii=False,
        )
        if nouvelle_valeur is not None
        else None
    )

    connection.execute(
        """
        INSERT INTO historique (
            type_objet,
            objet_id,
            action,
            ancienne_valeur,
            nouvelle_valeur,
            motif
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            type_objet,
            objet_id,
            action,
            ancienne_json,
            nouvelle_json,
            motif,
        ),
    )


def obtenir_historique(
    type_objet,
    objet_id,
):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                action,
                ancienne_valeur,
                nouvelle_valeur,
                motif,
                date_action
            FROM historique
            WHERE type_objet = ?
              AND objet_id = ?
            ORDER BY date_action DESC, id DESC
            """,
            (
                type_objet,
                objet_id,
            ),
        ).fetchall()

        resultat = []

        for row in rows:
            resultat.append(
                {
                    "id": row[0],
                    "action": row[1],
                    "ancienne_valeur": (
                        json.loads(row[2])
                        if row[2]
                        else None
                    ),
                    "nouvelle_valeur": (
                        json.loads(row[3])
                        if row[3]
                        else None
                    ),
                    "motif": row[4],
                    "date_action": row[5],
                }
            )

        return resultat

    finally:
        connection.close()