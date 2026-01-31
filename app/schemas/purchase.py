"""Purchase schemas - matching openapi.yaml Purchase components"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Request Models
# =============================================================================


class CreatePurchaseRequest(BaseModel):
    """Create purchase request"""

    pack_id: str = Field(..., description="購入対象の Pack ID")
    payment_method: Literal["stripe", "apple", "google"] = Field(..., description="決済方法")
    receipt_data: Optional[str] = Field(None, description="決済プロバイダーからのレシート")


class RestorePurchaseRequest(BaseModel):
    """Restore purchase request"""

    payment_method: Literal["stripe", "apple", "google"] = Field(..., description="決済方法")
    receipt_data: Optional[str] = Field(None, description="レシートデータ")


# =============================================================================
# Response Models
# =============================================================================


class Purchase(BaseModel):
    """Purchase object"""

    id: str
    pack_id: str
    amount: int = Field(..., description="購入金額")
    currency: Literal["JPY", "USD"] = "JPY"
    payment_method: Optional[Literal["stripe", "apple", "google"]] = None
    status: Literal["pending", "completed", "failed", "refunded"]
    created_at: datetime


class Entitlement(BaseModel):
    """Entitlement object"""

    id: str
    entitlement_type: Literal["pack"]
    entitlement_id: str
    granted_at: datetime
    revoked_at: Optional[datetime] = None


class PurchaseResponse(BaseModel):
    """Purchase response"""

    purchase: Purchase
    entitlement: Entitlement


class RestorePurchaseResponse(BaseModel):
    """Restore purchase response"""

    restored_count: int
    entitlements: List[Entitlement]


class EntitlementListResponse(BaseModel):
    """Entitlement list response"""

    data: List[Entitlement]
