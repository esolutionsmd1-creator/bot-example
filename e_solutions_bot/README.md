# E-Solutions Bot — MVP magazin Telegram

Bot Telegram demo pentru un magazin: categorii → produse → coș → checkout → comandă,
cu bază de date SQLite, verificare și scădere automată de stoc, panou admin și statistici.

## 1. Instalare

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Creare bot Telegram

1. Deschide [@BotFather](https://t.me/BotFather) în Telegram.
2. `/newbot` → alege un nume și un username → primești `BOT_TOKEN`.
3. Află-ți ID-ul de Telegram (ex. de la [@userinfobot](https://t.me/userinfobot)) → acesta e `ADMIN_ID`.

## 3. Configurare

Copiază `.env.example` în `.env` și completează-l:

```bash
cp .env.example .env
```

```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=123456789
```

## 4. Rulare

```bash
python bot.py
```

La prima pornire, botul creează automat `data/shop.db`, tabelele necesare și
adaugă categoriile și produsele demo (Nike Hoodie, Basic T-Shirt, Cargo Pants,
Nike Air, Cap).

## 5. Structură proiect

```text
e_solutions_bot/
├── bot.py                  # entrypoint: pornește Dispatcher-ul și polling-ul
├── config.py                # citește .env, SHOP_NAME, texte About/Contact
├── database.py               # schema SQLite + seed date demo
├── utils.py                  # safe_edit() - editare mesaje fără crash pe erori Telegram
├── handlers/
│   ├── start.py              # /start, meniu principal, About, Contact
│   ├── products.py           # categorii, listă produse, detaliu produs, adaugă în coș
│   ├── cart.py                # coș (adaugă/scade/șterge) + checkout (FSM) + confirmare
│   ├── orders.py              # "Comenzile mele" pentru client
│   └── admin.py               # panou admin: comenzi, produse, statistici (doar ADMIN_ID)
├── keyboards/
│   ├── main_menu.py
│   ├── product_buttons.py
│   └── admin_buttons.py
├── services/
│   ├── product_service.py     # CRUD produse/categorii
│   ├── cart_service.py         # logică coș + verificare stoc
│   ├── order_service.py        # creare comandă (tranzacție atomică), statusuri, statistici
│   └── user_service.py         # upsert utilizator
├── tests/
│   └── test_flow.py            # teste automate pt. stoc/comenzi (vezi secțiunea Testare)
├── data/
│   └── shop.db                 # creat automat la prima rulare
├── .env.example
├── requirements.txt
└── README.md
```

> Notă: fișierul de date se numește `data/shop.db` (nu `database/shop.db`) ca să nu
> existe un conflict de nume cu modulul `database.py` de la rădăcina proiectului.

## 6. Flux principal (client)

`/start` → 🛍 Produse → categorie → produs → ➕ Adaugă în coș → 🛒 Coș →
✅ Plasează comanda → nume / telefon / adresă / observații → confirmare → comandă
salvată, stocul scade automat, coșul se golește, iar `ADMIN_ID` primește o notificare
cu detaliile comenzii.

## 7. Panou admin

Vizibil doar utilizatorului cu `ADMIN_ID` (buton „🛠 Admin Panel” în meniul principal):

- **📦 Comenzi** — listă comenzi, schimbare status (Confirmată / În procesare /
  Finalizată / Anulată); clientul primește notificare la schimbarea statusului.
- **🛍 Produse** — schimbă stoc/preț, activează/dezactivează un produs, adaugă produs nou.
- **📊 Statistici** — total comenzi, finalizate, vânzări, produse vândute, produs
  popular, produse cu stoc redus.

## 8. Testare

### Automat (nu necesită Telegram/rețea)

```bash
python tests/test_flow.py
```

Acoperă exact scenariile obligatorii ale MVP-ului:
1. stoc 5 → comandă 2 → stoc 3
2. stoc 2 → comandă 3 → refuz, stocul rămâne neschimbat
3. doi clienți concurează pentru ultimul produs → doar o comandă reușește (fără overselling)
4. anulare înainte de confirmare → stocul rămâne neschimbat
5. comandă confirmată → coșul se golește
6. adminul schimbă stocul → clientul vede noul stoc
7. produs inactiv → nu poate fi adăugat în coș / comandat

### Manual (flux complet în Telegram)

`/start` → Produse → o categorie → Nike Hoodie (stoc 5) → adaugă 2 → Plasează comanda →
completează date → Confirmă → verifică: comanda apare în `data/shop.db`, stocul devine 3,
adminul primește notificarea, iar din Admin Panel → Comenzi/Produse se văd comanda și
noul stoc.

## 9. MVP vs. producție

Acest proiect e un MVP de demonstrație. Înainte de utilizare comercială reală, ar trebui
adăugate: hardening de securitate, backup-uri, hosting dedicat, o bază de date pregătită
pentru producție (ex. PostgreSQL) dacă traficul crește, gestionare mai atentă a
concurenței la scară mare, monitorizare/alertare, politici de confidențialitate,
rate limiting și validare/sanitizare suplimentară a datelor introduse de utilizatori
(ex. caractere HTML speciale în nume/adresă).

Funcționalități intenționat **neincluse** în acest MVP (posibil de adăugat ulterior fără
a rescrie arhitectura): plăți reale, PostgreSQL, Telegram Mini App, website, CRM,
analytics avansat, promoții, wishlist, coș abandonat, loyalty, AI, integrări de livrare.
