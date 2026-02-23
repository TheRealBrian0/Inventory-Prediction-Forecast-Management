"""Application configuration defaults and path helpers."""

from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "retail_store_inventory.csv"

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Default Flask/config settings."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "inventory-forecasting-poc-secret-key")
    DATA_SOURCE = os.environ.get("DATA_SOURCE", "csv").lower()
    CSV_PATH = os.environ.get("INVENTORY_CSV_PATH", os.environ.get("CSV_PATH", str(DEFAULT_CSV_PATH)))
    FORECAST_PERIODS = int(os.environ.get("FORECAST_PERIODS", 30))
    DEFAULT_STORE_ID = os.environ.get("DEFAULT_STORE_ID", "S001")
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER", "")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "")
    DB_TABLE = os.environ.get("DB_TABLE", "retail_inventory")
