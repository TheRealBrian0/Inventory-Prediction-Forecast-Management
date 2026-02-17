# backfill.py

from datetime import datetime, timedelta
from database import fetch_products, insert_sale, insert_inventory_level
from demand import calculate_demand
from inventory import process_inventory
from config import SIMULATION_CONFIG
from database import fetch_pending_restocks, mark_restock_completed


def run_backfill():
    products = fetch_products()

    start = datetime.strptime(SIMULATION_CONFIG["start_date"], "%Y-%m-%d %H:%M:%S")
    hours = SIMULATION_CONFIG["months_backfill"] * 30 * 24

    inventory_map = {p["id"]: p["initial_stock"] for p in products}

    current_time = start

    for _ in range(hours):
        # Apply arrived restocks
        arrived_restocks = fetch_pending_restocks(current_time)

        for restock in arrived_restocks:
            product_id = restock["product_id"]
            quantity = restock["quantity_added"]

            inventory_map[product_id] += quantity
            mark_restock_completed(restock["id"])

        for product in products:
            demand = calculate_demand(product, current_time)
            stock = inventory_map[product["id"]]

            new_stock, _ = process_inventory(product, stock, demand, current_time)

            insert_sale(product["id"], demand, current_time)
            insert_inventory_level(product["id"], new_stock, current_time)

            inventory_map[product["id"]] = new_stock

        current_time += timedelta(hours=1)

    print("Backfill completed.")
