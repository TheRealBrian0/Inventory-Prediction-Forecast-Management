"""JSON API routes designed for current Python frontend and future React clients."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from inventory_app.core.settings import get_settings
from inventory_app.data.loader import InventoryDataError
from inventory_app.dependencies.data import get_inventory_dataframe
from inventory_app.schemas.api import (
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
    ProductForecastResponse,
)
from inventory_app.services.dashboard import (
    get_all_products_forecast,
    get_dashboard_metrics,
    get_forecast_for_product,
)

api_router = APIRouter(prefix="/api/v1", tags=["api"])
legacy_api_router = APIRouter(prefix="/api", tags=["legacy-api"])


@api_router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Simple health endpoint for UI bootstrapping and liveness checks."""
    settings = get_settings()
    return HealthResponse(status="ok", app=settings.app_name, version=settings.app_version)


@api_router.get(
    "/metrics",
    response_model=MetricsResponse,
    responses={503: {"model": ErrorResponse}},
)
def get_metrics(
    store_id: str | None = Query(default=None, description="Override default store (e.g. S001)."),
    periods: int | None = Query(default=None, ge=1, le=180, description="Forecast horizon in days."),
) -> MetricsResponse:
    """Dashboard aggregates. React can call this once on page load."""
    settings = get_settings()

    try:
        df = get_inventory_dataframe(settings)
        metrics = get_dashboard_metrics(
            df,
            periods=periods or settings.forecast_periods,
            store_id=store_id or settings.default_store_id,
        )
        return MetricsResponse(**metrics)
    except InventoryDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@api_router.get(
    "/forecasts",
    response_model=list[ProductForecastResponse],
    responses={503: {"model": ErrorResponse}},
)
def get_forecasts(
    store_id: str | None = Query(default=None, description="Override default store (e.g. S001)."),
    periods: int | None = Query(default=None, ge=1, le=180, description="Forecast horizon in days."),
) -> list[ProductForecastResponse]:
    """List forecasts for all products. React list/grid views should use this endpoint."""
    settings = get_settings()

    try:
        df = get_inventory_dataframe(settings)
        forecasts = get_all_products_forecast(
            df,
            periods=periods or settings.forecast_periods,
            store_id=store_id or settings.default_store_id,
        )
        return [ProductForecastResponse(**item) for item in forecasts]
    except InventoryDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@api_router.get(
    "/forecasts/{product_id}",
    response_model=ProductForecastResponse,
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def get_product_forecast(
    product_id: str,
    store_id: str | None = Query(default=None, description="Override default store (e.g. S001)."),
    periods: int | None = Query(default=None, ge=1, le=180, description="Forecast horizon in days."),
) -> ProductForecastResponse:
    """Product-level forecast for detail pages.

    React product detail route can fetch this by `product_id` directly.
    """
    settings = get_settings()

    try:
        df = get_inventory_dataframe(settings)
        forecast = get_forecast_for_product(
            df,
            product_id=product_id,
            store_id=store_id or settings.default_store_id,
            periods=periods or settings.forecast_periods,
        )
    except InventoryDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not forecast:
        raise HTTPException(
            status_code=404,
            detail=f"No forecast found for product '{product_id}'.",
        )

    return ProductForecastResponse(**forecast)


# Backward-compatible aliases for existing consumers.
@legacy_api_router.get("/metrics", response_model=MetricsResponse, include_in_schema=False)
def legacy_metrics(
    store_id: str | None = Query(default=None),
    periods: int | None = Query(default=None, ge=1, le=180),
) -> MetricsResponse:
    return get_metrics(store_id=store_id, periods=periods)


@legacy_api_router.get("/all-forecasts", response_model=list[ProductForecastResponse], include_in_schema=False)
def legacy_all_forecasts(
    store_id: str | None = Query(default=None),
    periods: int | None = Query(default=None, ge=1, le=180),
) -> list[ProductForecastResponse]:
    return get_forecasts(store_id=store_id, periods=periods)

