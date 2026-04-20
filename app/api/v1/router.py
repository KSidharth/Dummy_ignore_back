
"""
API v1 router registry.
Aggregates all v1 endpoint routers for inclusion in main app.
"""
from fastapi import APIRouter
from app.api.v1 import auth


# Create v1 API router
api_v1_router = APIRouter()

# Register all v1 endpoint routers
api_v1_router.include_router(auth.router)
