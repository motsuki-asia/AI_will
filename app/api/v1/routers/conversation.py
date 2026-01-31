"""Conversation router - matching openapi.yaml Conversation paths"""
from typing import Optional

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from app.deps import OnboardedUser, Pagination, Sort
from app.schemas.conversation import (
    CreateThreadRequest,
    MessageListResponse,
    SendMessageRequest,
    SendMessageResponse,
    ThreadDetailResponse,
    ThreadListResponse,
    ThreadResponse,
)

router = APIRouter(prefix="/threads", tags=["Conversation"])


# =============================================================================
# GET /threads - スレッド一覧取得
# =============================================================================
@router.get(
    "",
    response_model=ThreadListResponse,
    summary="スレッド一覧取得",
    description="ユーザーの会話スレッド一覧を取得します。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def list_threads(
    user_state: OnboardedUser,
    pagination: Pagination,
    sort: Sort,
    character_id: Optional[str] = Query(None, description="キャラクター絞り込み"),
) -> ThreadListResponse:
    """
    スレッド一覧取得

    TODO: Implement list_threads
    - Fetch threads for current user (WHERE deleted_at IS NULL)
    - Filter by character_id if specified
    - Join with character info
    - Get last_message using LATERAL JOIN
    """
    raise NotImplementedError("TODO: Implement list_threads")


# =============================================================================
# POST /threads - スレッド作成
# =============================================================================
@router.post(
    "",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="スレッド作成",
    description="新しい会話スレッドを作成します。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        403: {"description": "購入が必要 / 年齢制限"},
        404: {"description": "Pack/キャラクター not found"},
    },
)
async def create_thread(
    user_state: OnboardedUser,
    request: CreateThreadRequest,
) -> ThreadResponse:
    """
    スレッド作成

    TODO: Implement create_thread
    - Check entitlement (owned or free pack)
    - Check age restriction
    - Create conversation_session
    """
    raise NotImplementedError("TODO: Implement create_thread")


# NOTE: DELETE /threads（一括削除）は MVP から削除。
# 理由: Privacy Job（POST /privacy/delete）で会話履歴の一括削除に対応可能。
# 個別削除は DELETE /threads/{thread_id} で対応。


# =============================================================================
# GET /threads/{thread_id} - スレッド詳細取得
# =============================================================================
@router.get(
    "/{thread_id}",
    response_model=ThreadDetailResponse,
    summary="スレッド詳細取得",
    description="指定したスレッドの詳細情報を取得します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのスレッド"},
        404: {"description": "スレッド not found"},
    },
)
async def get_thread(
    thread_id: str,
    user_state: OnboardedUser,
) -> ThreadDetailResponse:
    """
    スレッド詳細取得

    TODO: Implement get_thread
    - Fetch thread (verify ownership)
    - Get relationship info
    """
    raise NotImplementedError("TODO: Implement get_thread")


# =============================================================================
# DELETE /threads/{thread_id} - スレッド削除
# =============================================================================
@router.delete(
    "/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="スレッド削除",
    description="指定したスレッドを削除します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのスレッド"},
        404: {"description": "スレッド not found"},
    },
)
async def delete_thread(
    thread_id: str,
    user_state: OnboardedUser,
) -> None:
    """
    スレッド削除

    TODO: Implement delete_thread
    - Verify ownership
    - Soft delete thread and messages
    """
    raise NotImplementedError("TODO: Implement delete_thread")


# =============================================================================
# GET /threads/{thread_id}/messages - メッセージ履歴取得
# =============================================================================
@router.get(
    "/{thread_id}/messages",
    response_model=MessageListResponse,
    summary="メッセージ履歴取得",
    description="スレッドのメッセージ履歴を取得します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのスレッド"},
        404: {"description": "スレッド not found"},
    },
)
async def list_messages(
    thread_id: str,
    user_state: OnboardedUser,
    pagination: Pagination,
    order: str = Query("desc", description="asc（古い順）/ desc（新しい順）"),
) -> MessageListResponse:
    """
    メッセージ履歴取得

    TODO: Implement list_messages
    - Verify thread ownership
    - Fetch messages with pagination
    """
    raise NotImplementedError("TODO: Implement list_messages")


# =============================================================================
# POST /threads/{thread_id}/messages - メッセージ送信
# =============================================================================
@router.post(
    "/{thread_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="メッセージ送信",
    description="スレッドにメッセージを送信し、AIの応答を取得します。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのスレッド"},
        408: {"description": "タイムアウト"},
        503: {"description": "サービス利用不可"},
    },
)
async def send_message(
    thread_id: str,
    user_state: OnboardedUser,
    request: SendMessageRequest,
) -> SendMessageResponse:
    """
    メッセージ送信

    TODO: Implement send_message
    - Verify thread ownership
    - Save user message
    - Call LLM API
    - Save assistant message
    - Update relationship (affection)
    """
    raise NotImplementedError("TODO: Implement send_message")


# =============================================================================
# POST /threads/{thread_id}/messages:stream - メッセージ送信（SSE）
# =============================================================================
@router.post(
    "/{thread_id}/messages:stream",
    summary="メッセージ送信（SSEストリーミング）",
    description="スレッドにメッセージを送信し、AIの応答をSSEでストリーミング取得します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのスレッド"},
    },
)
async def send_message_stream(
    thread_id: str,
    user_state: OnboardedUser,
    request: SendMessageRequest,
) -> StreamingResponse:
    """
    メッセージ送信（SSEストリーミング）

    TODO: Implement send_message_stream
    - Verify thread ownership
    - Save user message
    - Stream LLM response as SSE events:
      - message_start: {user_message_id, assistant_message_id}
      - content_delta: {delta}
      - message_done: {assistant_message_id, finish_reason, usage}
      - error: {code, message}
    """

    async def event_generator():
        # TODO: Implement SSE streaming
        yield 'event: message_start\ndata: {"user_message_id": "msg_001", "assistant_message_id": "msg_002"}\n\n'
        yield 'event: content_delta\ndata: {"delta": "こんにちは！"}\n\n'
        yield 'event: message_done\ndata: {"assistant_message_id": "msg_002", "finish_reason": "stop"}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
