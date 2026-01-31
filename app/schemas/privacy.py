"""Privacy schemas - matching openapi.yaml Privacy components"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Job Common
# =============================================================================


JobStatus = Literal["queued", "processing", "completed", "cancelled", "failed"]
JobScope = Literal["conversations", "memories", "all"]


class JobProgress(BaseModel):
    """Job progress info"""

    total_items: int
    processed_items: int
    percentage: int


# =============================================================================
# Export Job Models
# =============================================================================


class CreateExportJobRequest(BaseModel):
    """Create export job request"""

    scope: JobScope = Field(..., description="エクスポート範囲")


class ExportJobResponse(BaseModel):
    """Export job response"""

    job_id: str
    status: JobStatus
    scope: str
    progress: Optional[JobProgress] = None
    download_url: Optional[str] = None
    download_expires_at: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# =============================================================================
# Delete Job Models
# =============================================================================


class CreateDeleteJobRequest(BaseModel):
    """Create delete job request"""

    scope: JobScope = Field(..., description="削除範囲")
    confirm: bool = Field(..., description="確認フラグ（true必須）")


class DeleteJobResponse(BaseModel):
    """Delete job response"""

    job_id: str
    status: JobStatus
    scope: str
    progress: Optional[JobProgress] = None
    grace_period_until: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
