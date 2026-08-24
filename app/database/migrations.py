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
    (
        2,
        """
        CREATE TABLE tours_eau (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            numero_recu INTEGER NOT NULL UNIQUE,

            parcelle_id INTEGER NOT NULL,
            ressource_id INTEGER NOT NULL,

            date_heure_debut TEXT NOT NULL,
            date_heure_fin TEXT NOT NULL,

            duree_minutes INTEGER NOT NULL
                CHECK (duree_minutes > 0),

            statut TEXT NOT NULL DEFAULT 'PLANIFIE'
                CHECK (
                    statut IN (
                        'PLANIFIE',
                        'TERMINE',
                        'ANNULE',
                        'REPORTE',
                        'INTERROMPU'
                    )
                ),

            remarque TEXT,

            date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            date_modification TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (parcelle_id)
                REFERENCES parcelles(id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT,

            FOREIGN KEY (ressource_id)
                REFERENCES ressources_eau(id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );


        CREATE TABLE indisponibilites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            ressource_id INTEGER NOT NULL,

            type TEXT NOT NULL
                CHECK (
                    type IN (
                        'PANNE',
                        'MAINTENANCE',
                        'AUTRE'
                    )
                ),

            date_heure_debut TEXT NOT NULL,
            date_heure_fin TEXT,

            motif TEXT,
            remarque TEXT,

            date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (ressource_id)
                REFERENCES ressources_eau(id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );


        CREATE INDEX idx_tours_eau_ressource_dates
        ON tours_eau (
            ressource_id,
            date_heure_debut,
            date_heure_fin
        );


        CREATE INDEX idx_tours_eau_parcelle
        ON tours_eau (parcelle_id);


        CREATE INDEX idx_indisponibilites_ressource_dates
        ON indisponibilites (
            ressource_id,
            date_heure_debut,
            date_heure_fin
        );
        """

    ),
    
        (
        3,
        """
        CREATE TABLE historique (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            type_objet TEXT NOT NULL,

            objet_id INTEGER NOT NULL,

            action TEXT NOT NULL,

            ancienne_valeur TEXT,
            nouvelle_valeur TEXT,

            motif TEXT,

            date_action TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );


        CREATE INDEX idx_historique_objet
        ON historique (
            type_objet,
            objet_id,
            date_action
        );
        """
    ),

    (
        4,
        """
        ALTER TABLE tours_eau
        ADD COLUMN tour_origine_id INTEGER
            REFERENCES tours_eau(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT;


        CREATE INDEX idx_tours_eau_origine
        ON tours_eau (tour_origine_id);
        """
    ),

    (
        5,
        """
        CREATE TABLE parcelles_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            agriculteur_id INTEGER NOT NULL,

            numero_lot TEXT NOT NULL,

            superficie_m2 REAL NOT NULL
                CHECK (superficie_m2 > 0),

            remarque TEXT,

            actif INTEGER NOT NULL DEFAULT 1
                CHECK (actif IN (0, 1)),

            date_creation TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            date_modification TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (agriculteur_id)
                REFERENCES agriculteurs(id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );


        INSERT INTO parcelles_new (
            id,
            agriculteur_id,
            numero_lot,
            superficie_m2,
            remarque,
            actif,
            date_creation,
            date_modification
        )
        SELECT
            id,
            agriculteur_id,
            numero_lot,
            superficie_m2,
            remarque,
            actif,
            date_creation,
            date_modification
        FROM parcelles;


        DROP INDEX IF EXISTS idx_parcelle_lot_actif_unique;
        DROP INDEX IF EXISTS idx_parcelles_agriculteur;


        CREATE UNIQUE INDEX idx_parcelle_lot_actif_unique_new
        ON parcelles_new (numero_lot)
        WHERE actif = 1;


        CREATE INDEX idx_parcelles_agriculteur_new
        ON parcelles_new (agriculteur_id);


        PRAGMA foreign_keys = OFF;


        DROP TABLE parcelles;


        ALTER TABLE parcelles_new
        RENAME TO parcelles;


        PRAGMA foreign_keys = ON;


        DROP INDEX IF EXISTS idx_parcelle_lot_actif_unique_new;
        DROP INDEX IF EXISTS idx_parcelles_agriculteur_new;


        CREATE UNIQUE INDEX idx_parcelle_lot_actif_unique
        ON parcelles (numero_lot)
        WHERE actif = 1;


        CREATE INDEX idx_parcelles_agriculteur
        ON parcelles (agriculteur_id);
        """
    ),
        (
        6,
        """
        UPDATE tours_eau
        SET
            nom_agriculteur_snapshot = (
                SELECT a.nom
                FROM parcelles p
                INNER JOIN agriculteurs a
                    ON a.id = p.agriculteur_id
                WHERE p.id = tours_eau.parcelle_id
            ),

            prenom_agriculteur_snapshot = (
                SELECT a.prenom
                FROM parcelles p
                INNER JOIN agriculteurs a
                    ON a.id = p.agriculteur_id
                WHERE p.id = tours_eau.parcelle_id
            ),

            cin_snapshot = (
                SELECT a.cin
                FROM parcelles p
                INNER JOIN agriculteurs a
                    ON a.id = p.agriculteur_id
                WHERE p.id = tours_eau.parcelle_id
            ),

            telephone_snapshot = (
                SELECT a.telephone
                FROM parcelles p
                INNER JOIN agriculteurs a
                    ON a.id = p.agriculteur_id
                WHERE p.id = tours_eau.parcelle_id
            ),

            numero_lot_snapshot = (
                SELECT p.numero_lot
                FROM parcelles p
                WHERE p.id = tours_eau.parcelle_id
            ),

            superficie_m2_snapshot = (
                SELECT p.superficie_m2
                FROM parcelles p
                WHERE p.id = tours_eau.parcelle_id
            ),

            ressource_nom_snapshot = (
                SELECT r.nom
                FROM ressources_eau r
                WHERE r.id = tours_eau.ressource_id
            );
        """
    ),
            (
        7,
        """
        UPDATE parcelles
        SET nom_lot = 'Lot ' || numero_lot
        WHERE nom_lot IS NULL
           OR trim(nom_lot) = '';


        UPDATE tours_eau
        SET nom_lot_snapshot = (
            SELECT p.nom_lot
            FROM parcelles p
            WHERE p.id = tours_eau.parcelle_id
        )
        WHERE nom_lot_snapshot IS NULL
           OR trim(nom_lot_snapshot) = '';
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

def preparer_migration_6(connection):
    colonnes_existantes = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(tours_eau)"
        ).fetchall()
    }

    colonnes_a_ajouter = {
        "nom_agriculteur_snapshot":
            "TEXT",

        "prenom_agriculteur_snapshot":
            "TEXT",

        "cin_snapshot":
            "TEXT",

        "telephone_snapshot":
            "TEXT",

        "numero_lot_snapshot":
            "TEXT",

        "superficie_m2_snapshot":
            "REAL",

        "ressource_nom_snapshot":
            "TEXT",
    }

    for nom_colonne, type_sql in (
        colonnes_a_ajouter.items()
    ):
        if (
            nom_colonne
            in colonnes_existantes
        ):
            continue

        connection.execute(
            f"""
            ALTER TABLE tours_eau
            ADD COLUMN {nom_colonne} {type_sql}
            """
        )

    connection.commit()
def preparer_migration_7(connection):
    # ---------------------------------
    # Table parcelles
    # ---------------------------------

    colonnes_parcelles = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(parcelles)"
        ).fetchall()
    }

    if (
        "nom_lot"
        not in colonnes_parcelles
    ):
        connection.execute(
            """
            ALTER TABLE parcelles
            ADD COLUMN nom_lot TEXT
            """
        )

    # ---------------------------------
    # Table tours_eau
    # ---------------------------------

    colonnes_tours = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(tours_eau)"
        ).fetchall()
    }

    if (
        "nom_lot_snapshot"
        not in colonnes_tours
    ):
        connection.execute(
            """
            ALTER TABLE tours_eau
            ADD COLUMN nom_lot_snapshot TEXT
            """
        )

    connection.commit()

def run_migrations():
    connection = get_connection()

    try:
        create_migrations_table(connection)

        current_version = get_current_version(connection)

        for version, sql in MIGRATIONS:
            if version <= current_version:
                continue

            print(f"Application de la migration {version}...")

            if version == 5:
                connection.commit()
                connection.execute(
                    #"PRAGMA foreign_keys = OFF"
                )
            if version == 6:
                preparer_migration_6(
                    connection
                )
            if version == 7:
                preparer_migration_7(
                    connection
                )
            connection.executescript(sql)

            if version == 5:
                connection.execute(
                    #"PRAGMA foreign_keys = ON"
                )    

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