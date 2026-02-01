"""Catalog schemas - matching openapi.yaml Catalog components"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .common import Character, Creator, Pagination, Tag


# =============================================================================
# Embedded Objects
# =============================================================================


class PackStats(BaseModel):
    """Pack statistics"""

    favorite_count: int
    conversation_count: int
    review_count: Optional[int] = None
    average_rating: Optional[float] = None


class UserStatus(BaseModel):
    """User's status for a Pack"""

    owned: bool
    favorited: bool


# =============================================================================
# Pack Models
# =============================================================================


class Pack(BaseModel):
    """Pack object"""

    id: str
    pack_type: Literal["persona", "scenario"]
    name: str
    description: str
    thumbnail_url: str
    cover_url: Optional[str] = None
    sample_voice_url: Optional[str] = None
    price: int = Field(..., description="価格（円）")
    is_free: bool
    age_rating: Literal["all", "r15", "r18"]
    tags: List[Tag] = []
    creator: Creator
    stats: PackStats
    created_at: datetime
    updated_at: Optional[datetime] = None


class PackItem(BaseModel):
    """Pack item (character, event, etc.)"""

    id: str
    item_type: Literal["character", "event", "voice_pack"]
    item_id: str
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None


# =============================================================================
# Response Models
# =============================================================================


class PackListResponse(BaseModel):
    """Pack list response"""

    data: List[Pack]
    pagination: Pagination


class PackDetailResponse(BaseModel):
    """Pack detail response"""

    pack: Pack
    user_status: UserStatus


class PackItemsResponse(BaseModel):
    """Pack items response"""

    data: List[PackItem]


class TagListResponse(BaseModel):
    """Tag list response"""

    data: List[Tag]


# =============================================================================
# Character Models (for direct character listing)
# =============================================================================


class CharacterListItem(BaseModel):
    """Character item for listing"""

    id: str
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    pack_id: Optional[str] = None
    pack_name: Optional[str] = None
    is_custom: bool = False  # True if user-created character


class CharacterListResponse(BaseModel):
    """Character list response"""

    data: List[CharacterListItem]
    pagination: Pagination
