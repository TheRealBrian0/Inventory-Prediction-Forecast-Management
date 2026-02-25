"""Route package exports."""

from inventory_app.routes.api import api_router, legacy_api_router
from inventory_app.routes.web import web_router

__all__ = ["api_router", "legacy_api_router", "web_router"]

