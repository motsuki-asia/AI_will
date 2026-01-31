"""SQLAlchemy Base class and common mixins"""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class TimestampMixin:
    """Mixin for created_at/updated_at timestamps"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
