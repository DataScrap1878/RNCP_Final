import pandas as pd
import sqlite3
import requests as req
from bs4 import BeautifulSoup
from pathlib import Path

 ## Déclarer les chemins vers les fichiers de référence et la base de données finale
 ## Permet d'éviter les problèmes de chemins relatifs lors de l'exécution du script depuis un autre répertoire
BASE_PATH = Path(__file__).resolve().parent
REFERENCE_DB_PATH_REFERENCE = BASE_PATH / "bookworld_reference.db"
REFERENCE_DB_PATH_BKWORLDFINAL = BASE_PATH / "bookworld_final.db"
REFERENCE_DB_PATH_SALES = BASE_PATH / "sales_raw.csv"
REFERENCE_DB_PATH_SCHEMA = BASE_PATH / "schema_final.sql"


## Fonction Extract : Extraction des données depuis les sources (csv, web, db)
def extract():
  global sales, df_catalogue, df_channels, df_countries, taux_gbp,df_category_rules
  try:
    sales = extract_csv()
    taux_gbp = Obtenir_Tx_Change()
    df_catalogue = scrape_books()
    df_channels, df_countries,df_category_rules = extract_db()
    print("Extraction complêtement réussie")
  except Exception as e:
    print(f"Erreur durant l'extraction: {e}")
    raise
  return

## Sous-fonction Extract_csv : Extraction des données depuis le fichier CSV
def extract_csv():
    sales = pd.read_csv(REFERENCE_DB_PATH_SALES)
    return sales

## Sous-fonction Obtenir_Tx_Change : Extraction du taux de change depuis l'API Frankfurter
def Obtenir_Tx_Change():
  url = "https://api.frankfurter.dev/v2/rate/gbp/eur"
  response = req.get(url)

  if response.status_code == 200:
      data = response.json()
      taux_gbp = data.get('rate')
      date_taux = data["date"]
      print(f"Extraction du taux de change réussie : {taux_gbp} en date du : {date_taux}")
      return taux_gbp
  else:
      print("Impossible de récupérer le taux de change.")
      return None

## Sous-fonction scrape_books : Extraction des données depuis le site web Books to Scrape
## Uniquement la première page est extraite pour l'exemple.
def scrape_books():
    response = req.get('http://books.toscrape.com/catalogue/page-1.html')
    soup = BeautifulSoup(response.content, 'html.parser')
    liste_livres = soup.find_all('article', class_='product_pod')

    data = []

    for item in liste_livres:
        title = item.h3.a['title']
        price = item.find('p', class_='price_color').text

        data.append({
            'Title': title,
            'Price': price
        })

    print("Extraction page Web réussie")
    df_catalogue = pd.DataFrame(data)
    return df_catalogue

## Fonction Extract_db : Extraction des données depuis la base de données SQLite
## Extraction des 3 bases de données : channels, countries et category_rules
## Nous utiliserons seulement les tables channels et countries pour la suite du projet.
def extract_db():
  try:
    conn = sqlite3.connect(REFERENCE_DB_PATH_REFERENCE)
    df_channels = pd.read_sql_query("SELECT * FROM channels;", conn)
    df_countries = pd.read_sql_query("SELECT * FROM countries;", conn)
    df_category_rules = pd.read_sql_query("SELECT * FROM category_rules", conn)
  except sqlite3.Error as e:
    print(f"Erreur SQLite : {e}")
    return None, None, None
  except Exception as e:
    print(f"Erreur inattendue : {e}")
    return None, None, None
  conn.close()
  print("Extraction db réussie")
  return df_channels, df_countries,df_category_rules

## Fonction Transform : Transformation des données extraites pour les préparer à l'insertion dans la base de données finale
def transform(sales,df_catalogue,df_countries,df_channels):
    sales = suprimer_colonnes_inutiles(sales)
    df_temp = fusionner_tables(sales,df_catalogue,df_countries,df_channels)
    convertir_prix(df_temp,taux_gbp)
    identifier_pays_inconnus(df_temp)
    return df_temp

## Traitement RGPD : Supprimer les colonnes inutiles pour la base de données finale
def suprimer_colonnes_inutiles(sales):
   sales= sales.drop(columns=['customer_first_name', 'customer_last_name' ])
   return sales

## Fusionner les tables sales, df_catalogue, df_countries et df_channels pour créer un DataFrame complet
## qui servira à l'agrégation des ventes par pays et à l'insertion dans la base de données finale.
def fusionner_tables(sales,df_catalogue,df_countries,df_channels):
  nb_lignes_avant = len(sales)
  df_temp = pd.merge(sales, df_catalogue, left_on='book_name', right_on='Title')
  df_temp = pd.merge(df_temp, df_countries, on='country_code', how='left', suffixes=('_books', '_country'))
  df_temp = pd.merge(df_temp, df_channels, on='channel_code', how='left', suffixes=('_country', '_channel'))
  nb_lignes_apres = len(df_temp)
  print(f"Fusion des tables terminée : {nb_lignes_avant} lignes avant, {nb_lignes_apres} lignes après")
  return df_temp

