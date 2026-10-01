import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("BOT_TOKEN")

try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
except ValueError:
    ADMIN_ID = 0

SHOP_NAME = "Demo Store"
CURRENCY = "MDL"
LOW_STOCK_THRESHOLD = 3

# baza de date locală (SQLite) - folder "data/" (nu "database/") ca să nu se suprapună
# cu modulul database.py de la rădăcina proiectului
DB_PATH = os.path.join(BASE_DIR, "data", "shop.db")

ABOUT_TEXT = (
    f"ℹ️ Despre {SHOP_NAME}\n\n"
    "Suntem un magazin demo care vinde haine, încălțăminte și accesorii.\n"
    "Acest bot este un MVP pentru testarea unui flux complet de comandă prin Telegram."
)

CONTACT_TEXT = (
    "📞 Contact\n\n"
    "Telefon: +373 60 000 000\n"
    "Email: contact@demo-store.md\n"
    "Program: Luni - Vineri, 09:00 - 18:00"
)
