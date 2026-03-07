# Sapp

## TODO

### general
- faire disparaître .gitignore

### garminconnect
- ajouter identification par token + stockage dans dossier data => une fois login avec .env pour la première fois

## But

Prendre le meilleur des apps (Komoot, garmin Connect et Strava)

### Détail des fonctionnalités (sur les données de l’utilisateur)

- Pente du parcours
- Zone FC
- Zone puissance
- Training effect
- Segment
- Local legends
- Manipulation des graphiques

## Étapes

1. gérer l’importation de donné
    1. Authentification de l’utilisateur 
        1. Variable d’environnement 
    2. Connexion à Garmin Connect et récupération des données

## Récupération des données 

Via Garmin Connect (wrapper python)

## Ressources

### Étapes 1
- Garmin Connect API, https://github.com/cyberjunky/python-garminconnect

Variable d'environnement avec https://pypi.org/project/python-dotenv/

## Initialisation du projet
### 1. Installer Python

Doc: https://www.python.org/downloads/

### 2. Initialiser de l'environnement virtuel
Dans le dossier du projet:

Doc: https://docs.python.org/fr/3.9/library/venv.html

`$> mkdir .venv`

`$> py -m venv .venv`

### 3. Activer environnement virtuel

Sous Windows

`$> .\.venv\Scripts\activate`

### 4. Installer les libraires

voir section Ressource, etape 1


### 5. Définir variable d'environnement

- Créer un fichier **.env**
- Ouvrir le fichier et définir 2 variables selon cet exmample

```
GARMIN_EMAIL="email"
GARMIN_PASSWORD="password"
```
