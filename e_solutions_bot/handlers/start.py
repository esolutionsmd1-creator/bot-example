from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import SHOP_NAME, ABOUT_TEXT, CONTACT_TEXT, ADMIN_ID
from keyboards.main_menu import main_menu_kb, back_to_main_kb
from services import user_service
from utils import safe_edit

router = Router()

WELCOME_TEXT = (
    f"👋 Bine ai venit la {SHOP_NAME}!\n\n"
    "Aici poți vedea produsele noastre, poți adăuga în coș și plasa o comandă direct din Telegram."
)


def _is_admin(user_id):
    return user_id == ADMIN_ID


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_service.get_or_create_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb(_is_admin(message.from_user.id)))


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(callback: CallbackQuery):
    await safe_edit(callback.message, WELCOME_TEXT, reply_markup=main_menu_kb(_is_admin(callback.from_user.id)))
    await callback.answer()


@router.callback_query(F.data == "menu:about")
async def cb_about(callback: CallbackQuery):
    await safe_edit(callback.message, ABOUT_TEXT, reply_markup=back_to_main_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:contact")
async def cb_contact(callback: CallbackQuery):
    await safe_edit(callback.message, CONTACT_TEXT, reply_markup=back_to_main_kb())
    await callback.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()
