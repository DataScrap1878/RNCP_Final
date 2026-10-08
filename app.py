import os
from functools import wraps
from secrets import compare_digest

from dotenv import load_dotenv
from flask import Flask, jsonify, request
import sqlite3
import pandas as pd

load_dotenv()

DB_path = 'bookworld_final.db'
app = Flask(__name__)

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

@app.route("/health", methods=["GET"])
def health_check():
    try:
        conn = sqlite3.connect(DB_path)
        conn.close()
        return jsonify({"message": "Connexion Ok"}), 200
    except Exception as e:
        print(f"Erreur : {e}")    # visible dans TON terminal
        jsonify({"message": "Erreur de connexion"}), 500
    
@app.route("/sales_by_country", methods=["GET"])
def sales_by_country():
    try:
        conn = sqlite3.connect(DB_path)
        query = "SELECT * FROM sales_by_country"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return jsonify(df.to_dict(orient="records")), 200
    except Exception as e:
        return jsonify({"message": "Erreur lors de la récupération des données", "error": str(e)}), 500

@app.route("/sales_details", methods=["GET"])
def sales_details():
    try:
        conn = sqlite3.connect(DB_path)
        query = "SELECT * FROM df_livres"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return jsonify(df.to_dict(orient="records")), 200
    except Exception as e:
        print(f"Erreur : {e}")    # visible dans TON terminal
        return jsonify({"message": "Erreur lors de la récupération des données", "error": str(e)}), 500


## Optionnel : Filter le details pour un pays spécifique en utilisant un paramètre de route

@app.route("/sales_details/<country>", methods=["GET"])
@token_required
def sales_details_by_country(country):
    # Vérifie si le pays est valide
    if country.capitalize() not in ['Netherlands', 'France', 'Spain', 'Germany', 'France',
                                     'Italy', 'Belgium', 'Portugal', 'Switzerland', 'Austria',
                                     'United Kingdom', 'United States', 'Canada', 'Australia']:
        return jsonify({"message": "Pays non valide"}), 400 
    try:
        conn = sqlite3.connect(DB_path)
        query = f"SELECT * FROM df_livres WHERE country_name = '{country}'"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return jsonify(df.to_dict(orient="records")), 200
    except Exception as e:
        print(f"Erreur : {e}")    # visible dans TON terminal
        return jsonify({"message": "Erreur lors de la récupération des données", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
