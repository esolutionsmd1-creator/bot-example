"""
Strat de acces la baza de date SQLite.
Inițializează schema și populează produse demo dacă baza e goală.
"""
import os
import sqlite3
import logging

import config

logger = logging.getLogger(__name__)


def get_connection():
    """Conexiune nouă, în modul autocommit (isolation_level=None) ca să
    putem controla manual tranzacțiile acolo unde e nevoie (ex: creare comandă)."""
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    image_url TEXT,
    stock INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    name TEXT,
    username TEXT,
    phone TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS carts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    customer_name TEXT,
    phone TEXT,
    address TEXT,
    notes TEXT,
    total_price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'Nouă',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
"""

DEMO_CATEGORIES = ["👕 Haine", "👟 Încălțăminte", "🎒 Accesorii", "🔥 Reduceri"]

# (categorie, nume, descriere, preț, image_url, stoc)
DEMO_PRODUCTS = [
    ("👕 Haine", "Nike Hoodie", "Hanorac Nike, unisex, bumbac gros.", 499, "", 5),
    ("👕 Haine", "Basic T-Shirt", "Tricou basic, bumbac 100%.", 249, "", 10),
    ("👕 Haine", "Cargo Pants", "Pantaloni cargo, model larg.", 699, "", 4),
    ("👟 Încălțăminte", "Nike Air", "Adidași Nike Air, confort maxim.", 1499, "", 3),
    ("🎒 Accesorii", "Cap", "Șapcă unisex, reglabilă.", 199, "", 7),
]


def init_db():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        _seed_demo_data(conn)
        logger.info("Baza de date inițializată (%s).", config.DB_PATH)
    finally:
        conn.close()


def _seed_demo_data(conn):
    if conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0] > 0:
        return

    cat_ids = {}
    for name in DEMO_CATEGORIES:
        cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        cat_ids[name] = cur.lastrowid

    for cat_name, name, description, price, image_url, stock in DEMO_PRODUCTS:
        conn.execute(
            "INSERT INTO products (category_id, name, description, price, image_url, stock, is_active) "
            "VALUES (?, ?, ?, ?, ?, ?, 1)",
            (cat_ids[cat_name], name, description, price, image_url, stock),
        )
    logger.info("Produse demo adăugate.")
