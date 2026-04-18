"""Server-rendered web routes (Python frontend via Jinja templates)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from inventory_app.core.settings import get_settings
from inventory_app.data.loader import InventoryDataError
from inventory_app.dependencies.data import get_inventory_dataframe
from inventory_app.services.dashboard import (
    get_all_products_forecast,
    get_dashboard_metrics,
    get_forecast_for_product,
)

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))
web_router = APIRouter(tags=["web"])


@web_router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request, store_id: str | None = None) -> HTMLResponse:
    """Dashboard page rendered from Jinja2 templates."""
    settings = get_settings()

    try:
        df = get_inventory_dataframe(settings)
    except InventoryDataError as exc:
        selected_store_id = store_id or settings.default_store_id
        return TEMPLATES.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={"request": request, "metrics": None, "forecasts": [], "load_error": str(exc), "selected_store_id": selected_store_id, "stores": ["S001", "S002", "S003", "S004", "S005"]},
        )

    selected_store_id = store_id or settings.default_store_id
    metrics = get_dashboard_metrics(
        df,
        periods=settings.forecast_periods,
        store_id=selected_store_id,
    )
    forecasts = get_all_products_forecast(
        df,
        periods=settings.forecast_periods,
        store_id=selected_store_id,
    )

    return TEMPLATES.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"request": request, "metrics": metrics, "forecasts": forecasts, "load_error": None, "selected_store_id": selected_store_id, "stores": ["S001", "S002", "S003", "S004", "S005"]},
    )


@web_router.get("/product/{product_id}", response_class=HTMLResponse)
def product_detail_page(product_id: str, request: Request, store_id: str | None = None) -> HTMLResponse:
    """Product details page with historical + forecast chart."""
    settings = get_settings()

    try:
        df = get_inventory_dataframe(settings)
    except InventoryDataError as exc:
        return TEMPLATES.TemplateResponse(
            request=request,
            name="product_detail.html",
            context={"request": request, "forecast": None, "forecast_chart": None, "load_error": str(exc)},
        )

    selected_store_id = store_id or settings.default_store_id
    forecast = get_forecast_for_product(
        df,
        product_id,
        store_id=selected_store_id,
        periods=settings.forecast_periods,
    )

    if not forecast:
        return TEMPLATES.TemplateResponse(
            request=request,
            name="product_detail.html",
            context={
                "request": request,
                "forecast": None,
                "forecast_chart": None,
                "load_error": (
                    f"No forecast data found for product '{product_id}' in "
                    f"store '{settings.default_store_id}'."
                ),
            },
            status_code=404,
        )

    forecast_chart = json.dumps(
        {
            "data": [
                {
                    "x": forecast["historical_dates"],
                    "y": forecast["historical_values"],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Historical Units Sold",
                },
                {
                    "x": forecast["forecast_dates"],
                    "y": forecast["forecast_values"],
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Forecast (yhat)",
                },
                {
                    "x": forecast["forecast_dates"] + forecast["forecast_dates"][::-1],
                    "y": forecast["forecast_upper"] + forecast["forecast_lower"][::-1],
                    "fill": "toself",
                    "fillcolor": "rgba(245, 158, 11, 0.20)",
                    "line": {"color": "rgba(245, 158, 11, 0)"},
                    "name": "Confidence Interval",
                    "type": "scatter",
                    "hoverinfo": "skip",
                },
            ],
            "layout": {
                "title": f"Demand Forecast for {forecast['product_id'].replace('P', 'SKU-')}",
                "xaxis": {"title": "Date"},
                "yaxis": {"title": "Units Sold"},
            },
        }
    )

    return TEMPLATES.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={"request": request, "forecast": forecast, "forecast_chart": forecast_chart, "load_error": None, "selected_store_id": selected_store_id},
    )

