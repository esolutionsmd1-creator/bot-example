from aiogram import Router, F
from aiogram.types import CallbackQuery

from keyboards.main_menu import back_to_main_kb
from keyboards.product_buttons import categories_kb, products_kb, product_detail_kb
from services import product_service, cart_service
from utils import safe_edit

router = Router()


@router.callback_query(F.data == "menu:products")
async def cb_categories(callback: CallbackQuery):
    categories = product_service.get_categories()
    if not categories:
        await safe_edit(callback.message, "Momentan nu există categorii.", reply_markup=back_to_main_kb())
    else:
        await safe_edit(callback.message, "🛍 Alege o categorie:", reply_markup=categories_kb(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("category:"))
async def cb_category_products(callback: CallbackQuery):
    category_id = int(callback.data.split(":")[1])
    category = product_service.get_category(category_id)
    if not category:
        await callback.answer("Categoria nu mai există.", show_alert=True)
        return

    products = product_service.get_products_by_category(category_id)
    if not products:
        await safe_edit(
            callback.message,
            f"{category['name']}\n\nNu sunt produse disponibile momentan.",
            reply_markup=categories_kb(product_service.get_categories()),
        )
    else:
        await safe_edit(callback.message, category["name"], reply_markup=products_kb(products))
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def cb_product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = product_service.get_product(product_id)
    if not product or not product["is_active"]:
        await callback.answer("Produsul nu mai este disponibil.", show_alert=True)
        return

    text = (
        f"<b>{product['name']}</b>\n"
        f"{product['description'] or ''}\n\n"
        f"💰 {int(product['price'])} MDL\n"
        f"📦 Stoc: {product['stock']}"
    )
    await safe_edit(callback.message, text, reply_markup=product_detail_kb(product_id, product["category_id"]))
    await callback.answer()


@router.callback_query(F.data.startswith("addcart:"))
async def cb_add_to_cart(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    ok, msg = cart_service.add_to_cart(callback.from_user.id, product_id, 1)
    await callback.answer(msg, show_alert=not ok)
