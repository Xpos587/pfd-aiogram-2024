from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.filters import ChatStates

logger = logging.getLogger(__name__)


class StateControlMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        state: FSMContext = data["state"]

        logger.debug("State: %s", await state.get_state())

        if isinstance(event, CallbackQuery):
            await state.set_state(ChatStates.ReadyToRespond)
        elif hasattr(event, "message") and isinstance(
            getattr(event, "message"), Message
        ):
            message: Message = getattr(event, "message")
            if (
                message.text
                and message.text.startswith("/")
                and message.text != "/start"
            ):
                await message.delete()
                await state.set_state(ChatStates.ReadyToRespond)

        return await handler(event, data)
