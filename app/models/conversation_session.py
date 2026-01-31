"""ConversationSession model - Thread for character conversations"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.character import Character
    from app.models.conversation_message import ConversationMessage


class ConversationSession(Base, TimestampMixin, SoftDeleteMixin):
    """
    ConversationSession model - represents a conversation thread

    session_type:
        'free': Regular free conversation
        'event': Event-driven conversation (future)
    """
    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("characters.id"),
        nullable=False,
        index=True,
    )
    pack_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("packs.id"),
        nullable=True,
        index=True,
    )
    session_type: Mapped[str] = mapped_column(
        String(20),
        default="free",
        nullable=False,
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", backref="conversation_sessions")
    character: Mapped["Character"] = relationship("Character", backref="conversation_sessions")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="session",
        order_by="ConversationMessage.created_at",
    )

    # Constants
    SESSION_TYPE_FREE = "free"
    SESSION_TYPE_EVENT = "event"

    @property
    def is_active(self) -> bool:
        return self.ended_at is None and not self.is_deleted

    @property
    def message_count(self) -> int:
        return len(self.messages) if self.messages else 0

    def __repr__(self) -> str:
        return f"<ConversationSession {self.id} user={self.user_id} char={self.character_id}>"
