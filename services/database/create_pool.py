from __future__ import annotations

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_pool(
    dsn: str | URL, enable_logging: bool = False
) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(url=dsn, echo=enable_logging)
    return async_sessionmaker(engine, expire_on_commit=False)
