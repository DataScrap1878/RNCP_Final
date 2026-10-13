import os
from functools import wraps
from secrets import compare_digest
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request

import sqlite3
import pandas as pd

load_dotenv()

BASE_PATH = Path(__file__).resolve().parent
DB_PATH = BASE_PATH / 'bookworld_final.db'
app = Flask(__name__)

## Connexion a la base de données en lecture seule
## Cela permet d'éviter de créer un fichier vide si la base de données n'existe pas
## Le mode URI est utilisé pour permettre l'utilisation de l'option "mode=ro" dans la chaîne de connexion SQLite.
def get_connection():
    return sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)

## Décorateur pour vérifier le token d'authentification dans les requêtes API
## On évite d'utiliser un token en clair dans le code pour des raisons de sécurité. Le token est stocké dans une variable d'environnement.
def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        expected_token = os.environ.get("API_TOKEN")
        if not expected_token:
            return jsonify({"message": "Token API non configuré côté serveur"}), 500

        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return jsonify({"message": "Token non valide"}), 401

        token = authorization[len("Bearer "):]
        if not compare_digest(token, expected_token):
            return jsonify({"message": "Token non valide"}), 401

        return f(*args, **kwargs)
    return wrapper

## end point pour vérifier la santé de l'API (sans token car c'est un check de santé)
@app.route("/health", methods=["GET"])
def health_check():
    try:
        conn = get_connection()
        nb_lignes = conn.execute('SELECT COUNT(*) FROM "sales_by_country"').fetchone()[0] ## Teste la connexion à la base de données et le nombre de lignes dans la table "sales_by_country"
        conn.close()
        return jsonify({"message": f"Connexion Ok - Nb lignes Sales_by_Country: {nb_lignes}"}), 200
    except Exception as e:
        print(f"Erreur : {e}")    # visible dans TON terminal
        return jsonify({"message": "Erreur de connexion"}), 503 ## 503 signifie "Service Unavailable" et est utilisé pour indiquer que le service n'est pas disponible pour le moment.

### End point pour récupérer les ventes par pays
@app.route("/sales-by-country", methods=["GET"])
@token_required
def sales_by_country():
    try:
        conn = get_connection()
        query = 'SELECT * FROM "sales_by_country" order by total_revenue_eur desc'
        df = pd.read_sql_query(query, conn)
        conn.close()
        return jsonify(df.to_dict(orient="records")), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des données", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
