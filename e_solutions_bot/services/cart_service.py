from datetime import datetime

from database import get_connection


def _get_or_create_cart(conn, telegram_id):
    row = conn.execute("SELECT id FROM carts WHERE telegram_id = ?", (telegram_id,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO carts (telegram_id, created_at) VALUES (?, ?)",
        (telegram_id, datetime.now().isoformat()),
    )
    return cur.lastrowid


def add_to_cart(telegram_id, product_id, quantity=1):
    """Adaugă produs în coș, verificând stocul. Returns (ok: bool, message: str)."""
    conn = get_connection()
    try:
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not product:
            return False, "Produsul nu mai există."
        if not product["is_active"]:
            return False, "Produsul nu mai este disponibil."

        cart_id = _get_or_create_cart(conn, telegram_id)
        item = conn.execute(
            "SELECT * FROM cart_items WHERE cart_id = ? AND product_id = ?",
            (cart_id, product_id),
        ).fetchone()
        current_qty = item["quantity"] if item else 0
        wanted_qty = current_qty + quantity

        if wanted_qty > product["stock"]:
            return False, f"Stoc insuficient. Disponibil: {product['stock']}."

        if item:
            conn.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (wanted_qty, item["id"]))
        else:
            conn.execute(
                "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)",
                (cart_id, product_id, quantity),
            )
        return True, "Adăugat în coș."
    finally:
        conn.close()


def get_cart_items(telegram_id):
    conn = get_connection()
    try:
        cart = conn.execute("SELECT id FROM carts WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if not cart:
            return []
        rows = conn.execute(
            """
            SELECT ci.id AS item_id, ci.quantity, p.id AS product_id, p.name, p.price,
                   p.stock, p.is_active
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.cart_id = ?
            ORDER BY ci.id
            """,
            (cart["id"],),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def change_quantity(telegram_id, item_id, delta):
    """Modifică cantitatea unui produs din coș. Returns (ok, message)."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT ci.id, ci.quantity, ci.cart_id, p.stock
            FROM cart_items ci
            JOIN carts c ON c.id = ci.cart_id
            JOIN products p ON p.id = ci.product_id
            WHERE ci.id = ? AND c.telegram_id = ?
            """,
            (item_id, telegram_id),
        ).fetchone()
        if not row:
            return False, "Produsul nu a fost găsit în coș."

        new_qty = row["quantity"] + delta
        if new_qty <= 0:
            conn.execute("DELETE FROM cart_items WHERE id = ?", (item_id,))
            return True, "Produs eliminat din coș."

        if new_qty > row["stock"]:
            return False, f"Stoc insuficient. Disponibil: {row['stock']}."

        conn.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_qty, item_id))
        return True, "Cantitate actualizată."
    finally:
        conn.close()


def remove_item(telegram_id, item_id):
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM cart_items WHERE id = ? AND cart_id IN "
            "(SELECT id FROM carts WHERE telegram_id = ?)",
            (item_id, telegram_id),
        )
        return True
    finally:
        conn.close()


def clear_cart(telegram_id):
    conn = get_connection()
    try:
        cart = conn.execute("SELECT id FROM carts WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if cart:
            conn.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["id"],))
    finally:
        conn.close()


def get_cart_total(telegram_id):
    items = get_cart_items(telegram_id)
    return sum(i["price"] * i["quantity"] for i in items)
