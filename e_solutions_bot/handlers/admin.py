from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config import ADMIN_ID
from keyboards.admin_buttons import (
    admin_menu_kb, admin_orders_kb, admin_order_detail_kb,
    admin_products_kb, admin_product_detail_kb,
)
from services import order_service, product_service
from utils import safe_edit

router = Router()
# tot acest router e disponibil DOAR pentru ADMIN_ID (cerința #17)
router.message.filter(F.from_user.id == ADMIN_ID)
router.callback_query.filter(F.from_user.id == ADMIN_ID)


class AdminEditStates(StatesGroup):
    stock = State()
    price = State()
    add_name = State()
    add_description = State()
    add_price = State()
    add_category = State()
    add_stock = State()


@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(callback.message, "🛠 Admin Panel", reply_markup=admin_menu_kb())
    await callback.answer()


# ---------- COMENZI ----------

@router.callback_query(F.data == "admin:orders")
async def cb_admin_orders(callback: CallbackQuery):
    orders = order_service.get_all_orders()
    if not orders:
        await safe_edit(callback.message, "Nu există comenzi.", reply_markup=admin_menu_kb())
    else:
        await safe_edit(callback.message, "📦 Comenzi", reply_markup=admin_orders_kb(orders))
    await callback.answer()


def _order_detail_text(order):
    items_text = "\n".join(f"{i['product_name']} x{i['quantity']}" for i in order["items"])
    return (
        f"#{order['id']}\n"
        f"Client: {order['customer_name']}\n"
        f"Telefon: {order['phone']}\n"
        f"Adresă: {order['address']}\n\n"
        f"{items_text}\n\n"
        f"Total: {int(order['total_price'])} MDL\n"
        f"Status: {order['status']}"
    )


@router.callback_query(F.data.startswith("admin:order:"))
async def cb_admin_order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[2])
    order = order_service.get_order(order_id)
    if not order:
        await callback.answer("Comanda nu a fost găsită.", show_alert=True)
        return
    await safe_edit(callback.message, _order_detail_text(order), reply_markup=admin_order_detail_kb(order_id, order["status"]))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:setstatus:"))
async def cb_admin_set_status(callback: CallbackQuery):
    _, _, order_id, status = callback.data.split(":", 3)
    order_id = int(order_id)
    telegram_id = order_service.update_order_status(order_id, status)
    if telegram_id is None:
        await callback.answer("Comanda nu a fost găsită.", show_alert=True)
        return

    order = order_service.get_order(order_id)
    await safe_edit(callback.message, _order_detail_text(order), reply_markup=admin_order_detail_kb(order_id, order["status"]))
    await callback.answer(f"Status actualizat: {status}")

    try:
        await callback.bot.send_message(telegram_id, f"📦 Comanda #{order_id} are un nou status: {status}")
    except Exception:
        pass  # userul poate avea botul blocat - nu oprim fluxul adminului


# ---------- PRODUSE ----------

@router.callback_query(F.data == "admin:products")
async def cb_admin_products(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    products = product_service.get_all_products()
    await safe_edit(callback.message, "🛍 Produse", reply_markup=admin_products_kb(products))
    await callback.answer()


def _product_detail_text(p):
    status = "activ ✅" if p["is_active"] else "inactiv ❌"
    return f"<b>{p['name']}</b>\n{p['description'] or ''}\n\nPreț: {int(p['price'])} MDL\nStoc: {p['stock']}\nStatus: {status}"


@router.callback_query(F.data.startswith("admin:product:"))
async def cb_admin_product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[2])
    p = product_service.get_product(product_id)
    if not p:
        await callback.answer("Produsul nu a fost găsit.", show_alert=True)
        return
    await safe_edit(callback.message, _product_detail_text(p), reply_markup=admin_product_detail_kb(product_id, p["is_active"]))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:toggle:"))
