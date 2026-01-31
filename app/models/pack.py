"""Pack model - Persona/Scenario bundles"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, SmallInteger, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.creator import Creator
    from app.models.character import Character


class Pack(Base, TimestampMixin, SoftDeleteMixin):
    """
    Pack model - bundles of characters and content (Persona or Scenario)
    
    pack_type:
        'persona': Single character with personality
        'scenario': Story-driven content with events
    
    Status:
        1: draft
        2: published
        3: suspended
    
    age_rating:
        'all': All ages
        'r15': 15+
        'r18': 18+
    """
    __tablename__ = "packs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    creator_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("creators.id"),
        nullable=False,
    )
    pack_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    cover_image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    price: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    age_rating: Mapped[str] = mapped_column(
        String(10),
        default="all",
        nullable=False,
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        nullable=False,
    )

    # Relationships
    creator: Mapped["Creator"] = relationship("Creator", back_populates="packs")
    # Note: Pack-Character relationship is via PackItem (polymorphic), query via PackItem model

    # Constants
    TYPE_PERSONA = "persona"
    TYPE_SCENARIO = "scenario"
    
    STATUS_DRAFT = 1
    STATUS_PUBLISHED = 2
    STATUS_SUSPENDED = 3

    AGE_RATING_ALL = "all"
    AGE_RATING_R15 = "r15"
    AGE_RATING_R18 = "r18"

    @property
    def is_published(self) -> bool:
        return self.status == self.STATUS_PUBLISHED and not self.is_deleted

    @property
    def is_free(self) -> bool:
        return self.price is None or self.price == 0

    def __repr__(self) -> str:
        return f"<Pack {self.name} ({self.pack_type})>"
