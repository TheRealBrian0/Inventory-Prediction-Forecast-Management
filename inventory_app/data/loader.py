"""Data loading utilities for inventory forecasting."""

import pandas as pd

REQUIRED_COLUMNS = {
    'Date',
    'Product ID',
    'Store ID',
    'Inventory Level',
    'Units Sold',
    'Demand Forecast',
    'Price',
    'Category',
}


def load_data(csv_path=None):
    """Load inventory data from CSV file."""
    if csv_path is None:
        raise ValueError('CSV path must be provided')

    try:
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()

        missing = REQUIRED_COLUMNS.difference(df.columns)
        if missing:
            raise ValueError(f'Missing required CSV columns: {sorted(missing)}')

        return df
    except Exception as e:
        print(f'Error loading data: {e}')
        raise ValueError(f'Failed to load data from {csv_path}: {e}')
"""Data loading utilities for inventory dashboard."""

from __future__ import annotations

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
