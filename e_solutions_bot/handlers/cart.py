import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import ADMIN_ID
from keyboards.product_buttons import cart_kb
from services import cart_service, order_service
from utils import safe_edit

logger = logging.getLogger(__name__)
router = Router()


class CheckoutStates(StatesGroup):
    name = State()
    phone = State()
    address = State()
    notes = State()
    confirm = State()


def _cart_text(items, total):
    if not items:
        return "🛒 Coșul tău este gol."
    lines = ["🛒 Coșul tău\n"]
    for i in items:
        lines.append(f"{i['name']}\n{int(i['price'])} MDL x{i['quantity']} = {int(i['price'] * i['quantity'])} MDL\n")
    lines.append(f"Total: {int(total)} MDL")
    return "\n".join(lines)


async def _refresh_cart(message, telegram_id):
    items = cart_service.get_cart_items(telegram_id)
    total = cart_service.get_cart_total(telegram_id)
    await safe_edit(message, _cart_text(items, total), reply_markup=cart_kb(items))


@router.callback_query(F.data == "menu:cart")
async def cb_view_cart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _refresh_cart(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("cart:inc:"))
async def cb_cart_inc(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[2])
    ok, msg = cart_service.change_quantity(callback.from_user.id, item_id, +1)
    if not ok:
        await callback.answer(msg, show_alert=True)
        return
    await _refresh_cart(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("cart:dec:"))
async def cb_cart_dec(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[2])
    ok, msg = cart_service.change_quantity(callback.from_user.id, item_id, -1)
    if not ok:
        await callback.answer(msg, show_alert=True)
        return
    await _refresh_cart(callback.message, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("cart:del:"))
async def cb_cart_del(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[2])
    cart_service.remove_item(callback.from_user.id, item_id)
    await _refresh_cart(callback.message, callback.from_user.id)
    await callback.answer("Produs eliminat.")


@router.callback_query(F.data == "checkout:start")
async def cb_checkout_start(callback: CallbackQuery, state: FSMContext):
    items = cart_service.get_cart_items(callback.from_user.id)
    if not items:
        await callback.answer("Coșul este gol.", show_alert=True)
        return
    await state.set_state(CheckoutStates.name)
    await safe_edit(callback.message, "Te rog introdu numele tău complet:")
    await callback.answer()


@router.message(CheckoutStates.name)
async def checkout_name(message: Message, state: FSMContext):
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("Nume invalid. Introdu numele tău complet:")
        return
    await state.update_data(customer_name=message.text.strip())
    await state.set_state(CheckoutStates.phone)
    await message.answer("Introdu numărul de telefon:")


@router.message(CheckoutStates.phone)
async def checkout_phone(message: Message, state: FSMContext):
    phone = (message.text or "").strip()
    if len(phone) < 6:
        await message.answer("Telefon invalid. Introdu un număr valid:")
        return
    await state.update_data(phone=phone)
    await state.set_state(CheckoutStates.address)
    await message.answer("Introdu adresa / localitatea:")


@router.message(CheckoutStates.address)
async def checkout_address(message: Message, state: FSMContext):
    address = (message.text or "").strip()
    if len(address) < 3:
        await message.answer("Adresă invalidă. Introdu adresa / localitatea:")
        return
    await state.update_data(address=address)
    await state.set_state(CheckoutStates.notes)
    await message.answer('Observații opționale (sau scrie "-" dacă nu ai):')


@router.message(CheckoutStates.notes)
async def checkout_notes(message: Message, state: FSMContext):
    notes = (message.text or "").strip()
    if notes == "-":
        notes = ""
    await state.update_data(notes=notes)
    data = await state.get_data()

    items = cart_service.get_cart_items(message.from_user.id)
    total = cart_service.get_cart_total(message.from_user.id)

    lines = ["📋 Confirmă comanda\n"]
    for i in items:
        lines.append(f"{i['name']} x{i['quantity']} = {int(i['price'] * i['quantity'])} MDL")
    lines.append(f"\nTotal: {int(total)} MDL")
    lines.append(f"\nNume: {data['customer_name']}")
    lines.append(f"Telefon: {data['phone']}")
    lines.append(f"Adresă: {data['address']}")
    if notes:
        lines.append(f"Observații: {notes}")
    lines.append("\n💳 Metodă de plată: Plata la livrare")

    b = InlineKeyboardBuilder()
    b.button(text="✅ Confirmă", callback_data="checkout:confirm")
    b.button(text="❌ Anulează", callback_data="checkout:cancel")
    b.adjust(2)

    await state.set_state(CheckoutStates.confirm)
    await message.answer("\n".join(lines), reply_markup=b.as_markup())


@router.callback_query(F.data == "checkout:cancel", CheckoutStates.confirm)
async def cb_checkout_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(callback.message, "❌ Comanda a fost anulată. Coșul tău a rămas neschimbat.")
    await callback.answer()


@router.callback_query(F.data == "checkout:confirm", CheckoutStates.confirm)
async def cb_checkout_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ok, result = order_service.create_order(
        callback.from_user.id,
        data.get("customer_name", ""),
        data.get("phone", ""),
        data.get("address", ""),
        data.get("notes", ""),
    )
    await state.clear()

    if not ok:
        await safe_edit(callback.message, f"⚠️ {result}")
        await callback.answer()
        return

    order = result
    await safe_edit(
        callback.message,
        f"✅ Comanda a fost plasată!\n\n"
        f"#{order['id']}\n"
        f"Total: {int(order['total_price'])} MDL\n\n"
        f"Vei fi contactat pentru confirmarea livrării.",
    )
    await callback.answer()

    try:
        items_text = "\n".join(f"{i['name']} x{i['quantity']}" for i in order["items"])
        admin_text = (
            f"🛍 COMANDĂ NOUĂ\n\n"
            f"#{order['id']}\n"
            f"Client: {order['customer_name']}\n"
            f"Telefon: {order['phone']}\n"
            f"Adresă: {order['address']}\n\n"
            f"{items_text}\n\n"
            f"Total: {int(order['total_price'])} MDL\n"
            f"Status: Nouă"
        )
        await callback.bot.send_message(ADMIN_ID, admin_text)
    except Exception:
        logger.exception("Nu s-a putut notifica adminul despre comanda noua.")
