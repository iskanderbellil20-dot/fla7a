from app.database.migrations import run_migrations


def initialize_database():
    run_migrations()


if __name__ == "__main__":
    initialize_database()
    print("Base de données initialisée avec succès.")