from enum import StrEnum, auto
from typing import Any, Final

from aiogram import F
from aiogram.filters import BaseFilter


class CallbackData(StrEnum):
    main: Final[str] = auto()
    faq: Final[str] = auto()
    ask: Final[str] = auto()
    like: Final[str] = auto()
    dislike: Final[str] = auto()

    def __call__(self, *args: Any, **kwargs: Any) -> BaseFilter:
        """Create a filter for callback data."""
        return (F.data == self.value) | (F.data.startswith(f"{self.value}:"))

    def extend(self, *args: Any) -> str:
        return self.value + ":" + ":".join(map(str, args))
