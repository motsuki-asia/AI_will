"""Safety router - matching openapi.yaml Safety paths"""
from fastapi import APIRouter, status

from app.deps import OnboardedUser, Pagination
from app.schemas.safety import (
    BlockListResponse,
    BlockResponse,
    CreateBlockRequest,
    CreateReportRequest,
    ReportReasonListResponse,
    ReportResponse,
)

router = APIRouter(tags=["Safety"])


# =============================================================================
# GET /report-reasons - 通報理由一覧取得
# =============================================================================
@router.get(
    "/report-reasons",
    response_model=ReportReasonListResponse,
    summary="通報理由一覧取得",
    description="通報時に選択できる理由の一覧を取得します。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def list_report_reasons(
    user_state: OnboardedUser,
) -> ReportReasonListResponse:
    """
    通報理由一覧取得

    TODO: Implement list_report_reasons
    - Fetch from m_report_reasons table
    """
    raise NotImplementedError("TODO: Implement list_report_reasons")


# =============================================================================
# POST /reports - 通報
# =============================================================================
@router.post(
    "/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="通報",
    description="コンテンツやユーザーを通報します。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        404: {"description": "通報対象 not found"},
        409: {"description": "重複通報（24時間以内）"},
    },
)
async def create_report(
    user_state: OnboardedUser,
    request: CreateReportRequest,
) -> ReportResponse:
    """
    通報

    TODO: Implement create_report
    - Verify target exists
    - Check for duplicate report (within 24 hours)
    - Create report record
    """
    raise NotImplementedError("TODO: Implement create_report")


# =============================================================================
# GET /blocks - ブロック一覧取得
# =============================================================================
@router.get(
    "/blocks",
    response_model=BlockListResponse,
    summary="ブロック一覧取得",
    description="ユーザーがブロックしている対象の一覧を取得します。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def list_blocks(
    user_state: OnboardedUser,
    pagination: Pagination,
) -> BlockListResponse:
    """
    ブロック一覧取得

    TODO: Implement list_blocks
    - Fetch user's blocks (WHERE deleted_at IS NULL)
    """
    raise NotImplementedError("TODO: Implement list_blocks")


# =============================================================================
# POST /blocks - ブロック
# =============================================================================
@router.post(
    "/blocks",
    response_model=BlockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ブロック",
    description="コンテンツやクリエイターをブロックします。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        409: {"description": "既にブロック済み"},
    },
)
async def create_block(
    user_state: OnboardedUser,
    request: CreateBlockRequest,
) -> BlockResponse:
    """
    ブロック

    TODO: Implement create_block
    - Check if already blocked
    - Create block record
    """
    raise NotImplementedError("TODO: Implement create_block")


# =============================================================================
# DELETE /blocks/{block_id} - ブロック解除
# =============================================================================
@router.delete(
    "/blocks/{block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="ブロック解除",
    description="指定したブロックを解除します。",
    responses={
        401: {"description": "認証エラー"},
        404: {"description": "ブロック not found"},
    },
)
async def delete_block(
    block_id: str,
    user_state: OnboardedUser,
) -> None:
    """
    ブロック解除

    TODO: Implement delete_block
    - Verify ownership
    - Soft delete block
    """
    raise NotImplementedError("TODO: Implement delete_block")
