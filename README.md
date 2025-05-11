# rasa-bot

rasa run actions : pour le lancement du serveur d'actions, nécessaires pour les différentes actions définies dans mon fichier actions.py, comme la connexion à la base de données etc
rasa train : pour l'entrainement de mon modèle Rasa avec les différentes données (nlu.yml, stories.yml et domain.yml) et directives liées à la réservation dans un restaurant.
rasa sehell : pour tester le fonctionnement du bot en mode interactif après avoir lancé le serveur d'actions et entraîné le modèle


### Script de création de la base restaurant.db
docker run -it -v /c/data:/db nouchka/sqlite3 /db/restaurant.db

### Script de création d'une table reservation
CREATE TABLE reservations (
     id TEXT PRIMARY KEY,
     name TEXT,
     date TEXT,
     time TEXT,
     number_of_people INTEGER,
     phone_number TEXT,
     comment TEXT,
     status TEXT DEFAULT 'active'
);