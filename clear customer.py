#!/usr/bin/env python3
"""
clear_customers.py
------------------
Deletes all customers and their associated orders/payments.
"""

import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',
    'database': 'restaurant_rms',
    'raise_on_warnings':True,
}

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def clear_customer_data():
    conn = get_conn()
    cur = conn.cursor()

    print("⚠️ Deleting all customers and related data...")
    cur.execute("SET FOREIGN_KEY_CHECKS=0")

    cur.execute("DELETE FROM payments")
    cur.execute("DELETE FROM order_items")
    cur.execute("DELETE FROM orders")
    cur.execute("DELETE FROM customers")

    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    cur.close()
    conn.close()

    print("✅ All customer-related data cleared successfully.")

if __name__ == "__main__":
    clear_customer_data()
