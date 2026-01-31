"""Security utilities - JWT authentication"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.errors import ErrorCode, UnauthenticatedException

# =============================================================================
# Password Hashing (using bcrypt directly for Python 3.13 compatibility)
# =============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a password"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


# =============================================================================
# JWT Token Handling
# =============================================================================


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create JWT access token

    Args:
        subject: Token subject (usually user_id)
        expires_delta: Token expiration time
        additional_claims: Additional JWT claims

    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT refresh token

    Args:
        subject: Token subject (usually user_id)
        expires_delta: Token expiration time

    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        UnauthenticatedException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise UnauthenticatedException(
                message="トークンの有効期限が切れています",
                code=ErrorCode.TOKEN_EXPIRED,
            )
        raise UnauthenticatedException(
            message="無効なトークンです",
            code=ErrorCode.UNAUTHENTICATED,
        )


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify access token

    Args:
        token: JWT access token

    Returns:
        Decoded token payload

    Raises:
        UnauthenticatedException: If token is invalid or not an access token
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise UnauthenticatedException(
            message="無効なアクセストークンです",
            code=ErrorCode.UNAUTHENTICATED,
        )
    return payload


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """
    Verify refresh token

    Args:
        token: JWT refresh token

    Returns:
        Decoded token payload

    Raises:
        UnauthenticatedException: If token is invalid or not a refresh token
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise UnauthenticatedException(
            message="無効なリフレッシュトークンです",
            code=ErrorCode.INVALID_REFRESH_TOKEN,
        )
    return payload
