DROP TABLE IF EXISTS "sales_by_country";
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS catalogue;
DROP TABLE IF EXISTS channels;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    country_code TEXT PRIMARY KEY,
    country_name TEXT NOT NULL,
    region TEXT,
    is_active INTEGER
);

CREATE TABLE channels (
    channel_code TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    acquisition_cost_gbp REAL NOT NULL,
    channel_group TEXT NOT NULL,
    is_active INTEGER NOT NULL
);

-- Table d'agrégat calculée par le pipeline : pas de FK (contient aussi NL, absent de countries)
CREATE TABLE "sales_by_country" (
    country_code TEXT PRIMARY KEY,
    country_name TEXT,
    total_orders INTEGER,
    total_quantity INTEGER,
    total_revenue_gbp REAL,
    total_revenue_eur REAL
);

CREATE TABLE catalogue (
    book_id TEXT PRIMARY KEY,
    Title TEXT NOT NULL,
    Price REAL
);

CREATE TABLE sales (
    order_id TEXT PRIMARY KEY,
    order_date TEXT,
    book_id TEXT NOT NULL,
    country_code TEXT NOT NULL,
    channel_code TEXT NOT NULL,
    quantity INTEGER,
    discount_rate REAL,
    "revenu (GBP)" REAL,
    "revenu (EUR)" REAL,
    FOREIGN KEY (channel_code) REFERENCES channels(channel_code),
    FOREIGN KEY (book_id) REFERENCES catalogue(book_id)
    -- Pas de FK sur country_code : référentiel pays incomplet (NL absent).
    -- Mise à jour du référentiel pays à faire côté métier (hors pipeline).
    -- book_id du catalogue : obtenu par jointure sur le titre entre ventes et catalogue scrapé.
);