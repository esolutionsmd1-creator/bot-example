from aiogram.utils.keyboard import InlineKeyboardBuilder

STATUS_OPTIONS = [
    ("✅ Confirmată", "Confirmată"),
    ("🚚 În procesare", "În procesare"),
    ("✅ Finalizată", "Finalizată"),
    ("❌ Anulată", "Anulată"),
]


def admin_menu_kb():
    b = InlineKeyboardBuilder()
    b.button(text="📦 Comenzi", callback_data="admin:orders")
    b.button(text="🛍 Produse", callback_data="admin:products")
    b.button(text="📊 Statistici", callback_data="admin:stats")
    b.button(text="🔙 Meniu principal", callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()


def admin_orders_kb(orders):
    b = InlineKeyboardBuilder()
    for o in orders:
        b.button(
            text=f"#{o['id']} — {o['status']} — {int(o['total_price'])} MDL",
            callback_data=f"admin:order:{o['id']}",
        )
    b.button(text="🔙 Admin Panel", callback_data="admin:menu")
    b.adjust(1)
    return b.as_markup()


def admin_order_detail_kb(order_id, current_status):
    b = InlineKeyboardBuilder()
    for label, status in STATUS_OPTIONS:
        if status != current_status:
            b.button(text=label, callback_data=f"admin:setstatus:{order_id}:{status}")
    b.button(text="🔙 Comenzi", callback_data="admin:orders")
    b.adjust(1)
    return b.as_markup()


def admin_products_kb(products):
    b = InlineKeyboardBuilder()
    for p in products:
        icon = "🟢" if p["is_active"] else "🔴"
        b.button(text=f"{icon} {p['name']} — stoc {p['stock']}", callback_data=f"admin:product:{p['id']}")
    b.button(text="➕ Adaugă produs", callback_data="admin:addproduct")
    b.button(text="🔙 Admin Panel", callback_data="admin:menu")
    b.adjust(1)
    return b.as_markup()


def admin_product_detail_kb(product_id, is_active):
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Schimbă stoc", callback_data=f"admin:editstock:{product_id}")
    b.button(text="💰 Schimbă preț", callback_data=f"admin:editprice:{product_id}")
    b.button(
        text="🔴 Dezactivează" if is_active else "🟢 Activează",
        callback_data=f"admin:toggle:{product_id}",
    )
    b.button(text="🔙 Produse", callback_data="admin:products")
    b.adjust(1)
    return b.as_markup()
