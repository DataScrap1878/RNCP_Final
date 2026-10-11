DROP TABLE IF EXISTS "sales-by-country";
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

CREATE TABLE "sales-by-country" (
    country_code TEXT PRIMARY KEY,
    country_name TEXT,
    total_orders INTEGER,
    total_quantity INTEGER,
    total_revenue_gbp REAL,
    total_revenue_eur REAL
);

CREATE TABLE sales (
    order_id TEXT PRIMARY KEY,
    order_date TEXT,
    book_id TEXT,
    country_code TEXT NOT NULL,
    channel_code TEXT NOT NULL,
    quantity INTEGER,
    discount_rate REAL,
    "revenu (GBP)" REAL,
    "revenu (EUR)" REAL,
    FOREIGN KEY (channel_code) REFERENCES channels(channel_code)
    -- Pas de FK sur country_code : référentiel pays incomplet (NL absent)
);

CREATE TABLE catalogue (
    Title TEXT,
    Price TEXT
);
