"""Purchase router - matching openapi.yaml Purchase paths"""
from fastapi import APIRouter, status

from app.deps import IdempotencyKey, OnboardedUser
from app.schemas.purchase import (
    CreatePurchaseRequest,
    EntitlementListResponse,
    PurchaseResponse,
    RestorePurchaseRequest,
    RestorePurchaseResponse,
)

router = APIRouter(tags=["Purchase"])


# =============================================================================
# POST /purchases - 購入
# =============================================================================
@router.post(
    "/purchases",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="購入",
    description="Packを購入します。Idempotency-Keyヘッダー必須。",
    responses={
        400: {"description": "バリデーションエラー / Idempotency-Key未指定"},
        401: {"description": "認証エラー"},
        409: {"description": "購入済み / 処理中"},
    },
)
async def create_purchase(
    user_state: OnboardedUser,
    idempotency_key: IdempotencyKey,
    request: CreatePurchaseRequest,
) -> PurchaseResponse:
    """
    購入

    TODO: Implement create_purchase
    - Check idempotency (return cached response if exists)
    - Verify receipt with payment provider
    - Check if already purchased
    - Create purchase record
    - Grant entitlement
    - Cache response for idempotency
    """
    raise NotImplementedError("TODO: Implement create_purchase")


# =============================================================================
# POST /purchases:restore - 購入復元
# =============================================================================
@router.post(
    "/purchases:restore",
    response_model=RestorePurchaseResponse,
    summary="購入復元",
    description="ストアの購入状態を復元します。Idempotency-Keyヘッダー必須。",
    responses={
        400: {"description": "バリデーションエラー"},
        401: {"description": "認証エラー"},
    },
)
async def restore_purchases(
    user_state: OnboardedUser,
    idempotency_key: IdempotencyKey,
    request: RestorePurchaseRequest,
) -> RestorePurchaseResponse:
    """
    購入復元

    TODO: Implement restore_purchases
    - Verify receipt with payment provider
    - Restore entitlements for all valid purchases
    """
    raise NotImplementedError("TODO: Implement restore_purchases")


# =============================================================================
# GET /entitlements - 利用権一覧取得
# =============================================================================
@router.get(
    "/entitlements",
    response_model=EntitlementListResponse,
    summary="利用権一覧取得",
    description="ユーザーが保持する利用権の一覧を取得します。",
    responses={
        401: {"description": "認証エラー"},
    },
)
async def list_entitlements(
    user_state: OnboardedUser,
) -> EntitlementListResponse:
    """
    利用権一覧取得

    TODO: Implement list_entitlements
    - Fetch user's entitlements
    """
    raise NotImplementedError("TODO: Implement list_entitlements")
