"""Catalog router - matching openapi.yaml Catalog paths"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException
from app.db.database import get_db
from app.deps import OnboardedUser, Pagination, Sort
from app.schemas.catalog import (
    PackDetailResponse,
    PackItemsResponse,
    PackListResponse,
    TagListResponse,
    UserStatus,
    CharacterListResponse,
)
from app.schemas.common import Pagination as PaginationSchema, Tag
from app.services.catalog import CatalogService

router = APIRouter(prefix="/packs", tags=["Catalog"])
characters_router = APIRouter(prefix="/characters", tags=["Catalog"])
tags_router = APIRouter(prefix="/tags", tags=["Catalog"])


def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    """Dependency to get CatalogService"""
    return CatalogService(db)


# =============================================================================
# GET /packs - Pack一覧取得
# =============================================================================
@router.get(
    "",
    response_model=PackListResponse,
    summary="Pack一覧取得",
    description="Persona/Scenario Packの一覧を取得します。フィルタ・ソート・ページング対応。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
        403: {"description": "オンボーディング未完了"},
    },
)
async def list_packs(
    user_state: OnboardedUser,
    pagination: Pagination,
    sort: Sort,
    type: Optional[Literal["persona", "scenario"]] = Query(None, description="Pack種別"),
    query: Optional[str] = Query(None, description="キーワード検索"),
    tags: Optional[str] = Query(None, description="タグ絞り込み（カンマ区切り）"),
    age_rating: Optional[Literal["all", "r15", "r18"]] = Query(None, description="年齢レーティング"),
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> PackListResponse:
    """
    Pack一覧取得

    - Apply age_rating filter based on user's age_group
    - Filter by type, query
    - Apply pagination
    - Join with creator info
    """
    packs, page_info = await catalog_service.list_packs(
        user_id=user_state.user_id,
        user_age_group=user_state.age_group,
        pack_type=type,
        query=query,
        cursor=pagination.cursor,
        limit=pagination.limit,
    )

    return PackListResponse(
        data=packs,
        pagination=page_info,
    )


# =============================================================================
# GET /packs/{pack_id} - Pack詳細取得
# =============================================================================
@router.get(
    "/{pack_id}",
    response_model=PackDetailResponse,
    summary="Pack詳細取得",
    description="指定したPackの詳細情報を取得します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "年齢制限"},
        404: {"description": "Pack not found"},
    },
)
async def get_pack(
    pack_id: str,
    user_state: OnboardedUser,
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> PackDetailResponse:
    """
    Pack詳細取得

    - Fetch pack from database
    - Check age restriction
    - Get user's ownership and favorite status
    """
    result = await catalog_service.get_pack(
        pack_id=pack_id,
        user_id=user_state.user_id,
        user_age_group=user_state.age_group,
    )

    if not result:
        raise NotFoundException("Packが見つかりません")

    pack, user_status = result
    return PackDetailResponse(
        pack=pack,
        user_status=user_status,
    )


# =============================================================================
# GET /packs/{pack_id}/items - Pack構成アイテム取得
# =============================================================================
@router.get(
    "/{pack_id}/items",
    response_model=PackItemsResponse,
    summary="Pack構成アイテム取得",
    description="Packに含まれるキャラクター、イベント等の構成アイテムを取得します。",
    responses={
        401: {"description": "認証エラー"},
        404: {"description": "Pack not found"},
    },
)
async def get_pack_items(
    pack_id: str,
    user_state: OnboardedUser,
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> PackItemsResponse:
    """
    Pack構成アイテム取得

    - Fetch pack items (characters, events, etc.)
    """
    items = await catalog_service.get_pack_items(
        pack_id=pack_id,
        user_id=user_state.user_id,
    )

    if items is None:
        raise NotFoundException("Packが見つかりません")

    return PackItemsResponse(data=items)


# =============================================================================
# GET /characters - キャラクター一覧取得
# =============================================================================
@characters_router.get(
    "",
    response_model=CharacterListResponse,
    summary="キャラクター一覧取得",
    description="公開中のキャラクター一覧を取得します。",
    responses={
        401: {"description": "認証エラー"},
        403: {"description": "オンボーディング未完了"},
    },
)
async def list_characters(
    user_state: OnboardedUser,
    pagination: Pagination,
    query: Optional[str] = Query(None, description="キーワード検索"),
    catalog_service: CatalogService = Depends(get_catalog_service),
) -> CharacterListResponse:
    """
    キャラクター一覧取得

    - List all characters from published packs
    - Apply age_rating filter based on user's age_group
    - Apply pagination
    """
    characters, page_info = await catalog_service.list_characters(
        user_id=user_state.user_id,
        user_age_group=user_state.age_group,
        query=query,
        cursor=pagination.cursor,
        limit=pagination.limit,
    )

    return CharacterListResponse(
        data=characters,
        pagination=page_info,
    )


# =============================================================================
# GET /tags - タグ一覧取得
# =============================================================================
@tags_router.get(
    "",
    response_model=TagListResponse,
    summary="タグ一覧取得",
    description="利用可能なタグの一覧を取得します。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def list_tags(
    user_state: OnboardedUser,
    type: Optional[Literal["pack", "character"]] = Query(None, description="タグ種別"),
) -> TagListResponse:
    """
    タグ一覧取得

    MVP: Returns empty list (tags not implemented yet)
    """
    # MVP: No tags implemented yet
    return TagListResponse(data=[])
