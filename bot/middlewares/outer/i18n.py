from __future__ import annotations

from typing import TYPE_CHECKING, cast

from aiogram.types import User
from aiogram_i18n.managers import BaseManager

if TYPE_CHECKING:
    from services.database import DBUser, Repository


class UserManager(BaseManager):
    async def get_locale(
        self,
        event_from_user: User | None = None,
        user: DBUser | None = None,
    ) -> str:
        if user:
            return user.locale
        if event_from_user:
            return event_from_user.language_code or cast(str, self.default_locale)
        return cast(str, self.default_locale)

    async def set_locale(
        self, locale: str, user: DBUser, repository: Repository
    ) -> None:
        user.locale = locale
        await repository.commit(user)
