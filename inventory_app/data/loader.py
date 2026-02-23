"""Data loading utilities for inventory dashboard."""

from pathlib import Path

import pandas as pd

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


class InventoryDataError(Exception):
    """Base class for inventory data loading errors."""


class InventoryDataFileMissingError(InventoryDataError):
    """Raised when inventory data file is missing."""


class InventoryDataColumnsError(InventoryDataError):
    """Raised when required inventory columns are missing."""


class InventoryDataReadError(InventoryDataError):
    """Raised when the CSV cannot be read."""


def load_inventory_data(csv_path: str | Path) -> pd.DataFrame:
    """Load and validate inventory CSV."""
    path = Path(csv_path)

    if not path.exists() or not path.is_file():
        raise InventoryDataFileMissingError(
            f"Inventory CSV is missing at '{path}'. Please provide a valid CSV path."
        )

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        raise InventoryDataReadError(
            f"Unable to read inventory CSV at '{path}': {exc}"
        ) from exc

    df.columns = df.columns.str.strip()
    missing_columns = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing_columns:
        raise InventoryDataColumnsError(
            "Inventory CSV schema validation failed. Missing required columns: "
            f"{', '.join(missing_columns)}"
        )

    return df


def load_data(csv_path=None):
    """Backward-compatible loader wrapper."""
    if csv_path is None:
        raise InventoryDataFileMissingError("CSV path must be provided")
    return load_inventory_data(csv_path)
