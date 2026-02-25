"""Shared data dependencies for web and API routes."""

from __future__ import annotations

import pandas as pd

from inventory_app.core.settings import Settings
from inventory_app.data.loader import load_inventory_data
from inventory_app.data.preprocess import preprocess_data


def get_inventory_dataframe(settings: Settings) -> pd.DataFrame:
    """Load and preprocess inventory data once per request."""
    config = {
        "DATA_SOURCE": settings.data_source,
        "CSV_PATH": settings.csv_path,
        "DB_HOST": settings.db_host,
        "DB_PORT": settings.db_port,
        "DB_USER": settings.db_user,
        "DB_PASSWORD": settings.db_password,
        "DB_NAME": settings.db_name,
        "DB_TABLE": settings.db_table,
    }
    df = load_inventory_data(config=config)
    return preprocess_data(df)

