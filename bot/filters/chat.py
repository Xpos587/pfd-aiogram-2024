from typing import Final

from aiogram import F
from aiogram.enums import ChatType
from aiogram.filters import Filter

from bot.settings import settings

from .magic_data import MagicData

admin_ids = settings.get_admin_ids()


ADMIN_ONLY: Final[Filter] = MagicData(F.event_from_user.id.in_(set(admin_ids)))
PRIVATE_ONLY: Final[Filter] = MagicData(F.event_chat.type == ChatType.PRIVATE)
