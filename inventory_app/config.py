"""Application configuration defaults and environment handling."""

import os


class Config:
    """Default Flask/config settings."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'inventory-forecasting-poc-secret-key')
    CSV_PATH = os.environ.get(
        'CSV_PATH',
        'C:/Users/arvinbrian.j/Desktop/DataSet/SYSCO_POC_DB/retail_store_inventory.csv'
    )
    FORECAST_PERIODS = int(os.environ.get('FORECAST_PERIODS', 30))
    DEFAULT_STORE_ID = os.environ.get('DEFAULT_STORE_ID', 'S001')
