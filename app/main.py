"""
AI will API - FastAPI Application Entry Point

This is the main application file that sets up the FastAPI application,
registers routers, and configures middleware and exception handlers.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.routers import (
    auth_router,
    catalog_router,
    conversation_router,
    memory_router,
    privacy_router,
    purchase_router,
    safety_router,
)
from app.api.v1.routers.image import router as image_router
from app.api.v1.routers.auth import me_router
from app.api.v1.routers.catalog import tags_router
from app.core.config import settings
from app.core.errors import (
    APIException,
    api_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)


# =============================================================================
# Lifespan Management
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler

    Startup:
    - Create database tables (dev only, use alembic in production)
    
    Shutdown:
    - Close database connections
    """
    from app.db.database import engine
    from app.db.base import Base
    # Import models to register them with Base
    from app.models import (  # noqa: F401
        User, RefreshToken, Creator, Pack, Character, PackItem,
        ConversationSession, ConversationMessage, ReportReason, Report,
    )

    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Create tables (for development - use alembic migrations in production)
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created (DEBUG mode)")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await engine.dispose()


# =============================================================================
# Application Factory
# =============================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI will - AI音声会話アプリのREST API",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # -------------------------------------------------------------------------
    # Exception Handlers (unified error format per rules/api.mdc)
    # -------------------------------------------------------------------------
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # -------------------------------------------------------------------------
    # Middleware
    # -------------------------------------------------------------------------

    # CORS - Allow all origins in development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=False if settings.DEBUG else True,  # credentials can't be used with wildcard
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # TODO: Add rate limiting middleware
    # TODO: Add request logging middleware

    # -------------------------------------------------------------------------
    # API Routes (v1)
    # -------------------------------------------------------------------------
    api_prefix = settings.API_V1_PREFIX

    # Auth
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(me_router, prefix=api_prefix)

    # Catalog
    app.include_router(catalog_router, prefix=api_prefix)
    app.include_router(tags_router, prefix=api_prefix)

    # Conversation
    app.include_router(conversation_router, prefix=api_prefix)

    # Purchase
    app.include_router(purchase_router, prefix=api_prefix)

    # Memory (Clips)
    app.include_router(memory_router, prefix=api_prefix)

    # Safety
    app.include_router(safety_router, prefix=api_prefix)

    # Privacy
    app.include_router(privacy_router, prefix=api_prefix)

    # Image Generation
    app.include_router(image_router, prefix=api_prefix)

    # -------------------------------------------------------------------------
    # Static Files (for generated images)
    # -------------------------------------------------------------------------
    import os
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


# =============================================================================
# Application Instance
# =============================================================================

app = create_app()


# =============================================================================
# Development Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
