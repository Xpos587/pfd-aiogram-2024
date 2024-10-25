from typing import Annotated, TypeAlias, TypeVar

from sqlalchemy import BigInteger, DateTime, Integer, event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Mapper,
    mapped_column,
    registry,
)

from utils.timeflow import datetime, now_tz

Int16: TypeAlias = Annotated[int, 16]
Int64: TypeAlias = Annotated[int, 64]


class Base(DeclarativeBase):
    registry = registry(type_annotation_map={Int16: Integer, Int64: BigInteger})


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_tz
    )


T = TypeVar("T", bound="TimestampMixin")


@event.listens_for(TimestampMixin, "before_update", propagate=True)
def timestamp_before_update(
    mapper: Mapper[T], connection: Connection, target: TimestampMixin
) -> None:
    target.updated_at = now_tz()
