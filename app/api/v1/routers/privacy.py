"""Privacy router - matching openapi.yaml Privacy paths"""
from fastapi import APIRouter, status

from app.deps import IdempotencyKey, OnboardedUser
from app.schemas.privacy import (
    CreateDeleteJobRequest,
    CreateExportJobRequest,
    DeleteJobResponse,
    ExportJobResponse,
)

router = APIRouter(prefix="/privacy", tags=["Privacy"])


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
    },
)
async def create_export_job(
    user_state: OnboardedUser,
    idempotency_key: IdempotencyKey,
    request: CreateExportJobRequest,
) -> ExportJobResponse:
    """
    データエクスポートジョブ作成

    TODO: Implement create_export_job
    - Check idempotency
    - Check for existing job in progress
    - Create export job
    - Queue background task
    """
    raise NotImplementedError("TODO: Implement create_export_job")


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
    },
)
async def get_export_job(
    job_id: str,
    user_state: OnboardedUser,
) -> ExportJobResponse:
    """
    エクスポートジョブ状態確認

    TODO: Implement get_export_job
    - Fetch job (verify ownership)
    - Return current status and progress
    """
    raise NotImplementedError("TODO: Implement get_export_job")


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
) -> DeleteJobResponse:
    """
    データ削除ジョブ作成

    TODO: Implement create_delete_job
    - Require confirm=true
    - Check idempotency
    - Check for existing job in progress
    - Create delete job with grace period
    - Queue background task (after grace period)
    """
    raise NotImplementedError("TODO: Implement create_delete_job")


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

    TODO: Implement get_delete_job
    - Fetch job (verify ownership)
    - Return current status and progress
    """
    raise NotImplementedError("TODO: Implement get_delete_job")


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

    TODO: Implement cancel_delete_job
    - Verify ownership
    - Check if within grace period
    - Cancel job
    """
    raise NotImplementedError("TODO: Implement cancel_delete_job")
