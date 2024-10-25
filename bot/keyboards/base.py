from typing import Optional, Union

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    ReplyKeyboardBuilder,
)


class Button:
    def __init__(
        self,
        text: str,
        callback_data: Optional[str] = None,
        url: Optional[str] = None,
    ):
        self.text = text
        self.callback_data = callback_data
        self.url = url


def common_keyboard(
    rows: Union[list[Union[tuple[Button, ...], Button]]],
    is_inline: bool = True,
    is_persistent: Optional[bool] = None,
    resize_keyboard: bool = True,
    one_time_keyboard: Optional[bool] = None,
    input_field_placeholder: Optional[str] = None,
    selective: Optional[bool] = None,
) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]:
    """
    Common keyboards builder helper.
    """
    options = {
        "is_persistent": is_persistent,
        "resize_keyboard": resize_keyboard,
        "one_time_keyboard": one_time_keyboard,
        "input_field_placeholder": input_field_placeholder,
        "selective": selective,
    }

    if isinstance(rows, Button):
        rows = [rows]

    if is_inline:
        inline_keyboard = InlineKeyboardBuilder()
        for row in rows:
            if isinstance(row, Button):
                row = (row,)
            inline_keyboard.row(
                *[
                    InlineKeyboardButton(
                        text=button.text,
                        callback_data=button.callback_data,
                        url=button.url,
                    )
                    for button in row
                ]
            )
    else:
        reply_keyboard = ReplyKeyboardBuilder()
        for row in rows:
            if isinstance(row, Button):
                row = (row,)
            reply_keyboard.row(
                *[KeyboardButton(text=button.text) for button in row]
            )
    if is_inline:
        return inline_keyboard.as_markup(**options)
    return reply_keyboard.as_markup(**options)


__all__ = ["ReplyKeyboardRemove"]
