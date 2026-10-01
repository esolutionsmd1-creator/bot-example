from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.main_menu import back_to_main_kb
from services import order_service
from utils import safe_edit

router = Router()


@router.callback_query(F.data == "menu:my_orders")
async def cb_my_orders(callback: CallbackQuery):
    orders = order_service.get_user_orders(callback.from_user.id)
    if not orders:
        await safe_edit(callback.message, "📦 Nu ai nicio comandă încă.", reply_markup=back_to_main_kb())
        await callback.answer()
        return

    lines = ["📦 Comenzile mele\n"]
    for o in orders:
        lines.append(f"#{o['id']} — {o['status']} — {int(o['total_price'])} MDL")
    await safe_edit(callback.message, "\n".join(lines), reply_markup=back_to_main_kb())
    await callback.answer()
