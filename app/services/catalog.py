"""Catalog service - Pack/Character listing and details"""
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Pack, Character, PackItem
from app.schemas.catalog import (
    Pack as PackSchema,
    PackStats,
    UserStatus,
    PackItem as PackItemSchema,
)
from app.schemas.common import Creator as CreatorSchema, Pagination


class CatalogService:
    """Service for catalog operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_packs(
        self,
        user_id: str,
        user_age_group: Optional[str] = None,
        pack_type: Optional[str] = None,
        query: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[List[PackSchema], Pagination]:
        """
        List published packs with filtering and pagination

        Args:
            user_id: Current user ID
            user_age_group: User's age group for filtering
            pack_type: Filter by pack type (persona/scenario)
            query: Search query
            cursor: Pagination cursor (pack ID)
            limit: Number of results

        Returns:
            Tuple of (packs, pagination)
        """
        # Base query - only published, not deleted
        stmt = (
            select(Pack)
            .where(Pack.status == Pack.STATUS_PUBLISHED)
            .where(Pack.deleted_at.is_(None))
            .options(selectinload(Pack.creator))
        )

        # Filter by pack type
        if pack_type:
            stmt = stmt.where(Pack.pack_type == pack_type)

        # Filter by age rating based on user's age group
        if user_age_group == "u13":
            stmt = stmt.where(Pack.age_rating == Pack.AGE_RATING_ALL)
        elif user_age_group == "u18":
            stmt = stmt.where(Pack.age_rating.in_([Pack.AGE_RATING_ALL, Pack.AGE_RATING_R15]))
        # adult can see all

        # Search by name/description
        if query:
            search_term = f"%{query}%"
            stmt = stmt.where(
                (Pack.name.ilike(search_term)) |
                (Pack.description.ilike(search_term))
            )

        # Cursor-based pagination
        if cursor:
            stmt = stmt.where(Pack.id > cursor)

        # Order and limit
        stmt = stmt.order_by(Pack.created_at.desc()).limit(limit + 1)

        result = await self.db.execute(stmt)
        packs = list(result.scalars().all())

        # Check if there are more results
        has_more = len(packs) > limit
        if has_more:
            packs = packs[:limit]

        # Convert to schema
        pack_schemas = []
        for pack in packs:
            pack_schema = self._pack_to_schema(pack)
            pack_schemas.append(pack_schema)

        pagination = Pagination(
            next_cursor=packs[-1].id if has_more and packs else None,
            has_more=has_more,
        )

        return pack_schemas, pagination

    async def get_pack(
        self,
        pack_id: str,
        user_id: str,
        user_age_group: Optional[str] = None,
    ) -> Optional[Tuple[PackSchema, UserStatus]]:
        """
        Get pack detail by ID

        Args:
            pack_id: Pack ID
            user_id: Current user ID
            user_age_group: User's age group for access check

        Returns:
            Tuple of (pack, user_status) or None if not found
        """
        stmt = (
            select(Pack)
            .where(Pack.id == pack_id)
            .where(Pack.status == Pack.STATUS_PUBLISHED)
            .where(Pack.deleted_at.is_(None))
            .options(selectinload(Pack.creator))
        )

        result = await self.db.execute(stmt)
        pack = result.scalar_one_or_none()

        if not pack:
            return None

        # Check age restriction
        if user_age_group == "u13" and pack.age_rating != Pack.AGE_RATING_ALL:
            return None
        if user_age_group == "u18" and pack.age_rating == Pack.AGE_RATING_R18:
            return None

        pack_schema = self._pack_to_schema(pack)

        # MVP: No purchase/favorite tracking yet
        user_status = UserStatus(
            owned=pack.is_free,  # Free packs are "owned"
            favorited=False,
        )

        return pack_schema, user_status

    async def get_pack_items(
        self,
        pack_id: str,
        user_id: str,
    ) -> Optional[List[PackItemSchema]]:
        """
        Get items in a pack

        Args:
            pack_id: Pack ID
            user_id: Current user ID

        Returns:
            List of pack items or None if pack not found
        """
        # First verify pack exists and is published
        stmt = select(Pack).where(
            Pack.id == pack_id,
            Pack.status == Pack.STATUS_PUBLISHED,
            Pack.deleted_at.is_(None),
        )
        result = await self.db.execute(stmt)
        pack = result.scalar_one_or_none()

        if not pack:
            return None

        # Get pack items
        stmt = (
            select(PackItem)
            .where(PackItem.pack_id == pack_id)
            .where(PackItem.deleted_at.is_(None))
            .order_by(PackItem.sort_order)
        )
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        # Fetch character details for character items
        item_schemas = []
        for item in items:
            if item.item_type == PackItem.ITEM_TYPE_CHARACTER:
                char_result = await self.db.execute(
                    select(Character).where(Character.id == item.item_id)
                )
                character = char_result.scalar_one_or_none()
                if character:
                    item_schemas.append(PackItemSchema(
                        id=item.id,
                        item_type=item.item_type,
                        item_id=item.item_id,
                        name=character.name,
                        description=character.description,
                        avatar_url=character.image_url,
                    ))
            else:
                # For non-character items, just return basic info
                item_schemas.append(PackItemSchema(
                    id=item.id,
                    item_type=item.item_type,
                    item_id=item.item_id,
                    name="Unknown",
                    description=None,
                ))

        return item_schemas

    def _pack_to_schema(self, pack: Pack) -> PackSchema:
        """Convert Pack model to schema"""
        return PackSchema(
            id=pack.id,
            pack_type=pack.pack_type,
            name=pack.name,
            description=pack.description or "",
            thumbnail_url=pack.cover_image_url or "/static/default_pack.png",
            cover_url=pack.cover_image_url,
            sample_voice_url=None,
            price=pack.price or 0,
            is_free=pack.is_free,
            age_rating=pack.age_rating,
            tags=[],  # MVP: No tags yet
            creator=CreatorSchema(
                id=pack.creator.id,
                display_name=pack.creator.display_name,
                avatar_url=None,
            ),
            stats=PackStats(
                favorite_count=0,
                conversation_count=0,
                review_count=0,
                average_rating=None,
            ),
            created_at=pack.created_at,
            updated_at=pack.updated_at,
        )
