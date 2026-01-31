"""Common schemas used across multiple modules"""
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Pagination
# =============================================================================


class Pagination(BaseModel):
    """Pagination info for list responses"""

    next_cursor: Optional[str] = Field(None, description="次ページのカーソル")
    has_more: bool = Field(..., description="次ページの有無")


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""

    data: List[T]
    pagination: Pagination

    model_config = ConfigDict(arbitrary_types_allowed=True)


# =============================================================================
# Error Response (matching openapi.yaml)
# =============================================================================


class ErrorDetail(BaseModel):
    """Individual error detail"""

    field: Optional[str] = None
    code: str
    message: str


class ErrorBody(BaseModel):
    """Error body structure"""

    code: str
    message: str
    details: List[ErrorDetail] = []


class ErrorResponse(BaseModel):
    """Unified error response"""

    error: ErrorBody


# =============================================================================
# Common Base Models
# =============================================================================


class TimestampMixin(BaseModel):
    """Mixin for created_at/updated_at fields"""

    created_at: datetime
    updated_at: Optional[datetime] = None


class BaseEntityModel(BaseModel):
    """Base model for entity responses"""

    id: str

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Common Embedded Objects
# =============================================================================


class Tag(BaseModel):
    """Tag object"""

    id: str
    name: str
    count: Optional[int] = None


class Creator(BaseModel):
    """Creator info (embedded in Pack)"""

    id: str
    display_name: str
    avatar_url: Optional[str] = None


class Character(BaseModel):
    """Character info (embedded in Thread, Clip)"""

    id: str
    name: str
    avatar_url: Optional[str] = None
