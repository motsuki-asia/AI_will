"""Conversation router - matching openapi.yaml Conversation paths"""
from typing import Optional, List as ListType

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException, ServiceUnavailableException
from app.db.database import get_db
from app.deps import OnboardedUser, Pagination, Sort
from app.models import ConversationMessage
from app.schemas.conversation import (
    CreateThreadRequest,
    Message,
    MessageListResponse,
    Relationship,
    RelationshipStage,
    SendMessageRequest,
    SendMessageResponse,
    Thread,
    ThreadDetailResponse,
    ThreadListResponse,
    ThreadResponse,
)
from app.schemas.common import Character as CharacterSchema
from app.services.conversation import ConversationService
from app.services.image import ImageService
from app.services.scene import SceneService

router = APIRouter(prefix="/threads", tags=["Conversation"])


def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    """Dependency to get ConversationService"""
    return ConversationService(db)


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
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ThreadListResponse:
    """
    スレッド一覧取得

    - Fetch threads for current user
    - Filter by character_id if specified
    - Join with character info
    """
    sessions, page_info = await conversation_service.list_threads(
        user_id=user_state.user_id,
        character_id=character_id,
        cursor=pagination.cursor,
        limit=pagination.limit,
    )

    threads = [_session_to_thread(s) for s in sessions]

    return ThreadListResponse(
        data=threads,
        pagination=page_info,
    )


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
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ThreadResponse:
    """
    スレッド作成

    - Check entitlement (MVP: all free)
    - Create conversation_session
    """
    session = await conversation_service.create_thread(
        user_id=user_state.user_id,
        pack_id=request.pack_id,
        character_id=request.character_id,
    )

    if not session:
        raise NotFoundException("キャラクターが見つかりません")

    # Update pack_id on session
    session.pack_id = request.pack_id
    await conversation_service.db.flush()

    return ThreadResponse(thread=_session_to_thread(session))


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
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> ThreadDetailResponse:
    """
    スレッド詳細取得

    - Fetch thread (verify ownership)
    - Get relationship info
    """
    session = await conversation_service.get_thread(thread_id, user_state.user_id)

    if not session:
        raise NotFoundException("スレッドが見つかりません")

    return ThreadDetailResponse(
        thread=_session_to_thread(session),
        relationship=Relationship(
            affection=0,
            stage=RelationshipStage(id="initial", name="初対面", code="initial"),
        ),
    )


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
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> None:
    """
    スレッド削除

    - Verify ownership
    - Soft delete thread
    """
    deleted = await conversation_service.delete_thread(thread_id, user_state.user_id)

    if not deleted:
        raise NotFoundException("スレッドが見つかりません")


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
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> MessageListResponse:
    """
    メッセージ履歴取得

    - Verify thread ownership
    - Fetch messages with pagination
    """
    result = await conversation_service.list_messages(
        thread_id=thread_id,
        user_id=user_state.user_id,
        cursor=pagination.cursor,
        limit=pagination.limit,
        order=order,
    )

    if result is None:
        raise NotFoundException("スレッドが見つかりません")

    messages, page_info = result

    return MessageListResponse(
        data=[_message_to_schema(m) for m in messages],
        pagination=page_info,
    )


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
    conversation_service: ConversationService = Depends(get_conversation_service),
) -> SendMessageResponse:
    """
    メッセージ送信

    - Verify thread ownership
    - Save user message
    - Call LLM API (or stub)
    - Save assistant message
    """
    result = await conversation_service.send_message(
        thread_id=thread_id,
        user_id=user_state.user_id,
        content=request.content,
    )

    if result is None:
        raise NotFoundException("スレッドが見つかりません")

    user_msg, ai_msg = result

    return SendMessageResponse(
        user_message=_message_to_schema(user_msg),
        assistant_message=_message_to_schema(ai_msg),
    )


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


