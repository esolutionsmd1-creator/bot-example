"""
Logica de creare a comenzilor. create_order() rulează într-o singură
tranzacție SQLite (BEGIN IMMEDIATE ... COMMIT) astfel încât verificarea
stocului și scăderea lui să fie atomice - fără overselling la comenzi
simultane (cerința #10, #13, #25.3).
"""
import logging
from datetime import datetime

import config
from database import get_connection

logger = logging.getLogger(__name__)


def create_order(telegram_id, customer_name, phone, address, notes=""):
    """Returns (ok: bool, order_dict | error_message)."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        cart = conn.execute("SELECT id FROM carts WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if not cart:
            conn.rollback()
            return False, "Coșul este gol."

        items = conn.execute(
            """
            SELECT ci.id AS item_id, ci.product_id, ci.quantity,
                   p.name, p.price, p.stock, p.is_active
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.cart_id = ?
            """,
            (cart["id"],),
        ).fetchall()

        if not items:
            conn.rollback()
            return False, "Coșul este gol."

        # verificare finală de stoc, în interiorul tranzacției (sursa adevărului)
        for item in items:
            if not item["is_active"]:
                conn.rollback()
                return False, f"Produsul '{item['name']}' nu mai este disponibil."
            if item["quantity"] > item["stock"]:
                conn.rollback()
                return False, (
                    f"Stoc insuficient pentru '{item['name']}'. Disponibil: {item['stock']}."
                )

        total = sum(i["price"] * i["quantity"] for i in items)

        cur = conn.execute(
            """
            INSERT INTO orders (telegram_id, customer_name, phone, address, notes,
                                 total_price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Nouă', ?)
            """,
            (telegram_id, customer_name, phone, address, notes, total, datetime.now().isoformat()),
        )
        order_id = cur.lastrowid

        for item in items:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, quantity, price) "
                "VALUES (?, ?, ?, ?, ?)",
                (order_id, item["product_id"], item["name"], item["quantity"], item["price"]),
            )
            conn.execute(
                "UPDATE products SET stock = ? WHERE id = ?",
                (item["stock"] - item["quantity"], item["product_id"]),
            )

        conn.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart["id"],))
        conn.commit()

        logger.info("Comandă nouă #%s pentru user %s, total %s MDL.", order_id, telegram_id, total)

        order = {
            "id": order_id,
            "total_price": total,
            "customer_name": customer_name,
            "phone": phone,
            "address": address,
            "items": [{"name": i["name"], "quantity": i["quantity"], "price": i["price"]} for i in items],
        }
        return True, order
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.exception("Eroare la crearea comenzii")
        return False, "A apărut o eroare la plasarea comenzii. Încearcă din nou."
    finally:
        conn.close()


def get_user_orders(telegram_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM orders WHERE telegram_id = ? ORDER BY id DESC", (telegram_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_order(order_id):
    conn = get_connection()
    try:
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return None
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
        result = dict(order)
        result["items"] = [dict(i) for i in items]
        return result
    finally:
        conn.close()


def get_all_orders(limit=50):
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_order_status(order_id, status):
    """Returns telegram_id-ul clientului (pentru notificare) sau None dacă nu există comanda."""
    conn = get_connection()
    try:
        order = conn.execute("SELECT telegram_id FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            return None
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        return order["telegram_id"]
    finally:
        conn.close()


def get_statistics():
    conn = get_connection()
    try:
        total_orders = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
        finished = conn.execute(
            "SELECT COUNT(*) c FROM orders WHERE status = 'Finalizată'"
        ).fetchone()["c"]
        total_sales = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) s FROM orders WHERE status != 'Anulată'"
        ).fetchone()["s"]
        sold_qty = conn.execute(
            """
            SELECT COALESCE(SUM(oi.quantity), 0) q FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.status != 'Anulată'
            """
        ).fetchone()["q"]
        popular = conn.execute(
            """
            SELECT oi.product_name, SUM(oi.quantity) qty FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.status != 'Anulată'
            GROUP BY oi.product_name
            ORDER BY qty DESC
            LIMIT 1
            """
        ).fetchone()
        low_stock = conn.execute(
            "SELECT COUNT(*) c FROM products WHERE stock <= ? AND is_active = 1",
            (config.LOW_STOCK_THRESHOLD,),
        ).fetchone()["c"]

        return {
            "total_orders": total_orders,
            "finished": finished,
            "total_sales": total_sales,
            "sold_qty": sold_qty,
            "popular_product": popular["product_name"] if popular else "-",
            "low_stock": low_stock,
        }
    finally:
        conn.close()
