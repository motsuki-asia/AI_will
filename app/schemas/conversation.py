"""Conversation schemas - matching openapi.yaml Conversation components"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .common import Character, Pagination


# =============================================================================
# Message Models
# =============================================================================


class Message(BaseModel):
    """Message object"""

    id: str
    role: Literal["user", "character"]
    content: str
    content_type: Literal["text", "audio"] = "text"
    created_at: datetime


# =============================================================================
# Relationship Models
# =============================================================================


class RelationshipStage(BaseModel):
    """Relationship stage"""

    id: str
    name: str
    code: str


class Relationship(BaseModel):
    """User-character relationship"""

    affection: int
    stage: RelationshipStage


# =============================================================================
# Thread Models
# =============================================================================


class Thread(BaseModel):
    """Thread (conversation session) object"""

    id: str
    pack_id: str
    character: Character
    session_type: Literal["free", "event"] = "free"
    event_id: Optional[str] = None
    message_count: int = 0
    last_message: Optional[Message] = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Request Models
# =============================================================================


class CreateThreadRequest(BaseModel):
    """Create thread request"""

    pack_id: Optional[str] = Field(None, description="対象 Pack ID（カスタムキャラクターの場合は省略可）")
    character_id: str = Field(..., description="対象キャラクター ID")
    session_type: Literal["free", "event"] = Field("free", description="セッション種別")
    event_id: Optional[str] = Field(None, description="イベント会話の場合のイベント ID")


class SendMessageRequest(BaseModel):
    """Send message request"""

    content: str = Field(..., max_length=2000, description="メッセージ内容")
    content_type: Literal["text", "audio"] = Field("text", description="コンテンツ種別")


# =============================================================================
# Response Models
# =============================================================================


class ThreadResponse(BaseModel):
    """Thread response"""

    thread: Thread


class ThreadDetailResponse(BaseModel):
    """Thread detail response"""

    thread: Thread
    relationship: Optional[Relationship] = None


class ThreadListResponse(BaseModel):
    """Thread list response"""

    data: List[Thread]
    pagination: Pagination


# NOTE: DeleteThreadsResponse は MVP から削除（DELETE /threads 廃止に伴い）


class SendMessageResponse(BaseModel):
    """Send message response"""

    user_message: Message
    assistant_message: Message


class MessageListResponse(BaseModel):
    """Message list response"""

    data: List[Message]
    pagination: Pagination


# =============================================================================
# SSE Event Models
# =============================================================================


class SSEMessageStart(BaseModel):
    """SSE message_start event payload"""

    user_message_id: str
    assistant_message_id: str


class SSEContentDelta(BaseModel):
    """SSE content_delta event payload"""

    delta: str


class SSEAudioDelta(BaseModel):
    """SSE audio_delta event payload"""

    delta: str  # Base64 encoded


class SSEUsage(BaseModel):
    """Token usage info"""

    prompt_tokens: int
    completion_tokens: int


class SSEMessageDone(BaseModel):
    """SSE message_done event payload"""

    assistant_message_id: str
    finish_reason: Literal["stop", "length", "content_filter"]
    usage: Optional[SSEUsage] = None


class SSEError(BaseModel):
    """SSE error event payload"""

    code: str
    message: str
