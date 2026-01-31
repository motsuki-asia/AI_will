"""ConversationMessage model - Individual messages in a conversation"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.conversation_session import ConversationSession


class ConversationMessage(Base):
    """
    ConversationMessage model - individual chat messages

    Note: No TimestampMixin (no updated_at) - messages are immutable
    Note: No SoftDeleteMixin - messages are permanent record

    role:
        'user': Message from user
        'character': Message from AI character (assistant)
    """
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation_sessions.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    session: Mapped["ConversationSession"] = relationship(
        "ConversationSession",
        back_populates="messages",
    )

    # Constants
    ROLE_USER = "user"
    ROLE_CHARACTER = "character"

    @property
    def is_from_user(self) -> bool:
        return self.role == self.ROLE_USER

    @property
    def is_from_character(self) -> bool:
        return self.role == self.ROLE_CHARACTER

    def __repr__(self) -> str:
        preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<ConversationMessage {self.id} {self.role}: {preview}>"
