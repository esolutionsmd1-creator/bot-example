"""Utilitare comune pentru handlere (cerința #22 - error handling)."""
import logging

from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


async def safe_edit(message, text, reply_markup=None, parse_mode=None):
    """Editează un mesaj ignorând eroarea inofensivă 'message is not modified'
    (apare când userul apasă un buton care nu schimbă conținutul) și logând
    orice altă eroare de Telegram API fără a opri botul."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.exception("Eroare la editarea mesajului.")
    except Exception:
        logger.exception("Eroare neașteptată la editarea mesajului.")
