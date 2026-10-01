from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(is_admin=False):
    b = InlineKeyboardBuilder()
    b.button(text="🛍 Produse", callback_data="menu:products")
    b.button(text="🛒 Coș", callback_data="menu:cart")
    b.button(text="📦 Comenzile mele", callback_data="menu:my_orders")
    b.button(text="ℹ️ Despre noi", callback_data="menu:about")
    b.button(text="📞 Contact", callback_data="menu:contact")
    if is_admin:
        b.button(text="🛠 Admin Panel", callback_data="admin:menu")
    b.adjust(1)
    return b.as_markup()


def back_to_main_kb():
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Meniu principal", callback_data="menu:main")
    return b.as_markup()
