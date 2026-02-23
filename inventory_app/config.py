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
    CSV_PATH = os.environ.get("INVENTORY_CSV_PATH", os.environ.get("CSV_PATH", str(DEFAULT_CSV_PATH)))
    FORECAST_PERIODS = int(os.environ.get("FORECAST_PERIODS", 30))
    DEFAULT_STORE_ID = os.environ.get("DEFAULT_STORE_ID", "S001")
