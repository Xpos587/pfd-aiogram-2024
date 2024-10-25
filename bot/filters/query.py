from enum import StrEnum, auto
from typing import Any, Final

from aiogram import F


class CallbackData(StrEnum):
    orange: Final[auto] = auto()
    lime: Final[auto] = auto()

    def __call__(self):
        return (F.data == self.value) | (F.data.startswith(self.value + ":"))

    def extend(self, *args: Any) -> str:
        return self.value + ":" + ":".join(map(str, args))
