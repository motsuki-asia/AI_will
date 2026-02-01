"""Character model"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.creator import Creator
    from app.models.pack import Pack
    from app.models.user import User


class Character(Base, TimestampMixin, SoftDeleteMixin):
    """
    Character model - AI personas for conversation
    
    Status:
        1: draft
        2: published
        3: suspended
    
    Characters can be:
    - Creator-owned: creator_id is set, user_id is NULL
    - User-owned (custom): user_id is set, creator_id is NULL
    """
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    creator_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("creators.id"),
        nullable=True,  # NULL for user-created characters
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,  # NULL for creator-owned characters
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    system_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="顔アップ画像URL（アイコン・背景用）",
    )
    full_body_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="立ち絵画像URL",
    )
    appearance_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="キャラクターの外見詳細記述（画像生成の一貫性のため）",
    )
    voice_id: Mapped[str] = mapped_column(
        String(20),
        default="nova",
        nullable=False,
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        nullable=False,
    )

    # Relationships
    creator: Mapped[Optional["Creator"]] = relationship("Creator", back_populates="characters")
    owner: Mapped[Optional["User"]] = relationship("User", backref="custom_characters")
    # Note: Pack-Character relationship is via PackItem (polymorphic), query via PackItem model

    # Constants
    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_SUSPENDED = 3

    @property
    def is_published(self) -> bool:
        return self.status == self.STATUS_PUBLISHED and not self.is_deleted

    def __repr__(self) -> str:
        return f"<Character {self.name}>"
