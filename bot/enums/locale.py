from __future__ import annotations

from enum import StrEnum, auto


class Locale(StrEnum):
    US = auto()
    RU = auto()

    DEFAULT = RU
