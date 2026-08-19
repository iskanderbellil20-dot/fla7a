from app.services.agriculteur_service import creer_agriculteur


parcelles = [
    {
        "numero_lot": "14",
        "superficie_m2": 7500,
        "ressources_ids": [1, 3],
    },
    {
        "numero_lot": "18",
        "superficie_m2": 12000,
        "ressources_ids": [2, 3],
    },
]


agriculteur_id = creer_agriculteur(
    nom="Ben Salah",
    prenom="Mohamed",
    cin="01234567",
    telephone="22123456",
    parcelles=parcelles,
    remarque="Agriculteur de test",
)

print(
    "Agriculteur créé avec ID :",
    agriculteur_id,
)