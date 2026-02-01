"""ConversationMessage model - Individual messages in a conversation"""
import uuid
from datetime import datetime, timezone, timedelta
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
        'system': System message (e.g., generated image)

    content_type:
        'text': Regular text message
        'image': Generated scene image
    """
    __tablename__ = "conversation_messages"

    # 画像の有効期限（日数）
    IMAGE_EXPIRY_DAYS = 7

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
    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="text",
        comment="メッセージの種類: text, image",
    )
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="画像URL（content_type=imageの場合）",
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="画像の有効期限（1週間後に自動削除）",
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
    ROLE_SYSTEM = "system"

    CONTENT_TYPE_TEXT = "text"
    CONTENT_TYPE_IMAGE = "image"

    @property
    def is_from_user(self) -> bool:
        return self.role == self.ROLE_USER

    @property
    def is_from_character(self) -> bool:
        return self.role == self.ROLE_CHARACTER

    @property
    def is_image(self) -> bool:
        return self.content_type == self.CONTENT_TYPE_IMAGE

    @property
    def is_expired(self) -> bool:
        """画像が期限切れかどうか"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def days_until_expiry(self) -> Optional[int]:
        """有効期限までの残り日数"""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)

    @classmethod
    def create_image_message(
        cls,
        session_id: str,
        image_url: str,
        content: str = "シーン画像を生成しました",
    ) -> "ConversationMessage":
        """画像メッセージを作成"""
        now = datetime.now(timezone.utc)
        return cls(
            session_id=session_id,
            role=cls.ROLE_SYSTEM,
            content=content,
            content_type=cls.CONTENT_TYPE_IMAGE,
            image_url=image_url,
            expires_at=now + timedelta(days=cls.IMAGE_EXPIRY_DAYS),
            created_at=now,
        )

    def __repr__(self) -> str:
        preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<ConversationMessage {self.id} {self.role}: {preview}>"
