"""Auth schemas - matching openapi.yaml Auth components"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import User as UserModel


# =============================================================================
# Request Models
# =============================================================================


class RegisterRequest(BaseModel):
    """User registration request"""

    email: EmailStr = Field(..., description="メールアドレス")
    password: str = Field(..., min_length=8, description="パスワード（8文字以上）")


class LoginRequest(BaseModel):
    """Login request"""

    email: EmailStr = Field(..., description="メールアドレス")
    password: str = Field(..., description="パスワード")


class RefreshRequest(BaseModel):
    """Token refresh request"""

    refresh_token: str = Field(..., description="リフレッシュトークン")


class LogoutRequest(BaseModel):
    """Logout request"""

    refresh_token: Optional[str] = Field(None, description="無効化対象のリフレッシュトークン")


class ConsentRequest(BaseModel):
    """Consent request"""

    terms_version: str = Field(..., description="利用規約バージョン")
    privacy_version: str = Field(..., description="プライバシーポリシーバージョン")


class AgeVerifyRequest(BaseModel):
    """Age verification request"""

    birth_date: Optional[str] = Field(None, description="生年月日（YYYY-MM-DD）")
    age_group: Optional[Literal["u13", "u18", "adult"]] = Field(
        None, description="年齢区分（birth_dateの代替）"
    )


class UpdateMeRequest(BaseModel):
    """Profile update request"""

    display_name: Optional[str] = Field(None, min_length=1, max_length=50, description="表示名")


# =============================================================================
# Response Models
# =============================================================================


class Tokens(BaseModel):
    """Token pair"""

    access_token: str
    refresh_token: str
    expires_in: int = Field(..., description="有効期限（秒）")


class TokenResponse(BaseModel):
    """Token response (for refresh)"""

    tokens: Tokens


class User(BaseModel):
    """User object - matches openapi.yaml User schema"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    display_name: Optional[str] = None
    consent_at: Optional[datetime] = None
    age_verified_at: Optional[datetime] = None
    age_group: Optional[Literal["u13", "u18", "adult"]] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, user: UserModel) -> "User":
        """Create schema from SQLAlchemy model"""
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            consent_at=user.consent_at,
            age_verified_at=user.age_verified_at,
            age_group=user.age_group,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class Onboarding(BaseModel):
    """Onboarding status"""

    consent_completed: bool
    age_verified: bool
    completed: bool

    @classmethod
    def from_user(cls, user: UserModel) -> "Onboarding":
        """Create onboarding status from user model"""
        return cls(
            consent_completed=user.consent_completed,
            age_verified=user.age_verified,
            completed=user.onboarding_completed,
        )


class AuthResponse(BaseModel):
    """Auth response (register/login)"""

    user: User
    tokens: Tokens


class UserResponse(BaseModel):
    """User response (profile update)"""

    user: User


class MeResponse(BaseModel):
    """Current user response"""

    user: User
    onboarding: Onboarding


class ConsentResponse(BaseModel):
    """Consent response"""

    user: User
    onboarding: Onboarding


class Restrictions(BaseModel):
    """Age-based restrictions"""

    adult_content: bool
    purchase_limit: Optional[int] = Field(None, description="課金上限（円/月）")


class AgeVerifyResponse(BaseModel):
    """Age verification response"""

    user: User
    onboarding: Onboarding
    restrictions: Restrictions
