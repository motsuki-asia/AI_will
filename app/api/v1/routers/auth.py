"""Auth router - matching openapi.yaml Auth paths"""
from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import NotFoundException
from app.db.database import get_db
from app.deps import CurrentUserId
from app.schemas.auth import (
    AgeVerifyRequest,
    AgeVerifyResponse,
    AuthResponse,
    ConsentRequest,
    ConsentResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    Onboarding,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    Tokens,
    UpdateMeRequest,
    User,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService"""
    return AuthService(db)


# =============================================================================
# POST /auth/register - ユーザー登録
# =============================================================================
@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー登録",
    description="メールアドレスとパスワードで新規ユーザーを登録します。",
    responses={
        400: {"description": "バリデーションエラー"},
        409: {"description": "メールアドレス重複"},
    },
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """ユーザー登録"""
    user, access_token, refresh_token = await auth_service.register(
        email=request.email,
        password=request.password,
    )

    return AuthResponse(
        user=User.from_model(user),
        tokens=Tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


# =============================================================================
# POST /auth/login - ログイン
# =============================================================================
@router.post(
    "/login",
    response_model=AuthResponse,
    summary="ログイン",
    description="メールアドレスとパスワードでログインします。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証失敗"},
        423: {"description": "アカウントロック"},
    },
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """ログイン"""
    user, access_token, refresh_token = await auth_service.login(
        email=request.email,
        password=request.password,
    )

    return AuthResponse(
        user=User.from_model(user),
        tokens=Tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


# =============================================================================
# POST /auth/refresh - トークン更新
# =============================================================================
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="トークン更新",
    description="リフレッシュトークンを使用してアクセストークンを更新します。",
    responses={
        401: {"description": "トークン無効"},
    },
)
async def refresh_token(
    request: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """トークン更新"""
    access_token, new_refresh_token = await auth_service.refresh_tokens(
        refresh_token=request.refresh_token,
    )

    return TokenResponse(
        tokens=Tokens(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
    )


# =============================================================================
# POST /auth/logout - ログアウト
# =============================================================================
@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ログアウト",
    description="リフレッシュトークンを無効化してログアウトします。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def logout(
    user_id: CurrentUserId,
    request: Optional[LogoutRequest] = None,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """ログアウト"""
    refresh_token = request.refresh_token if request else None
    await auth_service.logout(user_id=user_id, refresh_token=refresh_token)


# =============================================================================
# GET /me - ユーザー情報取得
# =============================================================================
me_router = APIRouter(tags=["Auth"])


@me_router.get(
    "/me",
    response_model=MeResponse,
    summary="ユーザー情報取得",
    description="認証ユーザーの情報とオンボーディング状態を取得します。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def get_me(
    user_id: CurrentUserId,
    auth_service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    """ユーザー情報取得"""
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("ユーザーが見つかりません")

    return MeResponse(
        user=User.from_model(user),
        onboarding=Onboarding.from_user(user),
    )


# =============================================================================
# PATCH /me - プロフィール更新
# =============================================================================
@me_router.patch(
    "/me",
    response_model=UserResponse,
    summary="プロフィール更新",
    description="ユーザーのプロフィール情報を更新します。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
    },
)
async def update_me(
    user_id: CurrentUserId,
    request: UpdateMeRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """プロフィール更新"""
    user = await auth_service.update_user(
        user_id=user_id,
        display_name=request.display_name,
    )
    if not user:
        raise NotFoundException("ユーザーが見つかりません")

    return UserResponse(user=User.from_model(user))


# =============================================================================
# POST /me/consent - 利用規約同意
# =============================================================================
@me_router.post(
    "/me/consent",
    response_model=ConsentResponse,
    summary="利用規約同意",
    description="利用規約とプライバシーポリシーへの同意を記録します。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        409: {"description": "同意済み"},
    },
)
async def consent(
    user_id: CurrentUserId,
    request: ConsentRequest,
) -> ConsentResponse:
    """
    利用規約同意

    TODO: Implement consent (Phase 2)
    - Validate version numbers
    - Record consent in database
    - Update user consent_at
    """
    raise NotImplementedError("TODO: Implement consent (Phase 2)")


# =============================================================================
# POST /me/age-verify - 年齢確認
# =============================================================================
@me_router.post(
    "/me/age-verify",
    response_model=AgeVerifyResponse,
    summary="年齢確認",
    description="ユーザーの年齢を確認し、適切な制限を設定します。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        403: {"description": "同意未完了"},
        409: {"description": "年齢確認済み"},
    },
)
async def age_verify(
    user_id: CurrentUserId,
    request: AgeVerifyRequest,
) -> AgeVerifyResponse:
    """
    年齢確認

    TODO: Implement age_verify (Phase 2)
    - Require consent completed
    - Calculate age_group from birth_date or use provided age_group
    - Set restrictions based on age
    - Log audit event
    """
    raise NotImplementedError("TODO: Implement age_verify (Phase 2)")
