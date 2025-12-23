"""Application factory for creating FastAPI app instance."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.exceptions import setup_exception_handlers
from app.api.v1.router import api_router
from app.core.middleware import setup_middleware
import os


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    # Setup logging
    setup_logging()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Mount static files
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    
    @app.get("/")
    async def root():
        """Redirect to API documentation."""
        return RedirectResponse(url=f"{settings.API_V1_STR}/docs")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "success": True,
            "data": {
                "status": "healthy", 
                "version": settings.VERSION
            }
        }
    
    return app