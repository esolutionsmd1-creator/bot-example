import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from config import ADMIN_ID, BOT_TOKEN, SHOP_NAME
from database import init_db
from handlers import admin, cart, orders, products, start

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN lipsește. Completează fișierul .env (vezi .env.example).")
        sys.exit(1)
    if not ADMIN_ID:
        logger.error("ADMIN_ID lipsește sau este invalid. Completează fișierul .env.")
        sys.exit(1)

    init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    @dp.error()
    async def error_handler(event: ErrorEvent):
        # cerința #22: botul nu trebuie să se oprească la erori normale de utilizator/Telegram
        logger.exception("Eroare neașteptată în handler: %s", event.exception)
        return True

    dp.include_router(start.router)
    dp.include_router(products.router)
    dp.include_router(cart.router)
    dp.include_router(orders.router)
    dp.include_router(admin.router)

    logger.info("%s bot pornește...", SHOP_NAME)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot oprit manual.")