async def cb_admin_toggle(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[2])
    new_val = product_service.toggle_active(product_id)
    if new_val is None:
        await callback.answer("Produsul nu a fost găsit.", show_alert=True)
        return
    p = product_service.get_product(product_id)
    await safe_edit(callback.message, _product_detail_text(p), reply_markup=admin_product_detail_kb(product_id, p["is_active"]))
    await callback.answer("Status actualizat.")


@router.callback_query(F.data.startswith("admin:editstock:"))
async def cb_admin_edit_stock_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[2])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminEditStates.stock)
    await safe_edit(callback.message, "Introdu noul stoc (număr întreg ≥ 0):")
    await callback.answer()


@router.message(AdminEditStates.stock)
async def admin_edit_stock_value(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Valoare invalidă. Introdu un număr întreg pentru stoc:")
        return
    data = await state.get_data()
    product_service.update_stock(data["product_id"], int(message.text.strip()))
    await state.clear()
    await message.answer("✅ Stoc actualizat.", reply_markup=admin_menu_kb())


@router.callback_query(F.data.startswith("admin:editprice:"))
async def cb_admin_edit_price_start(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split(":")[2])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminEditStates.price)
    await safe_edit(callback.message, "Introdu noul preț (MDL):")
    await callback.answer()


@router.message(AdminEditStates.price)
async def admin_edit_price_value(message: Message, state: FSMContext):
    try:
        price = float((message.text or "").strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Preț invalid. Introdu un număr pozitiv:")
        return
    data = await state.get_data()
    product_service.update_price(data["product_id"], price)
    await state.clear()
    await message.answer("✅ Preț actualizat.", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin:addproduct")
async def cb_admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminEditStates.add_name)
    await safe_edit(callback.message, "Nume produs nou:")
    await callback.answer()


@router.message(AdminEditStates.add_name)
async def admin_add_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Nume invalid. Introdu numele produsului:")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminEditStates.add_description)
    await message.answer("Descriere produs:")


@router.message(AdminEditStates.add_description)
async def admin_add_description(message: Message, state: FSMContext):
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(AdminEditStates.add_price)
    await message.answer("Preț (MDL):")


@router.message(AdminEditStates.add_price)
async def admin_add_price(message: Message, state: FSMContext):
    try:
        price = float((message.text or "").strip().replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Preț invalid. Introdu un număr pozitiv:")
        return
    await state.update_data(price=price)
    categories = product_service.get_categories()
    cat_list = "\n".join(f"{c['id']} — {c['name']}" for c in categories)
    await state.set_state(AdminEditStates.add_category)
    await message.answer(f"ID categorie:\n{cat_list}")


@router.message(AdminEditStates.add_category)
async def admin_add_category(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("ID invalid. Introdu ID-ul categoriei:")
        return
    category_id = int(message.text.strip())
    if not product_service.get_category(category_id):
        await message.answer("Categoria nu există. Introdu un ID valid:")
        return
    await state.update_data(category_id=category_id)
    await state.set_state(AdminEditStates.add_stock)
    await message.answer("Stoc inițial (număr întreg):")


@router.message(AdminEditStates.add_stock)
async def admin_add_stock(message: Message, state: FSMContext):
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Valoare invalidă. Introdu un număr întreg pentru stoc:")
        return
    data = await state.get_data()
    product_service.add_product(
        data["category_id"], data["name"], data["description"], data["price"], "", int(message.text.strip())
    )
    await state.clear()
    await message.answer("✅ Produs adăugat.", reply_markup=admin_menu_kb())


# ---------- STATISTICI ----------

@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery):
    s = order_service.get_statistics()
    text = (
        "📊 STATISTICI\n\n"
        f"Comenzi: {s['total_orders']}\n"
        f"Finalizate: {s['finished']}\n"
        f"Vânzări: {int(s['total_sales'])} MDL\n"
        f"Produse vândute: {s['sold_qty']}\n"
        f"Produs popular: {s['popular_product']}\n"
        f"Stoc redus: {s['low_stock']}"
    )
    await safe_edit(callback.message, text, reply_markup=admin_menu_kb())
    await callback.answer()
