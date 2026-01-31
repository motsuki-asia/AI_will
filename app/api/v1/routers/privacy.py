"""Privacy router - matching openapi.yaml Privacy paths"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ValidationException
from app.db.database import get_db
from app.deps import IdempotencyKey, OnboardedUser
from app.schemas.privacy import (
    CreateDeleteJobRequest,
    CreateExportJobRequest,
    DeleteJobResponse,
    ExportJobResponse,
    JobProgress,
)
from app.services.privacy import PrivacyService

router = APIRouter(prefix="/privacy", tags=["Privacy"])


def get_privacy_service(db: AsyncSession = Depends(get_db)) -> PrivacyService:
    """Dependency to get PrivacyService"""
    return PrivacyService(db)


# =============================================================================
# POST /privacy/export - データエクスポートジョブ作成
# =============================================================================
@router.post(
    "/export",
    response_model=ExportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="データエクスポートジョブ作成",
    description="ユーザーデータのエクスポートジョブを作成します。Idempotency-Keyヘッダー必須。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        409: {"description": "ジョブ進行中"},
        501: {"description": "未実装"},
    },
)
async def create_export_job(
    user_state: OnboardedUser,
    idempotency_key: IdempotencyKey,
    request: CreateExportJobRequest,
) -> ExportJobResponse:
    """
    データエクスポートジョブ作成

    Phase 3: Not implemented in MVP
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="エクスポート機能はPhase 3で実装予定です",
    )


# =============================================================================
# GET /privacy/export/{job_id} - エクスポートジョブ状態確認
# =============================================================================
@router.get(
    "/export/{job_id}",
    response_model=ExportJobResponse,
    summary="エクスポートジョブ状態確認",
    description="エクスポートジョブの状態を確認します。",
    responses={
        401: {"description": "認証エラー"},
        404: {"description": "ジョブ not found"},
        501: {"description": "未実装"},
    },
)
async def get_export_job(
    job_id: str,
    user_state: OnboardedUser,
) -> ExportJobResponse:
    """
    エクスポートジョブ状態確認

    Phase 3: Not implemented in MVP
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="エクスポート機能はPhase 3で実装予定です",
    )


# =============================================================================
# POST /privacy/delete - データ削除ジョブ作成
# =============================================================================
@router.post(
    "/delete",
    response_model=DeleteJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="データ削除ジョブ作成",
    description="ユーザーデータの削除ジョブを作成します。Idempotency-Keyヘッダー必須。",
    responses={
        400: {"description": "バリデーションエラー / confirm未指定"},
        401: {"description": "認証エラー"},
        409: {"description": "ジョブ進行中"},
    },
)
async def create_delete_job(
    user_state: OnboardedUser,
    idempotency_key: IdempotencyKey,
    request: CreateDeleteJobRequest,
    privacy_service: PrivacyService = Depends(get_privacy_service),
) -> DeleteJobResponse:
    """
    データ削除ジョブ作成

    MVP: Synchronous deletion (no grace period)
    - Require confirm=true
    - Delete conversations immediately
    """
    if not request.confirm:
        raise ValidationException(
            message="削除を確認してください",
            details=[{"field": "confirm", "code": "required", "message": "confirm: trueを指定してください"}],
        )

    job_info = await privacy_service.create_delete_job(
        user_id=user_state.user_id,
        scope=request.scope,
    )

    return DeleteJobResponse(
        job_id=job_info["job_id"],
        status=job_info["status"],
        scope=job_info["scope"],
        progress=JobProgress(**job_info["progress"]) if job_info["progress"] else None,
        grace_period_until=job_info["grace_period_until"],
        created_at=job_info["created_at"],
        completed_at=job_info["completed_at"],
        cancelled_at=job_info["cancelled_at"],
    )


# =============================================================================
# GET /privacy/delete/{job_id} - 削除ジョブ状態確認
# =============================================================================
@router.get(
    "/delete/{job_id}",
    response_model=DeleteJobResponse,
    summary="削除ジョブ状態確認",
    description="削除ジョブの状態を確認します。",
    responses={
        401: {"description": "認証エラー"},
        404: {"description": "ジョブ not found"},
    },
)
async def get_delete_job(
    job_id: str,
    user_state: OnboardedUser,
) -> DeleteJobResponse:
    """
    削除ジョブ状態確認

    MVP: Jobs are synchronous, so this always returns not found
    (job status is not persisted)
    """
    from app.core.errors import NotFoundException
    raise NotFoundException("ジョブが見つかりません（MVPでは即時完了のためジョブ状態は保存されません）")


# =============================================================================
# POST /privacy/delete/{job_id}/cancel - 削除ジョブキャンセル
# =============================================================================
@router.post(
    "/delete/{job_id}/cancel",
    response_model=DeleteJobResponse,
    summary="削除ジョブキャンセル",
    description="猶予期間内の削除ジョブをキャンセルします。",
    responses={
        400: {"description": "キャンセル不可（猶予期間終了 or 処理完了後）"},
        401: {"description": "認証エラー"},
        404: {"description": "ジョブ not found"},
    },
)
async def cancel_delete_job(
    job_id: str,
    user_state: OnboardedUser,
) -> DeleteJobResponse:
    """
    削除ジョブキャンセル

    MVP: Jobs are synchronous with no grace period, so cancel is not available
    """
    from app.core.errors import NotFoundException
    raise NotFoundException("ジョブが見つかりません（MVPでは即時削除のためキャンセルできません）")
