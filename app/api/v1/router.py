"""API v1 router aggregating all endpoints."""

from fastapi import APIRouter
from app.api.v1.endpoints import extraction, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    extraction.router,
    prefix="/text",
    tags=["Text Extraction"],
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["Health Checks"],
)