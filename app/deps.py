"""Dependencies for FastAPI dependency injection"""
from typing import Annotated, Optional

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import (
    ErrorCode,
    ForbiddenException,
    UnauthenticatedException,
    ValidationException,
)
from app.core.security import verify_access_token

# =============================================================================
# Security Dependencies
# =============================================================================

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> str:
    """
    Get current user ID from JWT token

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User ID from token

    Raises:
        UnauthenticatedException: If no token or invalid token
    """
    if not credentials:
        raise UnauthenticatedException()

    payload = verify_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthenticatedException()

    return user_id


async def get_optional_user_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> Optional[str]:
    """
    Get current user ID if authenticated, None otherwise

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User ID from token or None
    """
    if not credentials:
        return None

    try:
        payload = verify_access_token(credentials.credentials)
        return payload.get("sub")
    except UnauthenticatedException:
        return None


# Type aliases for dependency injection
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
OptionalUserId = Annotated[Optional[str], Depends(get_optional_user_id)]


# =============================================================================
# User State Dependencies (TODO: Implement with actual DB)
# =============================================================================


class UserState:
    """User state from database (placeholder)"""

    def __init__(
        self,
        user_id: str,
        consent_completed: bool = False,
        age_verified: bool = False,
        age_group: Optional[str] = None,
    ):
        self.user_id = user_id
        self.consent_completed = consent_completed
        self.age_verified = age_verified
        self.age_group = age_group

    @property
    def onboarding_completed(self) -> bool:
        return self.consent_completed and self.age_verified


async def get_current_user_state(user_id: CurrentUserId) -> UserState:
    """
    Get current user state from database

    TODO: Implement actual database lookup

    Args:
        user_id: Current user ID

    Returns:
        UserState object
    """
    # TODO: Fetch from database
    # For now, return a placeholder that passes all checks
    return UserState(
        user_id=user_id,
        consent_completed=True,
        age_verified=True,
        age_group="adult",
    )


CurrentUserState = Annotated[UserState, Depends(get_current_user_state)]


async def require_onboarding_completed(state: CurrentUserState) -> UserState:
    """
    Require user to have completed onboarding

    Args:
        state: Current user state

    Returns:
        UserState if onboarding completed

    Raises:
        ForbiddenException: If onboarding not completed
    """
    if not state.onboarding_completed:
        if not state.consent_completed:
            raise ForbiddenException(
                message="利用規約への同意が必要です",
                code=ErrorCode.CONSENT_REQUIRED,
            )
        if not state.age_verified:
            raise ForbiddenException(
                message="年齢確認が必要です",
                code=ErrorCode.ONBOARDING_REQUIRED,
            )
    return state


OnboardedUser = Annotated[UserState, Depends(require_onboarding_completed)]


# =============================================================================
# Idempotency Key Dependency
# =============================================================================


async def get_idempotency_key(
    idempotency_key: Annotated[Optional[str], Header(alias="Idempotency-Key")] = None,
) -> str:
    """
    Get and validate Idempotency-Key header

    Args:
        idempotency_key: Idempotency-Key header value

    Returns:
        Idempotency key

    Raises:
        ValidationException: If key is missing
    """
    if not idempotency_key:
        raise ValidationException(
            message="Idempotency-Key ヘッダーが必要です",
            details=[{"field": "Idempotency-Key", "code": "required", "message": "必須ヘッダーです"}],
        )
    return idempotency_key


IdempotencyKey = Annotated[str, Depends(get_idempotency_key)]


# =============================================================================
# Pagination Dependencies
# =============================================================================


class PaginationParams:
    """Pagination parameters"""

    def __init__(self, cursor: Optional[str] = None, limit: int = 20):
        self.cursor = cursor
        self.limit = min(max(limit, 1), 100)  # Clamp between 1 and 100


async def get_pagination(
    cursor: Optional[str] = None,
    limit: int = 20,
) -> PaginationParams:
    """Get pagination parameters"""
    return PaginationParams(cursor=cursor, limit=limit)


Pagination = Annotated[PaginationParams, Depends(get_pagination)]


# =============================================================================
# Sort Dependencies
# =============================================================================


class SortParams:
    """Sort parameters"""

    def __init__(self, sort: str = "created_at", order: str = "desc"):
        self.sort = sort
        self.order = order if order in ("asc", "desc") else "desc"


async def get_sort(
    sort: str = "created_at",
    order: str = "desc",
) -> SortParams:
    """Get sort parameters"""
    return SortParams(sort=sort, order=order)


Sort = Annotated[SortParams, Depends(get_sort)]
