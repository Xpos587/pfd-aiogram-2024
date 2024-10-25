from aiogram.enums import ChatType
from aiogram.types import Chat, User

from ..models import DBUser
from .base import BaseRepository


class UserRepository(BaseRepository[DBUser]):
    _entity = DBUser

    async def create_from_telegram(
        self, user: User, locale: str, chat: Chat
    ) -> DBUser:
        db_user: DBUser = DBUser(
            id=user.id,
            name=user.full_name,
            locale=locale,
            notifications=chat.type == ChatType.PRIVATE,
        )
        await self.commit(db_user)
        return db_user
