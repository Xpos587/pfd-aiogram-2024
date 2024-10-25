from typing import Any, Final

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram_i18n import I18nContext

from bot.filters import CallbackData as cbd
from bot.keyboards import Button, common_keyboard
from services.database import DBUser

router: Final[Router] = Router(name=__name__)


@router.message(Command("start"))
async def start_command(
    message: Message, i18n: I18nContext, user: DBUser
) -> Any:
    return await message.answer(
        text=i18n.start(name=user.mention),
        reply_markup=common_keyboard(
            rows=[
                (
                    Button(i18n.btn.orange(), callback_data=cbd.orange),
                    Button(i18n.btn.lime(), callback_data=cbd.lime),
                ),
                Button(
                    i18n.btn.source(),
                    url="https://github.com/Xpos587/aiogram-template",
                ),
            ]
        ),
    )


@router.callback_query()
async def handle_callbacks(
    query: CallbackQuery, i18n: I18nContext, callback_data: Any
) -> Any:
    await query.answer()  # Отвечаем на callback

    if callback_data == cbd.orange:
        await query.message.answer(i18n.msg.orange())
    elif callback_data == cbd.lime:
        await query.message.answer(i18n.msg.lime())
    else:
        await query.message.answer(
            i18n.msg.unknown()
        )  # На случай неизвестного callback
