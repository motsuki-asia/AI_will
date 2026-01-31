"""User model"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.creator import Creator


class AgeGroup(str, Enum):
    """Age group enumeration"""
    U13 = "u13"      # Under 13
    U18 = "u18"      # 13-17
    ADULT = "adult"  # 18+


class User(Base, TimestampMixin):
    """
    User model matching openapi.yaml User schema
    
    Fields:
        id: UUID primary key
        email: Unique email address
        password_hash: Hashed password (not exposed in API)
        display_name: Optional display name
        consent_at: Timestamp of terms/privacy consent
        age_verified_at: Timestamp of age verification
        age_group: Age category (u13, u18, adult)
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    consent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    age_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    age_group: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Relationships
    creator: Mapped[Optional["Creator"]] = relationship("Creator", back_populates="user", uselist=False)

    @property
    def consent_completed(self) -> bool:
        """Check if user has completed consent"""
        return self.consent_at is not None

    @property
    def age_verified(self) -> bool:
        """Check if user has verified age"""
        return self.age_verified_at is not None

    @property
    def onboarding_completed(self) -> bool:
        """Check if user has completed onboarding"""
        return self.consent_completed and self.age_verified

    def __repr__(self) -> str:
        return f"<User {self.email}>"
