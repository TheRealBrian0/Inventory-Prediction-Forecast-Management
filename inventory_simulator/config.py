# config.py

import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # change if needed
    "password": "root",
    "database": "syscodb"
}

SIMULATION_CONFIG = {
    "num_products": 25,
    "start_date": "2024-01-01 00:00:00",
    "months_backfill": 6,
    "weekend_multiplier": 1.3,
    "seasonality_amplitude": 0.2,
    "noise_level": 0.1,
    "restock_multiplier": 2
}
