"""Memory (Clip) schemas - matching openapi.yaml Memory components"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import Character, Pagination


# =============================================================================
# Request Models
# =============================================================================


class CreateClipRequest(BaseModel):
    """Create clip request"""

    source_message_id: str = Field(..., description="切り抜き元のメッセージ ID")
    title: Optional[str] = Field(None, max_length=100, description="タイトル")
    tags: Optional[List[str]] = Field(None, description="タグ")


# Note: UpdateClipRequest is removed (v1.1.0) - clips are immutable after creation


# =============================================================================
# Response Models
# =============================================================================


class Clip(BaseModel):
    """Clip object"""

    id: str
    title: Optional[str] = None
    content: str
    character: Character
    source_message_id: Optional[str] = None
    tags: List[str] = []
    created_at: datetime


class ClipResponse(BaseModel):
    """Clip response"""

    clip: Clip


class ClipListResponse(BaseModel):
    """Clip list response"""

    data: List[Clip]
    pagination: Pagination
