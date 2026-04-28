"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analytics_routes import router as analytics_router
from app.api.routes.game_routes import router as game_router
from app.models.database import init_db

_ALLOWED_ORIGINS_DEFAULT = "http://localhost:8501,http://127.0.0.1:8501"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _ALLOWED_ORIGINS_DEFAULT).split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize persistence resources during application startup."""
    init_db()
    yield

app = FastAPI(
    title="DiceQuest Analytics API",
    description="Interactive text adventure game API",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
# Origins are read from the ALLOWED_ORIGINS environment variable (comma-separated).
# Wildcard origin with allow_credentials=True is invalid per the CORS spec;
# credentials are not required for this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(analytics_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
