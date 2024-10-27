from typing import Final

from aiogram import Router

from . import start, chat

router: Final[Router] = Router(name=__name__)
router.include_routers(start.router, chat.router)
