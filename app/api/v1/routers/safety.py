"""Safety router - matching openapi.yaml Safety paths"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException, ValidationException
from app.db.database import get_db
from app.deps import OnboardedUser, Pagination
from app.schemas.common import Pagination as PaginationSchema
from app.schemas.safety import (
    Block,
    BlockListResponse,
    BlockResponse,
    CreateBlockRequest,
    CreateReportRequest,
    ReportReasonListResponse,
    ReportResponse,
)
from app.services.safety import SafetyService

router = APIRouter(tags=["Safety"])


def get_safety_service(db: AsyncSession = Depends(get_db)) -> SafetyService:
    """Dependency to get SafetyService"""
    return SafetyService(db)


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
    safety_service: SafetyService = Depends(get_safety_service),
) -> ReportReasonListResponse:
    """
    通報理由一覧取得

    - Fetch from m_report_reasons table
    """
    reasons = await safety_service.list_report_reasons()

    return ReportReasonListResponse(
        data=[safety_service.reason_to_schema(r) for r in reasons]
    )


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
    safety_service: SafetyService = Depends(get_safety_service),
) -> ReportResponse:
    """
    通報

    - Verify target exists (MVP: skip)
    - Create report record
    """
    report = await safety_service.create_report(
        user_id=user_state.user_id,
        target_type=request.target_type,
        target_id=request.target_id,
        reason_id=request.reason_id,
        detail=request.comment,
    )

    if not report:
        raise ValidationException(
            message="通報理由が見つかりません",
            details=[{"field": "reason_id", "code": "not_found", "message": "無効な通報理由IDです"}],
        )

    return ReportResponse(
        report=safety_service.report_to_schema(report),
        message="通報を受け付けました。ご報告ありがとうございます。",
    )


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

    MVP: Returns empty list (blocks not implemented yet)
    """
    return BlockListResponse(
        data=[],
        pagination=PaginationSchema(next_cursor=None, has_more=False),
    )


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
        501: {"description": "未実装"},
    },
)
async def create_block(
    user_state: OnboardedUser,
    request: CreateBlockRequest,
) -> BlockResponse:
    """
    ブロック

    Phase 2: Not implemented in MVP
    """
    from fastapi import HTTPException
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="ブロック機能はPhase 2で実装予定です",
    )


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
        501: {"description": "未実装"},
    },
)
async def delete_block(
    block_id: str,
    user_state: OnboardedUser,
) -> None:
    """
    ブロック解除

    Phase 2: Not implemented in MVP
    """
    from fastapi import HTTPException
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="ブロック機能はPhase 2で実装予定です",
    )
