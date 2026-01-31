"""Refresh token model for JWT token management"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefreshToken(Base):
    """
    Refresh token storage for secure token invalidation
    
    Strategy:
        - Store refresh tokens in DB for revocation capability
        - Each token has an expiry and revoked flag
        - On logout, revoke the token
        - On refresh, optionally rotate (create new, revoke old)
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        # Handle naive datetime from SQLite
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not revoked)"""
        return not self.is_expired and not self.revoked

    def revoke(self) -> None:
        """Revoke this token"""
        self.revoked = True
        self.revoked_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<RefreshToken user_id={self.user_id} revoked={self.revoked}>"
