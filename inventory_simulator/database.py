# database.py

import mysql.connector
from config import DB_CONFIG

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def insert_sale(product_id, quantity, timestamp):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO sales (product_id, quantity_sold, sale_timestamp)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (product_id, quantity, timestamp))
    conn.commit()

    cursor.close()
    conn.close()

def fetch_pending_restocks(current_time):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT * FROM restock_events
        WHERE status = 'pending'
        AND expected_arrival <= %s
    """

    cursor.execute(query, (current_time,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results


def mark_restock_completed(restock_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        UPDATE restock_events
        SET status = 'completed'
        WHERE id = %s
    """

    cursor.execute(query, (restock_id,))
    conn.commit()

    cursor.close()
    conn.close()


def insert_inventory_level(product_id, stock, timestamp):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO inventory_levels (product_id, stock_level, recorded_at)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (product_id, stock, timestamp))
    conn.commit()

    cursor.close()
    conn.close()

def insert_restock_event(product_id, quantity, expected_arrival):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO restock_events (product_id, quantity_added, expected_arrival)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (product_id, quantity, expected_arrival))
    conn.commit()

    cursor.close()
    conn.close()

def fetch_products():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return products
