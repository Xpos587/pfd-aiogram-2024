from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.filters import CallbackData

logger = logging.getLogger(__name__)


class QueryMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["callback_data"] = None
        if isinstance(event, Update) and event.callback_query:
            query = event.callback_query
            cb_data = query.data
            if not query.data:
                return await handler(event, data)

            for attribute in CallbackData:
                if cb_data.startswith(attribute.value) and (
                    len(cb_data) == len(attribute.value)
                    or cb_data[len(attribute.value)] == ":"
                ):
                    payload = cb_data.removeprefix(attribute.value).strip(":")
                    data["callback_data"] = attribute.value
                    if payload:
                        data["callback_data"] = (
                            int(payload) if payload.isdigit() else payload
                        )
                    break

        logger.debug(
            "CallbackData in middleware: %s", data.get("callback_data", "None")
        )
        return await handler(event, data)
