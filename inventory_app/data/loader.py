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
