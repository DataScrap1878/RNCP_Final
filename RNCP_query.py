import pandas as pd
import sqlite3
import requests as req
from bs4 import BeautifulSoup
from pathlib import Path

REFERENCE_DB_PATH = Path(__file__).resolve().parent / "bookworld_reference.db"


def extract():
  global sales, df, df_channels, df_countries, taux_gbp,df_category_rules
  try:
    sales = extract_csv()
    taux_gbp = Obtenir_Tx_Change()
    df = scrape_books()
    df_channels, df_countries,df_category_rules = extract_db()
    print("Extraction complêtement réussie")
  except Exception as e:
    print(f"Erreur durant l'extraction: {e}")
    raise
  return

def extract_csv():
    sales = pd.read_csv("sales_raw.csv")
    return sales

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
    df = pd.DataFrame(data)
    return df

def extract_db():
  try:
    conn = sqlite3.connect(REFERENCE_DB_PATH)
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


def transform(sales,df):
  create_sql2_insertNL_if_not()
  fusion_tables(sales,df)
  update_missing_country()
  convertir_prix()

def fusion_tables(sales,df):
    global df_livres, df_countries, df_channels
    nb_lignes_avant = len(sales)
    df_livres = pd.merge(sales, df, left_on='book_name', right_on='Title')
    df_livres = pd.merge(df_livres, df_countries, on='country_code', how ="left", suffixes = ('_books','_country'))
    df_livres = pd.merge(df_livres, df_channels, on='channel_code', how ="left")
    nb_lignes_apres = len(df_livres)
    if nb_lignes_avant != nb_lignes_apres:
        print(f"Attention : Nombre de lignes différent : {nb_lignes_avant} avant, {nb_lignes_apres} après")
    print(f"Fusion des tables terminée correctement df_livres : {nb_lignes_apres} lignes {len(df_livres.columns)} colonnes")
    return

def update_missing_country():
  df_livres['country_name']=df_livres['country_name'].fillna("Inconnu")
  return

def convertir_prix():
  global df_livres, taux_gbp
  df_livres['Price'] = df_livres['Price'].astype(str).str.replace('£', '').astype(float)
  if taux_gbp is not None:
    df_livres['Price (Eur)'] = df_livres['Price'] * taux_gbp
    df_livres['Acquisition cost (Eur)'] = df_livres['acquisition_cost_gbp'] * taux_gbp
    df_livres['revenu (GBP)'] = df_livres["quantity"]*df_livres['Price']*(1-df_livres["discount_rate"])
    df_livres['revenu (EUR)'] = df_livres["quantity"]*df_livres['Price (Eur)']*(1-df_livres["discount_rate"])
  print(f"Calcul du CA terminé : EUR : {df_livres['revenu (EUR)'].sum()} GBP :{ df_livres['revenu (GBP)'].sum()}")
  return

def create_aggregation():
  df_sales_by_country = (
      df_livres.groupby(["country_code", "country_name"], as_index=False)
      .agg({
          "order_id": "count",
          "quantity": "sum",
          "revenu (GBP)": "sum",
          "revenu (EUR)": "sum"
      })
  )
  print(f"Aggregation terminée : {df_sales_by_country.shape}")
  return df_sales_by_country

def create_sql1_inactive_countries():
  conn = sqlite3.connect(REFERENCE_DB_PATH)
  df_countries_inactive = pd.read_sql_query("SELECT * FROM countries where is_active = '1'", conn)
  print(df_countries_inactive)
  conn.close()

## Run the SQL created to update NL if not already created in the countries table
def create_sql2_insertNL_if_not():
    conn = sqlite3.connect(REFERENCE_DB_PATH)
    query = """
    INSERT INTO countries (country_code, country_name, currency_code,
    vat_rate, region, is_active
    )
    SELECT 'NL', 'Netherlands', 'EUR', 20.0, 'Europe', 1
    WHERE NOT EXISTS (SELECT 1 FROM countries WHERE country_code = 'NL')
    """
    try:
        conn.execute(query)
        conn.commit()
    finally:
        conn.close()

def load_to_database(df_countries_df,df_sales_by_country,df_livres):
    conn = sqlite3.connect("bookworld_final.db")          # étape 1

    schema_sql = Path("schema_final.sql").read_text(encoding="utf-8")
    conn.executescript(schema_sql)                         # étape 2

    df_countries[["country_code", "country_name", "region"]].to_sql(
        "countries",          # nom de la table dans schema_final.sql
        conn,
        if_exists="append",   # on AJOUTE dans la table existante
        index=False           # on n'envoie pas l'index pandas
    )                                                      # étape 3
    df_sales_by_country[["country_code", "country_name", "order_id", "quantity", "revenu (GBP)", "revenu (EUR)"]].to_sql(
        "sales_by_country",   # nom de la table dans schema_final.sql
        conn,
        if_exists="append",   # on AJOUTE dans la table existante
        index=False           # on n'envoie pas l'index pandas
    )                                                      # étape 3
    df_livres[[
        "order_id",
        "order_date",
        "book_id",
        "country_name",
        "quantity",
        "discount_rate",
        "Title",
        "Price",
        "currency_code",
        "vat_rate",
        "region",
        "is_active_x",
        "channel_name",
        "acquisition_cost_gbp",
        "is_active_y",
        "Price (Eur)",
        "Acquisition cost (Eur)",
        "revenu (GBP)",
        "revenu (EUR)"
    ]].to_sql(
        "df_livres",          # nom de la table dans schema_final.sql
        conn,
        if_exists="append",   # on AJOUTE dans la table existante
        index=False           # on n'envoie pas l'index pandas
    )                                                      # étape 3
    conn.commit()
    conn.close()


def main():
  extract()
  transform(sales, df)
  df_sales_by_country = create_aggregation()
  load_to_database(df_countries,df_sales_by_country,df_livres)


if __name__== "__main__":
  main()