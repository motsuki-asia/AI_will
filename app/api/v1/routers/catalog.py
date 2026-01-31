"""Catalog router - matching openapi.yaml Catalog paths"""
from typing import Literal, Optional

from fastapi import APIRouter, Query

from app.deps import OnboardedUser, Pagination, Sort
from app.schemas.catalog import (
    PackDetailResponse,
    PackItemsResponse,
    PackListResponse,
    TagListResponse,
)

router = APIRouter(prefix="/packs", tags=["Catalog"])
tags_router = APIRouter(prefix="/tags", tags=["Catalog"])


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
) -> PackListResponse:
    """
    Pack一覧取得

    TODO: Implement list_packs
    - Apply age_rating filter based on user's age_group
    - Filter by type, query, tags
    - Apply sorting and pagination
    - Join with tags, creator info
    """
    raise NotImplementedError("TODO: Implement list_packs")


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
) -> PackDetailResponse:
    """
    Pack詳細取得

    TODO: Implement get_pack
    - Fetch pack from database
    - Check age restriction
    - Get user's ownership and favorite status
    """
    raise NotImplementedError("TODO: Implement get_pack")


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
) -> PackItemsResponse:
    """
    Pack構成アイテム取得

    TODO: Implement get_pack_items
    - Fetch pack items (characters, events, etc.)
    """
    raise NotImplementedError("TODO: Implement get_pack_items")


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

    TODO: Implement list_tags
    - Fetch tags with counts
    - Filter by type if specified
    """
    raise NotImplementedError("TODO: Implement list_tags")
