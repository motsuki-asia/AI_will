"""Authentication service"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import (
    ConflictException,
    ErrorCode,
    UnauthenticatedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_refresh_token,
)
from app.models.user import User
from app.models.refresh_token import RefreshToken


class AuthService:
    """Authentication service handling user registration, login, and token management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # User Registration
    # =========================================================================

    async def register(self, email: str, password: str) -> Tuple[User, str, str]:
        """
        Register a new user

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (User, access_token, refresh_token)

        Raises:
            ConflictException: If email already exists
        """
        # Check if email exists
        existing = await self._get_user_by_email(email)
        if existing:
            raise ConflictException(
                message="このメールアドレスは既に登録されています",
                code=ErrorCode.CONFLICT,
            )

        # Create user
        user = User(
            email=email,
            password_hash=get_password_hash(password),
        )
        self.db.add(user)
        await self.db.flush()

        # Generate tokens
        access_token, refresh_token = await self._create_tokens(user)

        return user, access_token, refresh_token

    # =========================================================================
    # User Login
    # =========================================================================

    async def login(self, email: str, password: str) -> Tuple[User, str, str]:
        """
        Authenticate user and return tokens

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (User, access_token, refresh_token)

        Raises:
            UnauthenticatedException: If credentials are invalid
        """
        # Get user
        user = await self._get_user_by_email(email)
        if not user:
            raise UnauthenticatedException(
                message="メールアドレスまたはパスワードが正しくありません",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        # Verify password
        if not verify_password(password, user.password_hash):
            raise UnauthenticatedException(
                message="メールアドレスまたはパスワードが正しくありません",
                code=ErrorCode.INVALID_CREDENTIALS,
            )

        # Generate tokens
        access_token, refresh_token = await self._create_tokens(user)

        return user, access_token, refresh_token

    # =========================================================================
    # Token Refresh
    # =========================================================================

    async def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: The refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            UnauthenticatedException: If refresh token is invalid
        """
        # Verify JWT structure
        try:
            payload = verify_refresh_token(refresh_token)
            user_id = payload.get("sub")
        except UnauthenticatedException:
            raise

        # Check token in database
        token_hash = self._hash_token(refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == user_id,
            )
        )
        stored_token = result.scalar_one_or_none()

        if not stored_token or not stored_token.is_valid:
            raise UnauthenticatedException(
                message="無効なリフレッシュトークンです",
                code=ErrorCode.INVALID_REFRESH_TOKEN,
            )

        # Get user
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UnauthenticatedException(
                message="ユーザーが見つかりません",
                code=ErrorCode.UNAUTHENTICATED,
            )

        # Revoke old token and create new ones (token rotation)
        stored_token.revoke()

        access_token, new_refresh_token = await self._create_tokens(user)

        return access_token, new_refresh_token

    # =========================================================================
    # Logout
    # =========================================================================

    async def logout(self, user_id: str, refresh_token: Optional[str] = None) -> None:
        """
        Logout user by revoking refresh token(s)

        Args:
            user_id: User ID
            refresh_token: Optional specific token to revoke (revokes all if None)
        """
        if refresh_token:
            # Revoke specific token
            token_hash = self._hash_token(refresh_token)
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.user_id == user_id,
                )
            )
            stored_token = result.scalar_one_or_none()
            if stored_token:
                stored_token.revoke()
        else:
            # Revoke all tokens for user
            result = await self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked == False,
                )
            )
            tokens = result.scalars().all()
            for token in tokens:
                token.revoke()

    # =========================================================================
    # User Management
    # =========================================================================

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user(
        self,
        user_id: str,
        display_name: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update user profile

        Args:
            user_id: User ID
            display_name: New display name (if provided)

        Returns:
            Updated user or None if not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        if display_name is not None:
            user.display_name = display_name

        await self.db.flush()
        return user

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def _create_tokens(self, user: User) -> Tuple[str, str]:
        """Create access and refresh tokens for user"""
        # Create access token
        access_token = create_access_token(subject=user.id)

        # Create refresh token
        refresh_token = create_refresh_token(subject=user.id)

        # Store refresh token hash in database
        token_hash = self._hash_token(refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        stored_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(stored_token)

        return access_token, refresh_token

    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash a token for storage (don't store raw tokens)"""
        return hashlib.sha256(token.encode()).hexdigest()
