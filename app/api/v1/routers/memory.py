"""Memory (Clip) router - matching openapi.yaml Memory paths"""
from typing import Optional

from fastapi import APIRouter, Query, status

from app.deps import OnboardedUser, Pagination
from app.schemas.memory import ClipListResponse, ClipResponse, CreateClipRequest

router = APIRouter(prefix="/clips", tags=["Memory"])


# =============================================================================
# GET /clips - クリップ一覧取得
# =============================================================================
@router.get(
    "",
    response_model=ClipListResponse,
    summary="クリップ一覧取得",
    description="ユーザーの保存したクリップ（メモリー）一覧を取得します。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def list_clips(
    user_state: OnboardedUser,
    pagination: Pagination,
    thread_id: Optional[str] = Query(None, description="スレッド絞り込み"),
) -> ClipListResponse:
    """
    クリップ一覧取得

    TODO: Implement list_clips
    - Fetch clips for current user (WHERE deleted_at IS NULL)
    - Filter by thread_id if specified
    - Join with character info
    """
    raise NotImplementedError("TODO: Implement list_clips")


# =============================================================================
# POST /clips - クリップ作成
# =============================================================================
@router.post(
    "",
    response_model=ClipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="クリップ作成",
    description="メッセージを切り抜いてクリップとして保存します。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        404: {"description": "メッセージ not found"},
    },
)
async def create_clip(
    user_state: OnboardedUser,
    request: CreateClipRequest,
) -> ClipResponse:
    """
    クリップ作成

    TODO: Implement create_clip
    - Verify message ownership
    - Create clip record
    """
    raise NotImplementedError("TODO: Implement create_clip")


# =============================================================================
# GET /clips/{clip_id} - クリップ詳細取得
# =============================================================================
@router.get(
    "/{clip_id}",
    response_model=ClipResponse,
    summary="クリップ詳細取得",
    description="指定したクリップの詳細を取得します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのクリップ"},
        404: {"description": "クリップ not found"},
    },
)
async def get_clip(
    clip_id: str,
    user_state: OnboardedUser,
) -> ClipResponse:
    """
    クリップ詳細取得

    TODO: Implement get_clip
    - Fetch clip (verify ownership)
    """
    raise NotImplementedError("TODO: Implement get_clip")


# Note: PATCH /clips/{clip_id} is removed (v1.1.0) - clips are immutable after creation


# =============================================================================
# DELETE /clips/{clip_id} - クリップ削除
# =============================================================================
@router.delete(
    "/{clip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="クリップ削除",
    description="指定したクリップを削除します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのクリップ"},
        404: {"description": "クリップ not found"},
    },
)
async def delete_clip(
    clip_id: str,
    user_state: OnboardedUser,
) -> None:
    """
    クリップ削除

    TODO: Implement delete_clip
    - Verify ownership
    - Soft delete clip
    """
    raise NotImplementedError("TODO: Implement delete_clip")
