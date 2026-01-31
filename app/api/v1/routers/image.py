"""Image generation and partner creation API endpoints"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import OnboardedUser
from app.db.database import get_db
from app.services.image import ImageService
from app.services.tts import TTSService
from app.models import Character, ConversationSession
from app.core.errors import ServiceUnavailableException


router = APIRouter(prefix="/images", tags=["images"])

# サンプル音声のテキスト
VOICE_SAMPLE_TEXTS = {
    "nova": "こんにちは、私はNovaです。明るくて元気な声でお話しします。",
    "shimmer": "こんにちは、私はShimmerです。柔らかい声でお話しします。",
    "alloy": "こんにちは、私はAlloyです。中性的な声でお話しします。",
    "echo": "こんにちは、私はEchoです。男性的な声でお話しします。",
    "fable": "こんにちは、私はFableです。英国風の声でお話しします。",
    "onyx": "こんにちは、私はOnyxです。深みのある声でお話しします。",
}


# =============================================================================
# Schemas
# =============================================================================


class GenerateImageRequest(BaseModel):
    """Request to generate a character image"""
    name: str = Field(..., min_length=1, max_length=20, description="キャラクター名")
    description: Optional[str] = Field(None, max_length=200, description="性格・特徴")
    style: str = Field("anime", description="アートスタイル (anime, realistic, illustration)")


class CreatePartnerRequest(BaseModel):
    """Request to create a custom partner"""
    name: str = Field(..., min_length=1, max_length=20, description="パートナー名")
    description: Optional[str] = Field(None, max_length=200, description="性格・特徴")
    image_url: str = Field(..., description="画像URL")
    voice_id: Literal["nova", "shimmer", "alloy", "echo", "fable", "onyx"] = Field(
        "nova", description="声の種類"
    )


class PartnerResponse(BaseModel):
    """Response with created partner"""
    character_id: str
    thread_id: str
    name: str
    image_url: str
    voice_id: str


class GenerateImageResponse(BaseModel):
    """Response with generated image URL"""
    image_url: str
    style: str


class StylesResponse(BaseModel):
    """Available styles response"""
    styles: list[dict]


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/generate",
    response_model=GenerateImageResponse,
    summary="キャラクター画像生成",
    description="DALL-E 3を使用してキャラクター画像を生成します。",
    responses={
        401: {"description": "認証エラー"},
        503: {"description": "画像生成サービス利用不可"},
    },
)
async def generate_image(
    request: GenerateImageRequest,
    user_state: OnboardedUser,
) -> GenerateImageResponse:
    """Generate a character image using DALL-E 3"""
    
    service = ImageService()
    
    image_url = await service.generate_character_image(
        name=request.name,
        description=request.description,
        style=request.style,
    )
    
    if not image_url:
        raise ServiceUnavailableException(
            "画像生成サービスが利用できません。LLM_API_KEYを確認してください。"
        )
    
    return GenerateImageResponse(
        image_url=image_url,
        style=request.style,
    )


@router.get(
    "/styles",
    response_model=StylesResponse,
    summary="利用可能なスタイル一覧",
    description="画像生成で使用可能なアートスタイルの一覧を取得します。",
)
async def get_styles() -> StylesResponse:
    """Get available art styles"""
    service = ImageService()
    return StylesResponse(styles=service.get_available_styles())


@router.get(
    "/voice-sample/{voice_id}",
    summary="声のサンプル音声",
    description="指定した声のサンプル音声を取得します。",
    responses={
        200: {"content": {"audio/mpeg": {}}},
        503: {"description": "TTSサービス利用不可"},
    },
)
async def get_voice_sample(
    voice_id: Literal["nova", "shimmer", "alloy", "echo", "fable", "onyx"],
    user_state: OnboardedUser,
) -> Response:
    """Get a voice sample audio for the specified voice"""
    
    sample_text = VOICE_SAMPLE_TEXTS.get(voice_id, "こんにちは、よろしくお願いします。")
    
    tts_service = TTSService()
    audio_data = await tts_service.synthesize(text=sample_text, voice=voice_id)
    
    if not audio_data:
        raise ServiceUnavailableException(
            "TTSサービスが利用できません。LLM_API_KEYを確認してください。"
        )
    
    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'inline; filename="voice-sample-{voice_id}.mp3"',
            "Cache-Control": "public, max-age=86400",  # 1日キャッシュ
        },
    )


# =============================================================================
# Partner Creation
# =============================================================================


@router.post(
    "/partner",
    response_model=PartnerResponse,
    summary="カスタムパートナー作成",
    description="カスタムパートナーを作成し、会話スレッドを開始します。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def create_partner(
    request: CreatePartnerRequest,
    user_state: OnboardedUser,
    db: AsyncSession = Depends(get_db),
) -> PartnerResponse:
    """Create a custom partner and start a conversation thread"""
    
    # Build system prompt from description
    system_prompt = f"""あなたは「{request.name}」というキャラクターです。

性格・特徴:
{request.description or '親しみやすくて、相手の話をよく聞く'}

話し方:
- カジュアルな日本語
- 絵文字は使わない
- 相槌をよく打つ
- 短めの返答を心がける

注意:
- 不適切な内容には応じない
- 個人情報を聞き出さない
"""

    # Create character
    character = Character(
        user_id=user_state.user_id,
        name=request.name,
        description=request.description,
        system_prompt=system_prompt,
        image_url=request.image_url,
        voice_id=request.voice_id,
        status=Character.STATUS_PUBLISHED,
    )
    db.add(character)
    await db.flush()
    
    # Create conversation thread
    session = ConversationSession(
        user_id=user_state.user_id,
        character_id=character.id,
        session_type=ConversationSession.SESSION_TYPE_FREE,
    )
    db.add(session)
    await db.commit()
    
    return PartnerResponse(
        character_id=character.id,
        thread_id=session.id,
        name=character.name,
        image_url=character.image_url or "",
        voice_id=character.voice_id,
    )
