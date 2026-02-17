# seed_products.py

from database import get_connection
import random

PRODUCT_CATALOG = [
    ("Fresh Chicken Breast", 20, 100, 48, 500),
    ("Ground Beef 80/20", 15, 80, 72, 400),
    ("Atlantic Salmon Fillet", 10, 50, 36, 300),
    ("Whole Milk 1 Gallon", 30, 150, 24, 600),
    ("Cheddar Cheese Block", 12, 60, 72, 350),
    ("Russet Potatoes 10lb", 25, 120, 48, 700),
    ("Romaine Lettuce", 18, 90, 24, 400),
    ("Tomatoes 25lb Case", 22, 100, 48, 450),
    ("Frozen French Fries", 28, 130, 72, 800),
    ("Burger Buns Pack", 35, 160, 48, 900)
]

def seed_products():
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
        INSERT INTO products
        (sku, name, base_demand, reorder_threshold, lead_time_hours, initial_stock)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    for i, product in enumerate(PRODUCT_CATALOG):
        sku = f"SKU-{1000 + i}"
        name, base_demand, reorder_threshold, lead_time, initial_stock = product

        cursor.execute(insert_query, (
            sku,
            name,
            base_demand,
            reorder_threshold,
            lead_time,
            initial_stock
        ))

    conn.commit()
    cursor.close()
    conn.close()

    print("Products seeded successfully.")
