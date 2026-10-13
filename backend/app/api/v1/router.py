from fastapi import APIRouter

from app.api.v1.endpoints import auth, ingest, zones, incidents, admin
from app.bonus.trend import router as trend_router

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(ingest.router)
api_router.include_router(zones.router)
api_router.include_router(incidents.router)
api_router.include_router(admin.router)
api_router.include_router(trend_router.router)
