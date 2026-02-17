# demand.py

import numpy as np
from datetime import datetime

from config import SIMULATION_CONFIG

def calculate_demand(product, current_time):
    base = product["base_demand"]

    # Hourly seasonality (daily cycle)
    hour = current_time.hour
    seasonal_factor = 1 + SIMULATION_CONFIG["seasonality_amplitude"] * np.sin(2 * np.pi * hour / 24)

    # Weekend boost
    weekend_factor = 1
    if current_time.weekday() >= 5:
        weekend_factor = SIMULATION_CONFIG["weekend_multiplier"]

    # Random noise
    noise = np.random.normal(1, SIMULATION_CONFIG["noise_level"])

    demand = base * seasonal_factor * weekend_factor * noise

    return max(0, int(round(demand)))