# =============================================================================
# GET /threads/{thread_id}/messages/{message_id}/audio - メッセージ音声取得
# =============================================================================
@router.get(
    "/{thread_id}/messages/{message_id}/audio",
    summary="メッセージ音声取得",
    description="メッセージを音声で取得します（TTS）。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのスレッド"},
        404: {"description": "メッセージ not found"},
        503: {"description": "TTS未設定"},
    },
)
async def get_message_audio(
    thread_id: str,
    message_id: str,
    user_state: OnboardedUser,
    voice: str = Query("nova", description="音声の種類（nova, shimmer, alloy, echo, fable, onyx）"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    メッセージ音声取得

    - Verify thread ownership
    - Get message content
    - Convert to speech using TTS API
    """
    from sqlalchemy import select
    from app.models import ConversationSession, ConversationMessage
    from app.services.tts import TTSService
    import io
    
    # Verify thread ownership
    result = await db.execute(
        select(ConversationSession)
        .where(ConversationSession.id == thread_id)
        .where(ConversationSession.user_id == user_state.user_id)
        .where(ConversationSession.deleted_at.is_(None))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundException("スレッドが見つかりません")
    
    # Get message
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.id == message_id)
        .where(ConversationMessage.session_id == thread_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise NotFoundException("メッセージが見つかりません")
    
    # Generate audio
    tts_service = TTSService()
    audio_bytes = await tts_service.synthesize(
        text=message.content,
        voice=voice,
    )
    
    if not audio_bytes:
        from app.core.errors import ServiceUnavailableException
        raise ServiceUnavailableException("音声合成サービスが利用できません。LLM_API_KEYを設定してください。")
    
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="message_{message_id}.mp3"',
        },
    )


# =============================================================================
# POST /threads/{thread_id}/scene-image - シーン画像生成
# =============================================================================


class SceneImageRequest(BaseModel):
    """Request to generate scene image from selected messages"""
    message_ids: ListType[str] = Field(..., min_length=1, description="選択されたメッセージIDリスト")


@router.post(
    "/{thread_id}/scene-image",
    summary="シーン画像生成",
    description="選択したメッセージの内容に基づいてシーン画像を生成します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "他ユーザーのスレッド"},
        404: {"description": "スレッド not found"},
        503: {"description": "画像生成サービス利用不可"},
    },
)
async def generate_scene_image(
    thread_id: str,
    request: SceneImageRequest,
    user_state: OnboardedUser,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    シーン画像生成

    - Verify thread ownership
    - Get selected messages
    - Generate scene description using LLM
    - Generate image using DALL-E
    - Save as image message in chat
    """
    # Get thread and verify ownership
    session = await conversation_service.get_thread(thread_id, user_state.user_id)
    if not session:
        raise NotFoundException("スレッドが見つかりません")

    # Get selected messages by IDs
    db = conversation_service.db
    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.id.in_(request.message_ids))
        .where(ConversationMessage.session_id == thread_id)
        .order_by(ConversationMessage.created_at.asc())
    )
    messages = list(result.scalars().all())

    if not messages:
        raise NotFoundException("選択されたメッセージが見つかりません")

    # Generate scene description using LLM
    scene_service = SceneService()
    scene_prompt = await scene_service.generate_scene_prompt(
        character_name=session.character.name,
        character_description=session.character.description,
        messages=messages,
        appearance_description=session.character.appearance_description,
    )

    if not scene_prompt:
        raise ServiceUnavailableException("シーン生成に失敗しました")

    # Generate image
    image_service = ImageService()
    image_url = await image_service.generate_scene_image(scene_prompt)

    if not image_url:
        raise ServiceUnavailableException("画像生成サービスが利用できません")

    # Save as image message in chat
    image_message = ConversationMessage.create_image_message(
        session_id=thread_id,
        image_url=image_url,
        content="シーン画像を生成しました",
    )
    db.add(image_message)
    await db.commit()

    return {
        "message_id": image_message.id,
        "image_url": image_url,
        "expires_at": image_message.expires_at.isoformat() if image_message.expires_at else None,
    }


# =============================================================================
# Helper Functions
# =============================================================================


def _session_to_thread(session) -> Thread:
    """Convert ConversationSession model to Thread schema"""
    from app.models import ConversationSession

    return Thread(
        id=session.id,
        pack_id=session.pack_id or "",
        character=CharacterSchema(
            id=session.character.id,
            name=session.character.name,
            avatar_url=session.character.image_url,
        ),
        session_type=session.session_type,
        event_id=None,
        message_count=0,
        last_message=None,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _message_to_schema(message) -> Message:
    """Convert ConversationMessage model to Message schema"""
    return Message(
        id=message.id,
        role=message.role,
        content=message.content,
        content_type=message.content_type or "text",
        image_url=message.image_url,
        expires_at=message.expires_at,
        created_at=message.created_at,
    )
