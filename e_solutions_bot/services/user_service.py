from datetime import datetime

from database import get_connection


def get_or_create_user(telegram_id, name, username):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET name = ?, username = ? WHERE telegram_id = ?",
                (name, username, telegram_id),
            )
            return dict(row)
        cur = conn.execute(
            "INSERT INTO users (telegram_id, name, username, created_at) VALUES (?, ?, ?, ?)",
            (telegram_id, name, username, datetime.now().isoformat()),
        )
        return {"id": cur.lastrowid, "telegram_id": telegram_id, "name": name, "username": username}
    finally:
        conn.close()


def update_phone(telegram_id, phone):
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, telegram_id))
    finally:
        conn.close()
