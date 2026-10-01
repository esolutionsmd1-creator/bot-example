from database import get_connection


def get_categories():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, name FROM categories ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_category(category_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, name FROM categories WHERE id = ?", (category_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_products_by_category(category_id, only_active=True):
    conn = get_connection()
    try:
        query = "SELECT * FROM products WHERE category_id = ?"
        params = [category_id]
        if only_active:
            query += " AND is_active = 1"
        query += " ORDER BY id"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_product(product_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_products():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_stock(product_id, new_stock):
    conn = get_connection()
    try:
        conn.execute("UPDATE products SET stock = ? WHERE id = ?", (max(0, int(new_stock)), product_id))
    finally:
        conn.close()


def update_price(product_id, new_price):
    conn = get_connection()
    try:
        conn.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
    finally:
        conn.close()


def toggle_active(product_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT is_active FROM products WHERE id = ?", (product_id,)).fetchone()
        if not row:
            return None
        new_val = 0 if row["is_active"] else 1
        conn.execute("UPDATE products SET is_active = ? WHERE id = ?", (new_val, product_id))
        return new_val
    finally:
        conn.close()


def add_product(category_id, name, description, price, image_url, stock):
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO products (category_id, name, description, price, image_url, stock, is_active) "
            "VALUES (?, ?, ?, ?, ?, ?, 1)",
            (category_id, name, description, price, image_url, stock),
        )
        return cur.lastrowid
    finally:
        conn.close()
