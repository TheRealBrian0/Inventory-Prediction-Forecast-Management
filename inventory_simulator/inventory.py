# inventory.py

from datetime import timedelta
from database import insert_restock_event
from config import SIMULATION_CONFIG

def process_inventory(product, current_stock, demand, current_time):
    new_stock = current_stock - demand

    restock_triggered = False

    if new_stock <= product["reorder_threshold"]:
        quantity = int(product["base_demand"] * SIMULATION_CONFIG["restock_multiplier"])
        expected_arrival = current_time + timedelta(hours=product["lead_time_hours"])

        insert_restock_event(product["id"], quantity, expected_arrival)
        restock_triggered = True

    return max(0, new_stock), restock_triggered
