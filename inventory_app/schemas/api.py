"""Pydantic schemas for API contracts.

These models make response contracts explicit so a future React client can
consume endpoints with predictable field names and types.
"""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class MetricsResponse(BaseModel):
    total_inventory: int
    total_units_sold_30d: int
    avg_daily_sales: float
    products_at_risk: int
    products_low_stock: int
    products_healthy: int
    total_products: int
    category_inventory: dict[str, int]
    latest_date: str


class ProductForecastResponse(BaseModel):
    product_id: str
    store_id: str
    current_inventory: int
    days_until_stockout: int
    days_until_stockout_display: str
    stockout_within_horizon: bool
    stockout_date: str
    recommendation: str
    avg_daily_demand: float
    max_daily_demand: float
    min_daily_demand: float
    total_forecasted_demand: float
    avg_forecasted_demand: float
    forecast_dates: list[str]
    forecast_values: list[float]
    forecast_lower: list[float]
    forecast_upper: list[float]
    historical_dates: list[str]
    historical_values: list[float]
    available_stores_categorized: dict[str, list[str]]


class ErrorResponse(BaseModel):
    detail: str

