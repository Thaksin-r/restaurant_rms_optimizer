#!/usr/bin/env python3
"""
reset_shopkeeper_data.py
------------------------
Safely clears all shopkeeper-related tables:
categories, ingredients, recipe, menu_items, restaurant_tables
"""

import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',
    'database': 'restaurant_rms',
    'raise_on_warnings':True,
}

def clear_shopkeeper_tables():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("⚠️ This will DELETE all shopkeeper-related data (menu, ingredients, recipes, tables).")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("❌ Cancelled.")
        conn.close()
        return

    tables = ["recipe", "menu_items", "ingredients", "categories", "restaurant_tables"]

    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    for t in tables:
        cur.execute(f"TRUNCATE TABLE {t}")
        print(f"✅ Cleared table: {t}")
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()

    cur.close()
    conn.close()
    print("🎉 All shopkeeper tables cleared successfully.")

if __name__ == "__main__":
    clear_shopkeeper_tables()
