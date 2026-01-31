"""ReportReason model - Master data for report reasons"""
import uuid

from sqlalchemy import String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ReportReason(Base, TimestampMixin):
    """
    ReportReason - Master data for report reasons
    """
    __tablename__ = "m_report_reasons"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    reason_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )
    label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger,
        default=0,
        nullable=False,
    )

    # Predefined reason codes
    CODE_VIOLENT = "violent"
    CODE_INAPPROPRIATE = "inappropriate"
    CODE_SPAM = "spam"
    CODE_HARASSMENT = "harassment"
    CODE_OTHER = "other"

    def __repr__(self) -> str:
        return f"<ReportReason {self.reason_code}>"
