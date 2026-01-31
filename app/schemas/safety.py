"""Safety schemas - matching openapi.yaml Safety components"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .common import Pagination


# =============================================================================
# Report Models
# =============================================================================


class ReportReason(BaseModel):
    """Report reason"""

    id: str
    code: str
    name: str


class CreateReportRequest(BaseModel):
    """Create report request"""

    target_type: Literal["character", "message", "pack", "creator"] = Field(
        ..., description="通報対象種別"
    )
    target_id: str = Field(..., description="通報対象 ID")
    reason_id: str = Field(..., description="通報理由 ID")
    comment: Optional[str] = Field(None, max_length=500, description="補足コメント")


class Report(BaseModel):
    """Report object"""

    id: str
    target_type: str
    target_id: str
    reason: ReportReason
    status: Literal["open", "in_progress", "resolved", "rejected"]
    created_at: datetime


class ReportReasonListResponse(BaseModel):
    """Report reason list response"""

    data: List[ReportReason]


class ReportResponse(BaseModel):
    """Report response"""

    report: Report
    message: str


# =============================================================================
# Block Models
# =============================================================================


class CreateBlockRequest(BaseModel):
    """Create block request"""

    target_type: Literal["user", "creator", "character", "tag"] = Field(
        ..., description="ブロック対象種別"
    )
    target_id: str = Field(..., description="ブロック対象 ID")


class Block(BaseModel):
    """Block object"""

    id: str
    target_type: str
    target_id: str
    target_name: Optional[str] = None
    created_at: datetime


class BlockResponse(BaseModel):
    """Block response"""

    block: Block


class BlockListResponse(BaseModel):
    """Block list response"""

    data: List[Block]
    pagination: Pagination
