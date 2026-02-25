"""Backward-compatible module exposing the ASGI app instance."""

from __future__ import annotations

import uvicorn

from inventory_app import create_app
from inventory_app.core.settings import get_settings

app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("app:app", host=settings.host, port=settings.port, reload=False)

