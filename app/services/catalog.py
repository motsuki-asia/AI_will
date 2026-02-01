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
    CharacterListItem,
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

    async def list_characters(
        self,
        user_id: str,
        user_age_group: Optional[str] = None,
        query: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> Tuple[List[CharacterListItem], Pagination]:
        """
        List all characters from published packs and user's custom characters

        Args:
            user_id: Current user ID
            user_age_group: User's age group for filtering
            query: Search query
            cursor: Pagination cursor (character ID)
            limit: Number of results

        Returns:
            Tuple of (characters, pagination)
        """
        from sqlalchemy import or_
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"list_characters called: user_id={user_id}, age_group={user_age_group}")

        # Get published packs that user can access
        pack_stmt = (
            select(Pack)
            .where(Pack.status == Pack.STATUS_PUBLISHED)
            .where(Pack.deleted_at.is_(None))
        )

        # Filter by age rating based on user's age group
        if user_age_group == "u13":
            pack_stmt = pack_stmt.where(Pack.age_rating == Pack.AGE_RATING_ALL)
        elif user_age_group == "u18":
            pack_stmt = pack_stmt.where(Pack.age_rating.in_([Pack.AGE_RATING_ALL, Pack.AGE_RATING_R15]))

        pack_result = await self.db.execute(pack_stmt)
        accessible_packs = {p.id: p for p in pack_result.scalars().all()}
        logger.info(f"Found {len(accessible_packs)} accessible packs")

        # Get pack items of type character from accessible packs
        pack_items = {}
        if accessible_packs:
            item_stmt = (
                select(PackItem)
                .where(PackItem.pack_id.in_(accessible_packs.keys()))
                .where(PackItem.item_type == PackItem.ITEM_TYPE_CHARACTER)
                .where(PackItem.deleted_at.is_(None))
            )
            item_result = await self.db.execute(item_stmt)
            pack_items = {pi.item_id: pi for pi in item_result.scalars().all()}
            logger.info(f"Found {len(pack_items)} pack items")

        # Build character query: pack characters OR user's custom characters
        char_conditions = []
        
        # Pack characters (if any pack items exist)
        if pack_items:
            char_conditions.append(Character.id.in_(pack_items.keys()))
        
        # User's custom characters (user_id is set)
        char_conditions.append(Character.user_id == user_id)

        if not char_conditions:
            return [], Pagination(next_cursor=None, has_more=False)

        char_stmt = (
            select(Character)
            .where(or_(*char_conditions))
            .where(Character.status == Character.STATUS_PUBLISHED)
            .where(Character.deleted_at.is_(None))
        )

        # Search by name/description
        if query:
            search_term = f"%{query}%"
            char_stmt = char_stmt.where(
                (Character.name.ilike(search_term)) |
                (Character.description.ilike(search_term))
            )

        # Cursor-based pagination
        if cursor:
            char_stmt = char_stmt.where(Character.id > cursor)

        # Order and limit
        char_stmt = char_stmt.order_by(Character.created_at.desc()).limit(limit + 1)

        char_result = await self.db.execute(char_stmt)
        characters = list(char_result.scalars().all())
        logger.info(f"Found {len(characters)} characters")

        # Check if there are more results
        has_more = len(characters) > limit
        if has_more:
            characters = characters[:limit]

        # Convert to schema
        character_schemas = []
        for char in characters:
            # Check if it's a pack character or user's custom character
            pack_item = pack_items.get(char.id)
            if pack_item:
                pack = accessible_packs.get(pack_item.pack_id)
                if pack:
                    character_schemas.append(CharacterListItem(
                        id=char.id,
                        name=char.name,
                        description=char.description,
                        avatar_url=char.image_url,
                        pack_id=pack.id,
                        pack_name=pack.name,
                        is_custom=False,
                    ))
            elif char.user_id == user_id:
                # User's custom character
                character_schemas.append(CharacterListItem(
                    id=char.id,
                    name=char.name,
                    description=char.description,
                    avatar_url=char.image_url,
                    pack_id=None,
                    pack_name=None,
                    is_custom=True,
                ))

        pagination = Pagination(
            next_cursor=characters[-1].id if has_more and characters else None,
            has_more=has_more,
        )

        return character_schemas, pagination

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
