# Projet de données de ventes Bookworld

Ce projet comprend un pipeline de données et une API Flask pour traiter les données de ventes de Bookworld. Le pipeline combine le fichier CSV des ventes avec les prix des livres récupérés sur Books to Scrape et les données de référence stockées dans SQLite, calcule les ventes en GBP et en EUR, puis enregistre les résultats pour l'API.

## Fichiers du projet

| Fichier | Rôle |
| --- | --- |
| `RNCP_query.py` | Extrait, transforme, agrège et charge les données de ventes |
| `app.py` | API Flask permettant de vérifier la base de données et de récupérer les données de ventes |
| `sales_raw.csv` | Fichier source des ventes |
| `bookworld_reference.db` | Tables de référence des pays, des canaux et des règles de catégorisation |
| `schema_final.sql` | Schéma utilisé pour créer les tables de sortie |
| `bookworld_final.db` | Base SQLite générée localement par le pipeline et lue par l'API ; elle n'est pas incluse dans le dépôt GitHub |

## Prérequis

- Python 3
- Les packages Python `pandas`, `requests`, `beautifulsoup4`, `Flask` et `python-dotenv`
- Un accès à Internet lors de l'exécution du pipeline, pour récupérer le taux de change GBP/EUR et les prix des livres

Installez les packages :

```bash
python -m pip install -r requirements.txt
```

## Configurer le jeton API

L'API lit le jeton attendu depuis la variable d'environnement `API_TOKEN`. Pour le configurer localement sans l'inscrire dans le code :

1. Dans PowerShell, copiez le fichier d'exemple : `Copy-Item .env.example .env`.
2. Remplacez la valeur de `API_TOKEN` dans `.env` par un jeton secret. Le fichier doit contenir une ligne de la forme `API_TOKEN=votre-jeton-secret`.
3. Ne partagez pas et n'ajoutez pas `.env` à Git : ce fichier est ignoré par `.gitignore`.

Vous pouvez générer un jeton aléatoire avec Python :

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Lors d'un appel à `GET /sales_details/<country>`, envoyez ce même jeton dans l'en-tête HTTP :

```text
Authorization: Bearer <votre-jeton-secret>
```

Le fichier `.env.example` ne contient qu'une valeur fictive. Il faut créer le fichier `.env` local avant de démarrer l'API pour que le jeton soit configuré. Si `.env` existe déjà, modifiez-le au lieu de recopier le fichier d'exemple. Après toute modification de `.env`, arrêtez puis redémarrez Flask pour qu'il recharge la variable.

Pour appeler la route protégée `GET /sales_details/<country>` depuis PowerShell, utilisez `curl.exe` et remplacez `VOTRE_JETON` par la valeur configurée dans `.env` :

```powershell
curl.exe -H "Authorization: Bearer VOTRE_JETON" "http://127.0.0.1:5000/sales_details/Netherlands"
```

Les routes publiques `/health`, `/sales_by_country` et `/sales_details` peuvent être ouvertes directement dans le navigateur. La barre d'adresse ne permet pas d'ajouter l'en-tête d'autorisation pour la route protégée. Pour la tester dans la console du navigateur (F12), exécutez :

```javascript
fetch("http://127.0.0.1:5000/sales_details/Netherlands", {
  headers: { Authorization: "Bearer VOTRE_JETON" }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

Ne publiez jamais un vrai jeton dans du code JavaScript ou dans un dépôt Git. HTTP convient uniquement aux essais sur la machine locale, car il ne chiffre pas les données transmises. Pour un déploiement public, utilisez HTTPS et ne distribuez pas le jeton aux clients du navigateur.

## Exécuter le pipeline de données

Ouvrez un terminal dans le répertoire du projet (`RNCP`), puis exécutez :

```bash
python RNCP_query.py
```

Le script lit `sales_raw.csv` et `bookworld_reference.db`, récupère les prix actuels des livres et le taux de change GBP/EUR, puis crée ou met à jour `bookworld_final.db` avec les ventes agrégées et le détail des ventes. Cette base est un résultat généré : elle est ignorée par Git et n'apparaît donc pas sur GitHub. Après avoir cloné le projet, exécutez le pipeline pour générer cette base avant de lancer l'API.

Le pipeline initialise les tables de sortie à l'aide de `schema_final.sql`. Ce schéma supprime puis recrée ces tables : chaque exécution remplace donc les données de sortie existantes.

## Lancer l'API

Après avoir exécuté le pipeline, démarrez Flask depuis le même répertoire du projet :

```bash
python app.py
```

Par défaut, Flask s'exécute en mode débogage à l'adresse `http://127.0.0.1:5000`.

### Points de terminaison

| Méthode | Point de terminaison | Description |
| --- | --- | --- |
| `GET` | `/health` | Vérifie que l'API peut ouvrir la base de données de sortie |
| `GET` | `/sales_by_country` | Renvoie les ventes agrégées par pays |
| `GET` | `/sales_details` | Renvoie le détail des ventes traitées |
| `GET` | `/sales_details/<country>` | Renvoie le détail des ventes pour un pays donné |

Exemples de requêtes :

```text
http://127.0.0.1:5000/health
http://127.0.0.1:5000/sales_by_country
http://127.0.0.1:5000/sales_details/Netherlands
```

Le point de terminaison filtré par pays accepte actuellement les pays répertoriés dans `app.py`, notamment les Pays-Bas, la France, l'Allemagne, l'Italie, le Royaume-Uni et les États-Unis. Dans l'URL, utilisez le nom du pays en anglais, par exemple `Netherlands`.
