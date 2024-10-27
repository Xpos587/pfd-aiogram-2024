from typing import Any, Final
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputMediaPhoto, CallbackQuery
from aiogram_i18n import I18nContext
from assets import image

from bot.filters import CallbackData as cbd, ChatStates
from bot.keyboards import Button, common_keyboard

router: Final[Router] = Router(name=__name__)


@router.message(Command("start"))
@router.callback_query(cbd.main())
async def start_command(
    object: CallbackQuery | Message,
    i18n: I18nContext,
    state: FSMContext,
) -> Any:
    await state.clear()

    reply_markup = common_keyboard(
        rows=[
            (
                Button(i18n.btn.faq(), callback_data=cbd.faq),
                Button(i18n.btn.ask(), callback_data=cbd.ask),
            ),
            Button(
                i18n.btn.source(),
                url="https://github.com/pfd-aiogram-2024",
            ),
        ]
    )

    if isinstance(object, CallbackQuery):
        message: Message = getattr(object, "message")
        return await message.edit_media(
            media=InputMediaPhoto(media=image.start, caption=i18n.start()),
            reply_markup=reply_markup,
        )

    message = object
    return message.answer_photo(
        photo=image.start, caption=i18n.start(), reply_markup=reply_markup
    )


@router.callback_query(cbd.faq())
async def handle_faq(
    query: CallbackQuery, i18n: I18nContext, state: FSMContext
) -> Any:
    await state.clear()
    await query.message.edit_media(
        media=InputMediaPhoto(
            media=image.faq,  # Убедитесь, что у вас есть соответствующее изображение
            caption=i18n.msg.faq(),
        ),
        reply_markup=common_keyboard(
            rows=[Button(i18n.btn.back(), callback_data=cbd.main)]
        ),
    )


@router.callback_query(cbd.ask())
async def handle_ask(
    query: CallbackQuery, i18n: I18nContext, state: FSMContext
) -> Any:
    await state.set_state(ChatStates.AwaitingQuestion)
    await query.message.edit_media(
        media=InputMediaPhoto(
            media=image.chat,  # Убедитесь, что у вас есть соответствующее изображение
            caption=i18n.msg.ask(),
        ),
        reply_markup=common_keyboard(
            rows=[Button(i18n.btn.back(), callback_data=cbd.main)]
        ),
    )
