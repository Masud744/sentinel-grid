from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.session import AsyncSessionLocal, engine
from app.database.base import Base
from app.api.v1.router import api_router
from app.websocket.router import router as ws_router
from app.services.incident_service import recover_system_state_from_db
from scripts.seed_data import seed
import app.models  # Register all models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB schema, seed defaults & Reconstruct Zone States from DB
    await seed()

    async with AsyncSessionLocal() as db:
        recovered = await recover_system_state_from_db(db)
        print(f"[STARTUP] Successfully reconstructed zone states from database for {len(recovered)} zones.")

    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "system": settings.PROJECT_NAME,
        "status": "ONLINE",
        "api_docs": "/docs",
        "websocket_feed": "/ws/updates"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["*.db", "scs_rg.db*", "*.log", ".venv/*"]
    )
