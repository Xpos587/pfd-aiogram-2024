from typing import Final

from aiogram.filters import Filter, StateFilter
from aiogram.fsm.state import State, StatesGroup


class ChatStates(StatesGroup):
    ReadyToRespond = State()


NoneState: Final[Filter] = StateFilter(None)
AnyState: Final[Filter] = ~NoneState
