from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    Sequence,
    Type,
    TypeVar,
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

if TYPE_CHECKING:
    from ..models import Base

T = TypeVar("T", bound="Base")


class BaseRepository(Generic[T]):
    _session: AsyncSession
    _entity: Type[T]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self, *instances: Base) -> None:
        self._session.add_all(instances)
        await self._session.commit()

    async def delete(self, *instances: Base) -> None:
        for instance in instances:
            await self._session.delete(instance)
        await self._session.commit()

    async def get(self, **filters: dict[str, Any]) -> Optional[T]:
        query = select(self._entity).filter_by(**filters)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def get_many(self, **filters: dict[str, Any]) -> Sequence[T]:
        query = select(self._entity).filter_by(**filters)
        result = await self._session.execute(query)
        return result.scalars().all()
