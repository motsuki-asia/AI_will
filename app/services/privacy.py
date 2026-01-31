"""Privacy service - Data export and deletion"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConversationSession


class PrivacyService:
    """Service for privacy operations (data export and deletion)"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_conversations(
        self,
        user_id: str,
        scope: str = "conversations",
    ) -> int:
        """
        Delete user's conversation data

        Args:
            user_id: User ID
            scope: Deletion scope (conversations, memories, all)

        Returns:
            Number of sessions deleted
        """
        # Get all user's sessions
        result = await self.db.execute(
            select(ConversationSession)
            .where(ConversationSession.user_id == user_id)
            .where(ConversationSession.deleted_at.is_(None))
        )
        sessions = result.scalars().all()

        count = 0
        now = datetime.now(timezone.utc)

        for session in sessions:
            session.deleted_at = now
            count += 1

        await self.db.flush()
        return count

    async def create_delete_job(
        self,
        user_id: str,
        scope: str,
    ) -> dict:
        """
        Create a delete job (MVP: synchronous deletion)

        Args:
            user_id: User ID
            scope: Deletion scope

        Returns:
            Job info dict
        """
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # MVP: Perform synchronous deletion
        deleted_count = await self.delete_conversations(user_id, scope)

        return {
            "job_id": job_id,
            "status": "completed",
            "scope": scope,
            "progress": {
                "total_items": deleted_count,
                "processed_items": deleted_count,
                "percentage": 100,
            },
            "grace_period_until": None,
            "created_at": now,
            "completed_at": now,
            "cancelled_at": None,
        }
