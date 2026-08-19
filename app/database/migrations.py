from app.database.connection import get_connection


MIGRATIONS = [
    (
        1,
        """
        CREATE TABLE association (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nom TEXT NOT NULL,
            adresse TEXT,
            telephone TEXT,
            email TEXT
        );

        CREATE TABLE agriculteurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            cin TEXT NOT NULL UNIQUE,
            telephone TEXT NOT NULL,
            remarque TEXT,
            actif INTEGER NOT NULL DEFAULT 1
                CHECK (actif IN (0, 1)),
            date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            date_modification TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            CHECK (
                length(cin) = 8
                AND cin NOT GLOB '*[^0-9]*'
            )
        );

        CREATE TABLE ressources_eau (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            etat TEXT NOT NULL DEFAULT 'DISPONIBLE'
                CHECK (
                    etat IN (
                        'DISPONIBLE',
                        'EN_PANNE',
                        'MAINTENANCE',
                        'HORS_SERVICE'
                    )
                ),
            description TEXT,
            remarque TEXT,
            actif INTEGER NOT NULL DEFAULT 1
                CHECK (actif IN (0, 1)),
            date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            date_modification TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE parcelles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agriculteur_id INTEGER NOT NULL,
            numero_lot TEXT NOT NULL UNIQUE,
            superficie_m2 REAL NOT NULL
                CHECK (superficie_m2 > 0),
            remarque TEXT,
            actif INTEGER NOT NULL DEFAULT 1
                CHECK (actif IN (0, 1)),
            date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            date_modification TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (agriculteur_id)
                REFERENCES agriculteurs(id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );

        CREATE TABLE parcelles_ressources (
            parcelle_id INTEGER NOT NULL,
            ressource_id INTEGER NOT NULL,

            PRIMARY KEY (parcelle_id, ressource_id),

            FOREIGN KEY (parcelle_id)
                REFERENCES parcelles(id)
                ON UPDATE CASCADE
                ON DELETE CASCADE,

            FOREIGN KEY (ressource_id)
                REFERENCES ressources_eau(id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );
        """
    ),
]


def create_migrations_table(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()


def get_current_version(connection):
    row = connection.execute(
        "SELECT MAX(version) FROM schema_migrations"
    ).fetchone()

    return row[0] if row[0] is not None else 0


def run_migrations():
    connection = get_connection()

    try:
        create_migrations_table(connection)

        current_version = get_current_version(connection)

        for version, sql in MIGRATIONS:
            if version <= current_version:
                continue

            print(f"Application de la migration {version}...")

            connection.executescript(sql)

            connection.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)",
                (version,),
            )

            connection.commit()

            print(f"Migration {version} appliquée.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()