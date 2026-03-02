# Sapp

## But

Prendre le meilleur des apps (Komoot, garmin Connect et Strava)

### Détail des fonctionnalités (sur les données de l’utilisateur)

#### Komoot

- Pente du parcours

#### Garmin Connect

- Zone FC
- Zone puissance
- Training effect

#### Strava

- Segment
- Local legends
- Manipulation des graphiques

## Étapes

1. gérer l’importation de donné
    1. Authentification de l’utilisateur 
        1. Variable d’environnement 
    2. Connexion au différentes applis
        1. Garmin Connect
        2. Komoot
        3. Strava 

## Ressources

### Étapes 1

- Komoot API, https://matteovillosio.com/post/kompy/
- Garmin Connect API, https://github.com/cyberjunky/python-garminconnect
- Strava API, https://pypi.org/project/stravalib/

## Initialisation du projet
### 1. Installer Python

Doc: https://www.python.org/downloads/

### 2. Initialiser de l'environnement virtuel
Dans le dossier du projet:

Doc: https://docs.python.org/fr/3.9/library/venv.html

$> mkdir .venv

$> py -m venv .venv

### 3. Activer environnement virtuel

Sous Windows

$> .\.venv\Scripts\activate

### 4. Installer les libraires

voir section Ressource, etape 1

## Récupération des données 

L'idéal serait de récupérer les infos directement depuis l'appareil en question mais les transferts de données étant chiffré impossible de bypass l'API garmin connect

Méthode a utiliser passer via l'API garmin connect