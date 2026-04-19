"""Inventory forecasting FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from inventory_app.core.settings import get_settings
from inventory_app.routes.api import api_router, legacy_api_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Serve React static files
    if os.path.exists("frontend/build/static"):
        app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

        @app.get("/{full_path:path}")
        async def serve_react(full_path: str):
            if full_path.startswith("api"):
                return {"error": "API route not found"}
            return FileResponse("frontend/build/index.html")

    app.include_router(api_router)
    app.include_router(legacy_api_router)

    return app

