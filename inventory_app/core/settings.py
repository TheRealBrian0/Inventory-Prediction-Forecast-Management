"""Application settings and environment loading for FastAPI."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "retail_store_inventory.csv"

# Root env file stays the single source of truth for local configuration.
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    secret_key: str
    data_source: str
    csv_path: str
    forecast_periods: int
    default_store_id: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_table: str
    host: str
    port: int
    cors_origins: list[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    cors_raw = os.environ.get("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in cors_raw.split(",") if origin.strip()]

    return Settings(
        app_name=os.environ.get("APP_NAME", "Inventory Forecast Management API"),
        app_version=os.environ.get("APP_VERSION", "2.0.0"),
        secret_key=os.environ.get("SECRET_KEY", "inventory-forecasting-poc-secret-key"),
        data_source=os.environ.get("DATA_SOURCE", "csv").lower(),
        csv_path=os.environ.get("INVENTORY_CSV_PATH", os.environ.get("CSV_PATH", str(DEFAULT_CSV_PATH))),
        forecast_periods=int(os.environ.get("FORECAST_PERIODS", 30)),
        default_store_id=os.environ.get("DEFAULT_STORE_ID", "S001"),
        db_host=os.environ.get("DB_HOST", "127.0.0.1"),
        db_port=int(os.environ.get("DB_PORT", 3306)),
        db_user=os.environ.get("DB_USER", ""),
        db_password=os.environ.get("DB_PASSWORD", ""),
        db_name=os.environ.get("DB_NAME", ""),
        db_table=os.environ.get("DB_TABLE", "retail_inventory"),
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 8000)),
        cors_origins=origins if origins else ["*"],
    )

