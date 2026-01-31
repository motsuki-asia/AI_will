"""API v1 routers"""
from .auth import router as auth_router
from .catalog import router as catalog_router
from .conversation import router as conversation_router
from .purchase import router as purchase_router
from .memory import router as memory_router
from .safety import router as safety_router
from .privacy import router as privacy_router

__all__ = [
    "auth_router",
    "catalog_router",
    "conversation_router",
    "purchase_router",
    "memory_router",
    "safety_router",
    "privacy_router",
]
