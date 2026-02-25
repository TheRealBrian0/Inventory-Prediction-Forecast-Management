"""Backward-compatible configuration access.

Use `inventory_app.core.settings.get_settings` for new code.
"""

from inventory_app.core.settings import get_settings


class Config:
    """Legacy config shape retained for compatibility with older imports."""

    _settings = get_settings()

    SECRET_KEY = _settings.secret_key
    DATA_SOURCE = _settings.data_source
    CSV_PATH = _settings.csv_path
    FORECAST_PERIODS = _settings.forecast_periods
    DEFAULT_STORE_ID = _settings.default_store_id
    DB_HOST = _settings.db_host
    DB_PORT = _settings.db_port
    DB_USER = _settings.db_user
    DB_PASSWORD = _settings.db_password
    DB_NAME = _settings.db_name
    DB_TABLE = _settings.db_table

