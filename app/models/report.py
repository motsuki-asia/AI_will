"""Report model - User reports for safety"""
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Report(Base, TimestampMixin):
    """
    Report model - User reports for inappropriate content

    target_type:
        'character': Reporting a character
        'conversation_message': Reporting a specific message
        'creator': Reporting a creator

    status:
        1: open (new report)
        2: in_progress (being reviewed)
        3: resolved (action taken)
        4: rejected (no action needed)
    """
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    reporter_user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,  # Can be null if user is deleted
    )
    reason_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("m_report_reasons.id"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    target_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
    )
    detail: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        default=1,
        nullable=False,
    )

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_user_id])
    reason = relationship("ReportReason")

    # Constants
    TARGET_TYPE_CHARACTER = "character"
    TARGET_TYPE_MESSAGE = "conversation_message"
    TARGET_TYPE_CREATOR = "creator"

    STATUS_OPEN = 1
    STATUS_IN_PROGRESS = 2
    STATUS_RESOLVED = 3
    STATUS_REJECTED = 4

    def __repr__(self) -> str:
        return f"<Report {self.id} {self.target_type}:{self.target_id}>"
