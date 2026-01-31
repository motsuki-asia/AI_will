"""PackItem model - association table between Pack and Character"""
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, SoftDeleteMixin


class PackItem(Base, TimestampMixin, SoftDeleteMixin):
    """
    PackItem - Links Packs to Characters (and other items in future)
    
    item_type:
        'character': A character in the pack
        'event': An event/scenario (future)
        'voice_pack': Voice assets (future)
    """
    __tablename__ = "pack_items"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    pack_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("packs.id"),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(
        String(30),
        default="character",
        nullable=False,
    )
    item_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger,
        default=0,
        nullable=False,
    )

    # Note: Polymorphic reference - FK constraint not enforced at DB level
    # Application layer must verify item_id exists in appropriate table

    # Constants
    ITEM_TYPE_CHARACTER = "character"
    ITEM_TYPE_EVENT = "event"
    ITEM_TYPE_VOICE_PACK = "voice_pack"

    def __repr__(self) -> str:
        return f"<PackItem pack={self.pack_id} {self.item_type}={self.item_id}>"
