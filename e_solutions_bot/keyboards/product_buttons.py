from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_kb(categories):
    b = InlineKeyboardBuilder()
    for c in categories:
        b.button(text=c["name"], callback_data=f"category:{c['id']}")
    b.button(text="🔙 Meniu principal", callback_data="menu:main")
    b.adjust(1)
    return b.as_markup()


def products_kb(products):
    b = InlineKeyboardBuilder()
    for p in products:
        b.button(text=f"{p['name']} — {int(p['price'])} MDL", callback_data=f"product:{p['id']}")
    b.button(text="🔙 Categorii", callback_data="menu:products")
    b.adjust(1)
    return b.as_markup()


def product_detail_kb(product_id, category_id):
    b = InlineKeyboardBuilder()
    b.button(text="➕ Adaugă în coș", callback_data=f"addcart:{product_id}")
    b.button(text="🛒 Vezi coșul", callback_data="menu:cart")
    b.button(text="🔙 Înapoi", callback_data=f"category:{category_id}")
    b.adjust(1)
    return b.as_markup()


def cart_kb(items):
    b = InlineKeyboardBuilder()
    for i in items:
        b.row(
            InlineKeyboardButton(text="➖", callback_data=f"cart:dec:{i['item_id']}"),
            InlineKeyboardButton(text=i["name"][:18], callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"cart:inc:{i['item_id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"cart:del:{i['item_id']}"),
        )
    if items:
        b.row(InlineKeyboardButton(text="✅ Plasează comanda", callback_data="checkout:start"))
    b.row(InlineKeyboardButton(text="🔙 Meniu principal", callback_data="menu:main"))
    return b.as_markup()
