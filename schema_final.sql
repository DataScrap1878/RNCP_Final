DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    country_code TEXT PRIMARY KEY,
    country_name TEXT NOT NULL,
    region TEXT
);

DROP TABLE IF EXISTS sales_by_country;

CREATE TABLE sales_by_country (
    country_code TEXT,
    country_name TEXT,
    order_id INTEGER,
    quantity INTEGER,
    "revenu (GBP)" REAL,
    "revenu (EUR)" REAL
);

DROP TABLE IF EXISTS df_livres;

CREATE TABLE df_livres (
    order_id INTEGER,
    order_date TEXT,
    book_id INTEGER,
    country_name TEXT,
    quantity INTEGER,
    discount_rate REAL,
    Title TEXT,
    Price REAL,
    currency_code TEXT,
    vat_rate REAL,
    region TEXT,
    is_active_x INTEGER,
    channel_name TEXT,
    acquisition_cost_gbp REAL,
    is_active_y INTEGER,
    "Price (Eur)" REAL,
    "Acquisition cost (Eur)" REAL,
    "revenu (GBP)" REAL,
    "revenu (EUR)" REAL
);
