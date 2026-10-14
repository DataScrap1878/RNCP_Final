DROP TABLE IF EXISTS "sales_by_country";
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS catalogue;
DROP TABLE IF EXISTS channels;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    country_code TEXT PRIMARY KEY,
    country_name TEXT NOT NULL,
    region TEXT
);

CREATE TABLE channels (
    channel_code TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    acquisition_cost_gbp REAL NOT NULL,
    channel_group TEXT NOT NULL,
    is_active INTEGER NOT NULL
);

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
    Title TEXT not NULL,
    Price real
);
CREATE TABLE sales (
    order_id TEXT PRIMARY KEY,
    order_date TEXT,
    book_id TEXT not null,
    country_code TEXT NOT NULL,
    channel_code TEXT NOT NULL,
    quantity INTEGER,
    discount_rate REAL,
    "revenu (GBP)" REAL,
    "revenu (EUR)" REAL,
    FOREIGN KEY (channel_code) REFERENCES channels(channel_code),
    foreign key (book_id) references catalogue(book_id)
    -- Pas de FK sur country_code : référentiel pays incomplet (NL absent)
    -- Suggérer de mettre à jour le référentiel pays pour inclure tous les pays présents dans les ventes
    -- La Primary Key book_id du Catalogue a été construite a partir d'un lien sur le nom du livre avec la table Sales
);


