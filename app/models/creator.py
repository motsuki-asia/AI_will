"""Creator model"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.pack import Pack
    from app.models.character import Character


class Creator(Base, TimestampMixin, SoftDeleteMixin):
    """
    Creator model - content creators who publish Packs and Characters
    
    Status:
        1: active
        2: suspended
        3: banned
    """
    __tablename__ = "creators"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    bio: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="creator")
    packs: Mapped[list["Pack"]] = relationship("Pack", back_populates="creator")
    characters: Mapped[list["Character"]] = relationship("Character", back_populates="creator")

    # Status constants
    STATUS_ACTIVE = 1
    STATUS_SUSPENDED = 2
    STATUS_BANNED = 3

    @property
    def is_active(self) -> bool:
        return self.status == self.STATUS_ACTIVE and not self.is_deleted

    def __repr__(self) -> str:
        return f"<Creator {self.display_name}>"