## Identifier les pays inconnus et les remplacer par "Inconnu" en indiquant le code pays dans la colonne country_name
def identifier_pays_inconnus(df_temp):
  codes_inconnus = df_temp[df_temp['country_name'].isna()]['country_code'].unique()
  if len(codes_inconnus) > 0:
    print(f"Attention, les codes pays suivants sont inconnus et seront remplacés par 'Inconnu' : {list(codes_inconnus)}")
    libelles_inconnus = "Inconnu (" + df_temp['country_code'] + ")"
    df_temp['country_name']=df_temp['country_name'].fillna(libelles_inconnus)
  return df_temp

## Convertir les prix en EUR et calculer le revenu total par ligne de commande
def convertir_prix(df_temp,taux_gbp):
  df_temp['Price'] = df_temp['Price'].astype(str).str.replace('£', '').astype(float)
  if taux_gbp is not None:
    df_temp['Price (Eur)'] = df_temp['Price'] * taux_gbp
    df_temp['Acquisition cost (Eur)'] = df_temp['acquisition_cost_gbp'] * taux_gbp
    df_temp['revenu (GBP)'] = df_temp["quantity"]*df_temp['Price']*(1-df_temp["discount_rate"])
    df_temp['revenu (EUR)'] = df_temp["quantity"]*df_temp['Price (Eur)']*(1-df_temp["discount_rate"])
  print(f"Calcul du CA terminé : EUR : {df_temp['revenu (EUR)'].sum()} GBP :{ df_temp['revenu (GBP)'].sum()}")
  return df_temp

## Créer l'agrégation des ventes par pays à partir du DataFrame df_temp
def create_aggregation(df_temp):
  sales_by_country = (
      df_temp.groupby(["country_code", "country_name"], as_index=False)
      .agg(
          total_orders=("order_id", "count"),
          total_quantity=("quantity", "sum"),
          total_revenue_gbp=("revenu (GBP)", "sum"),
          total_revenue_eur=("revenu (EUR)", "sum")
      )
  )
  print(f"Aggregation terminée : {sales_by_country.shape}")
  return sales_by_country

## Créer la base de données finale bookworld_final.db et y insérer les données transformées
def load_to_database(df_countries, sales_by_country, df_channels, df_catalogue, df_temp):
    conn = sqlite3.connect(REFERENCE_DB_PATH_BKWORLDFINAL)
    conn.execute("PRAGMA foreign_keys = ON")

    schema_sql = REFERENCE_DB_PATH_SCHEMA 
    conn.executescript(schema_sql.read_text(encoding="utf-8"))              # étape 2

    df_countries[["country_code", "country_name", "region"]].to_sql(
        "countries",          # nom de la table dans schema_final.sql
        conn,
        if_exists="append",   # on AJOUTE dans la table existante
        index=False           # on n'envoie pas l'index pandas
    )
    df_channels.to_sql(
        "channels",          # nom de la table dans schema_final.sql
        conn,
        if_exists="append",   # on AJOUTE dans la table existante
        index=False           # on n'envoie pas l'index pandas
    )                                                      # étape 3
    sales_by_country[[
        "country_code",
        "country_name",
        "total_orders",
        "total_quantity",
        "total_revenue_gbp",
        "total_revenue_eur"
    ]].to_sql(
        "sales-by-country",   # nom de la table dans schema_final.sql
        conn,
        if_exists="append",   # on AJOUTE dans la table existante
        index=False           # on n'envoie pas l'index pandas
    )                                                      # étape 3
    df_temp[[
        "order_id",
        "order_date",
        "book_id",
        "country_code",
        "channel_code",
        "quantity",
        "discount_rate",
        "revenu (GBP)",
        "revenu (EUR)"
    ]].to_sql(
        "sales",          # nom de la table dans schema_final.sql
        conn,
        if_exists="append",   # on AJOUTE dans la table existante
        index=False           # on n'envoie pas l'index pandas
    )
    df_catalogue.to_sql(
        "catalogue",          # nom de la table dans schema_final.sql
        conn,
        if_exists="append",   # on AJOUTE dans la table existante
        index=False           # on n'envoie pas l'index pandas
    )                                                      # étape 3
    conn.commit()
    conn.close()

## Appeler la fonction main pour exécuter le pipeline ETL
def main():
  extract()
  df_temp = transform(sales, df_catalogue,df_countries,df_channels)
  sales_by_country = create_aggregation(df_temp)
  load_to_database(df_countries, sales_by_country, df_channels, df_catalogue, df_temp)
  
## Appeler la fonction main si le script est exécuté directement
if __name__== "__main__":
  main()