"""Conversation service - Thread and message management"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import ConversationSession, ConversationMessage, Character
from app.schemas.conversation import (
    Thread,
    Message,
    Relationship,
    RelationshipStage,
)
from app.schemas.common import Character as CharacterSchema, Pagination


class ConversationService:
    """Service for conversation operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_thread(
        self,
        user_id: str,
        pack_id: str,
        character_id: str,
    ) -> Optional[ConversationSession]:
        """
        Get existing thread or create a new conversation thread.
        
        If user already has a thread with this character, return the existing one.
        Otherwise create a new thread.

        Args:
            user_id: User ID
            pack_id: Pack ID (for entitlement check)
            character_id: Character ID to converse with

        Returns:
            ConversationSession (existing or new) or None if character not found
        """
        # Verify character exists and is published
        result = await self.db.execute(
            select(Character)
            .where(Character.id == character_id)
            .where(Character.status == Character.STATUS_PUBLISHED)
            .where(Character.deleted_at.is_(None))
        )
        character = result.scalar_one_or_none()
        if not character:
            return None

        # Check for existing thread with this character
        existing_result = await self.db.execute(
            select(ConversationSession)
            .where(ConversationSession.user_id == user_id)
            .where(ConversationSession.character_id == character_id)
            .where(ConversationSession.deleted_at.is_(None))
            .order_by(ConversationSession.updated_at.desc())
            .limit(1)
        )
        existing_session = existing_result.scalar_one_or_none()
        
        if existing_session:
            # Return existing thread
            existing_session.character = character
            return existing_session

        # MVP: Skip entitlement check (all free packs)
        # TODO: Check if user owns the pack or it's free

        # Create new session
        session = ConversationSession(
            user_id=user_id,
            character_id=character_id,
            session_type=ConversationSession.SESSION_TYPE_FREE,
        )
        self.db.add(session)
        await self.db.flush()

        # Attach the character to the session for immediate access
        session.character = character

        return session

    async def list_threads(
        self,
        user_id: str,
        character_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[List[ConversationSession], Pagination]:
        """
        List user's conversation threads

        Args:
            user_id: User ID
            character_id: Optional filter by character
            cursor: Pagination cursor
            limit: Number of results

        Returns:
            Tuple of (sessions, pagination)
        """
        stmt = (
            select(ConversationSession)
            .where(ConversationSession.user_id == user_id)
            .where(ConversationSession.deleted_at.is_(None))
            .options(selectinload(ConversationSession.character))
        )

        if character_id:
            stmt = stmt.where(ConversationSession.character_id == character_id)

        if cursor:
            stmt = stmt.where(ConversationSession.id < cursor)

        stmt = stmt.order_by(ConversationSession.updated_at.desc()).limit(limit + 1)

        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())

        has_more = len(sessions) > limit
        if has_more:
            sessions = sessions[:limit]

        pagination = Pagination(
            next_cursor=sessions[-1].id if has_more and sessions else None,
            has_more=has_more,
        )

        return sessions, pagination

    async def get_thread(
        self,
        thread_id: str,
        user_id: str,
    ) -> Optional[ConversationSession]:
        """
        Get a specific thread

        Args:
            thread_id: Thread ID
            user_id: User ID (for ownership check)

        Returns:
            ConversationSession or None
        """
        result = await self.db.execute(
            select(ConversationSession)
            .where(ConversationSession.id == thread_id)
            .where(ConversationSession.user_id == user_id)
            .where(ConversationSession.deleted_at.is_(None))
            .options(selectinload(ConversationSession.character))
        )
        return result.scalar_one_or_none()

    async def delete_thread(
        self,
        thread_id: str,
        user_id: str,
    ) -> bool:
        """
        Soft delete a thread

        Args:
            thread_id: Thread ID
            user_id: User ID (for ownership check)

        Returns:
            True if deleted, False if not found
        """
        session = await self.get_thread(thread_id, user_id)
        if not session:
            return False

        session.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def list_messages(
        self,
        thread_id: str,
        user_id: str,
        cursor: Optional[str] = None,
        limit: int = 50,
        order: str = "desc",
    ) -> Optional[Tuple[List[ConversationMessage], Pagination]]:
        """
        List messages in a thread

        Args:
            thread_id: Thread ID
            user_id: User ID (for ownership check)
            cursor: Pagination cursor
            limit: Number of results
            order: 'asc' or 'desc'

        Returns:
            Tuple of (messages, pagination) or None if thread not found
        """
        # Verify thread ownership
        session = await self.get_thread(thread_id, user_id)
        if not session:
            return None

        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.session_id == thread_id)
        )

        if cursor:
            if order == "desc":
                stmt = stmt.where(ConversationMessage.id < cursor)
            else:
                stmt = stmt.where(ConversationMessage.id > cursor)

        if order == "desc":
            stmt = stmt.order_by(ConversationMessage.created_at.desc())
        else:
            stmt = stmt.order_by(ConversationMessage.created_at.asc())

        stmt = stmt.limit(limit + 1)

        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())

        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        pagination = Pagination(
            next_cursor=messages[-1].id if has_more and messages else None,
            has_more=has_more,
        )

        return messages, pagination

    async def send_message(
        self,
        thread_id: str,
        user_id: str,
        content: str,
    ) -> Optional[Tuple[ConversationMessage, ConversationMessage]]:
        """
        Send a message and get AI response

        Args:
            thread_id: Thread ID
            user_id: User ID (for ownership check)
            content: User's message content

        Returns:
            Tuple of (user_message, ai_message) or None if thread not found
        """
        # Verify thread ownership
        result = await self.db.execute(
            select(ConversationSession)
            .where(ConversationSession.id == thread_id)
            .where(ConversationSession.user_id == user_id)
            .where(ConversationSession.deleted_at.is_(None))
            .options(selectinload(ConversationSession.character))
        )
        session = result.scalar_one_or_none()
        if not session:
            return None

        # Save user message
        user_message = ConversationMessage(
            session_id=thread_id,
            role=ConversationMessage.ROLE_USER,
            content=content,
        )
        self.db.add(user_message)
        await self.db.flush()

        # Generate AI response
        ai_response = await self._generate_response(
            session=session,
            user_message=content,
        )

        # Save AI message
        ai_message = ConversationMessage(
            session_id=thread_id,
            role=ConversationMessage.ROLE_CHARACTER,
            content=ai_response,
        )
        self.db.add(ai_message)
        await self.db.flush()

        # Update session's updated_at for proper sorting in conversation list
        session.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

        return user_message, ai_message

    async def _generate_response(
        self,
        session: ConversationSession,
        user_message: str,
    ) -> str:
        """
        Generate AI response

        Uses OpenAI API if LLM_API_KEY is set, otherwise returns stub response.

        Args:
            session: Conversation session (with character loaded)
            user_message: User's message

        Returns:
            AI response text
        """
        character = session.character

        # Check if LLM API is configured
        if settings.LLM_API_KEY:
            try:
                return await self._call_llm_api(
                    system_prompt=character.system_prompt or self._default_prompt(character),
                    user_message=user_message,
                    session=session,
                )
            except Exception as e:
                # Fall back to stub on error
                print(f"LLM API error: {e}")
                return self._stub_response(character, user_message)
        else:
            # Stub response for MVP without LLM
            return self._stub_response(character, user_message)

    async def _call_llm_api(
        self,
        system_prompt: str,
        user_message: str,
        session: ConversationSession,
    ) -> str:
        """Call OpenAI API for response generation"""
        import openai

        client = openai.AsyncOpenAI(api_key=settings.LLM_API_KEY)

        # Get recent messages for context
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session.id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(10)
        )
        recent_messages = list(result.scalars().all())
        recent_messages.reverse()

        # Build messages list
        messages = [{"role": "system", "content": system_prompt}]
        for msg in recent_messages:
            role = "user" if msg.role == ConversationMessage.ROLE_USER else "assistant"
            messages.append({"role": role, "content": msg.content})
        messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )

        return response.choices[0].message.content or "..."

    def _stub_response(self, character: Character, user_message: str) -> str:
        """Generate a stub response for MVP testing"""
        name = character.name
        responses = [
            f"こんにちは！{name}です。お話できて嬉しいです！",
            "なるほど、そうなんですね。もっと聞かせてください！",
            f"ありがとうございます。{name}もそう思います。",
            f"面白いですね！{name}はそういう話が大好きです。",
            f"分かります。{name}も同じ気持ちになることがあります。",
        ]
        # Simple selection based on message length
        index = len(user_message) % len(responses)
        return responses[index]

    def _default_prompt(self, character: Character) -> str:
        """Generate a default system prompt if none is set"""
        return f"""あなたは「{character.name}」というキャラクターです。

性格:
- 親しみやすい
- 相手の話をよく聞く
- ポジティブ

話し方:
- カジュアルな日本語
- 絵文字は使わない
- 相槌をよく打つ

注意:
- 不適切な内容には応じない
- 個人情報を聞き出さない
"""

    def session_to_thread(self, session: ConversationSession) -> Thread:
        """Convert ConversationSession to Thread schema"""
        return Thread(
            id=session.id,
            character=CharacterSchema(
                id=session.character.id,
                name=session.character.name,
                avatar_url=session.character.image_url,
            ),
            last_message=None,  # MVP: Not loading last message
            relationship=Relationship(
                affection=0,
                stage=RelationshipStage(
                    id="initial",
                    name="初対面",
                ),
            ),
            message_count=0,  # MVP: Not counting
            created_at=session.created_at,
            updated_at=session.updated_at,
        )

    def message_to_schema(self, message: ConversationMessage) -> Message:
        """Convert ConversationMessage to Message schema"""
        return Message(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at,
        )
