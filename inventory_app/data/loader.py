"""Data loading utilities for inventory dashboard."""

from pathlib import Path
import re
from urllib.parse import quote_plus

import pandas as pd

try:
    from sqlalchemy import create_engine
except ImportError:  # pragma: no cover
    create_engine = None

REQUIRED_COLUMNS = {
    "Date",
    "Store ID",
    "Product ID",
    "Inventory Level",
    "Units Sold",
    "Demand Forecast",
    "Price",
    "Category",
}

MYSQL_COLUMN_MAP = {
    "date": "Date",
    "store_id": "Store ID",
    "product_id": "Product ID",
    "inventory_level": "Inventory Level",
    "units_sold": "Units Sold",
    "demand_forecast": "Demand Forecast",
    "price": "Price",
    "category": "Category",
}


class InventoryDataError(Exception):
    """Base class for inventory data loading errors."""


class InventoryDataFileMissingError(InventoryDataError):
    """Raised when inventory data file is missing."""


class InventoryDataColumnsError(InventoryDataError):
    """Raised when required inventory columns are missing."""


class InventoryDataReadError(InventoryDataError):
    """Raised when data cannot be read."""


def _validate_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    missing_columns = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing_columns:
        raise InventoryDataColumnsError(
            "Inventory schema validation failed. Missing required columns: "
            f"{', '.join(missing_columns)}"
        )
    return df


def _validate_identifier(name: str, label: str) -> str:
    if not name or not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise InventoryDataReadError(
            f"Invalid {label} '{name}'. Use only letters, numbers, and underscores."
        )
    return name


def _load_from_csv(csv_path: str | Path) -> pd.DataFrame:
    path = Path(csv_path)

    if not path.exists() or not path.is_file():
        raise InventoryDataFileMissingError(
            f"Inventory CSV is missing at '{path}'. Please provide a valid CSV path."
        )

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise InventoryDataReadError(f"Unable to read inventory CSV at '{path}': {exc}") from exc

    return _validate_columns(df)


def _load_from_mysql(config) -> pd.DataFrame:
    if create_engine is None:
        raise InventoryDataReadError(
            "MySQL loading requires SQLAlchemy and PyMySQL. Install with: pip install sqlalchemy pymysql"
        )

    db_host = config.get("DB_HOST", "127.0.0.1")
    db_port = int(config.get("DB_PORT", 3306))
    db_user = config.get("DB_USER", "")
    db_password = config.get("DB_PASSWORD", "")
    db_name = _validate_identifier(config.get("DB_NAME", ""), "database name")
    db_table = _validate_identifier(config.get("DB_TABLE", "retail_inventory"), "table name")

    if not db_user:
        raise InventoryDataReadError("DB_USER is required for MySQL data source.")

    conn_url = (
        f"mysql+pymysql://{quote_plus(str(db_user))}:{quote_plus(str(db_password))}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    engine = create_engine(conn_url)

    select_fields = ", ".join(
        [f"`{src}` AS `{dst}`" for src, dst in MYSQL_COLUMN_MAP.items()]
    )
    query = f"SELECT {select_fields} FROM `{db_table}`"

    try:
        df = pd.read_sql_query(query, con=engine)
    except Exception as exc:
        raise InventoryDataReadError(
            f"Unable to read inventory rows from MySQL {db_name}.{db_table}: {exc}"
        ) from exc

    return _validate_columns(df)


def load_inventory_data(csv_path: str | Path | None = None, config=None) -> pd.DataFrame:
    """Load inventory data from configured source."""
    source = "csv"
    if config is not None:
        source = str(config.get("DATA_SOURCE", "csv")).lower()

    if source == "mysql":
        return _load_from_mysql(config)

    effective_csv_path = csv_path
    if effective_csv_path is None and config is not None:
        effective_csv_path = config.get("CSV_PATH")

    if effective_csv_path is None:
        raise InventoryDataFileMissingError("CSV path must be provided for CSV data source.")

    return _load_from_csv(effective_csv_path)


def load_data(csv_path=None):
    """Backward-compatible loader wrapper."""
    if csv_path is None:
        raise InventoryDataFileMissingError("CSV path must be provided")
    return load_inventory_data(csv_path=csv_path)
