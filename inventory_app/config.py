"""Application configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "retail_store_inventory.csv"


class CsvPathResolutionError(RuntimeError):
    """Raised when the inventory CSV path cannot be resolved."""


def resolve_csv_path() -> Path:
    """Resolve CSV path from env var then project default.

    Resolution order:
    1. INVENTORY_CSV_PATH environment variable
    2. project-relative default data/retail_store_inventory.csv
    3. explicit startup error if missing
    """
    env_path = os.getenv("INVENTORY_CSV_PATH")
    candidate = Path(env_path).expanduser() if env_path else DEFAULT_CSV_PATH

    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate

    if candidate.exists() and candidate.is_file():
        return candidate

    resolution_source = (
        f"INVENTORY_CSV_PATH={env_path!r}" if env_path else f"default={DEFAULT_CSV_PATH}"
    )
    raise CsvPathResolutionError(
        "Inventory CSV file not found. "
        f"Checked {candidate} via {resolution_source}. "
        "Set INVENTORY_CSV_PATH to a valid CSV file path or add data/retail_store_inventory.csv."
    )
