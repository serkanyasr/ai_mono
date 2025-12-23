"""API v1 router aggregation."""

from fastapi import APIRouter
from .endpoints import chat, sessions, health, cache, limits

# Create the main v1 router
router = APIRouter()

# Include all endpoint routers
router.include_router(health.router, tags=["health"])
router.include_router(chat.router, tags=["chat"])
router.include_router(sessions.router, tags=["sessions"])
router.include_router(cache.router, tags=["cache"])
router.include_router(limits.router, tags=["limits"])
