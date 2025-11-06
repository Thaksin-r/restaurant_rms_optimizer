#!/usr/bin/env python3
"""
feed_shopkeeper.py
------------------
Populate the restaurant_rms database with realistic data:
categories, ingredients, menu_items, recipes, restaurant_tables.
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

def seed_shopkeeper():
    conn = get_conn()
    cur = conn.cursor()
    print("🌱 Seeding full restaurant data...")

    # -------- Categories --------
    categories = [
        'Starters', 'Main Course', 'Beverages', 'Desserts',
        'Snacks', 'Biriyani', 'South Indian', 'Chinese'
    ]
    for c in categories:
        cur.execute("INSERT IGNORE INTO categories (name) VALUES (%s)", (c,))
    conn.commit()

    # -------- Ingredients --------
    ingredients = [
        ('Rice', 'kg', 60, 10, 40.00),
        ('Chicken', 'kg', 40, 5, 180.00),
        ('Mutton', 'kg', 20, 3, 420.00),
        ('Fish', 'kg', 25, 4, 250.00),
        ('Prawns', 'kg', 15, 3, 480.00),
        ('Egg', 'pcs', 200, 20, 6.00),
        ('Oil', 'ltr', 25, 5, 110.00),
        ('Ghee', 'kg', 5, 1, 600.00),
        ('Tomato', 'kg', 40, 8, 30.00),
        ('Onion', 'kg', 50, 10, 25.00),
        ('Chilli Powder', 'kg', 8, 2, 260.00),
        ('Salt', 'kg', 15, 2, 20.00),
        ('Pepper', 'kg', 5, 1, 600.00),
        ('Garam Masala', 'kg', 3, 1, 800.00),
        ('Coriander', 'kg', 4, 1, 150.00),
        ('Flour', 'kg', 40, 5, 60.00),
        ('Butter', 'kg', 6, 1, 500.00),
        ('Cheese', 'kg', 10, 2, 450.00),
        ('Paneer', 'kg', 12, 3, 360.00),
        ('Milk', 'ltr', 20, 5, 45.00),
        ('Sugar', 'kg', 25, 5, 50.00),
        ('Ice Cream Mix', 'kg', 5, 1, 400.00),
        ('Coke Syrup', 'ltr', 8, 2, 90.00),
        ('Coffee Powder', 'kg', 6, 1, 700.00),
        ('Tea Leaves', 'kg', 5, 1, 500.00)
    ]
    cur.executemany("""
        INSERT IGNORE INTO ingredients (name, unit, stock, min_required, cost_price)
        VALUES (%s,%s,%s,%s,%s)
    """, ingredients)
    conn.commit()

    # -------- Menu Items --------
    menu_items = [
        # Starters
        ('Starters', 'Chicken 65', 160.00, 80.00),
        ('Starters', 'Paneer Tikka', 140.00, 70.00),
        ('Starters', 'Gobi Manchurian', 120.00, 60.00),
        ('Starters', 'French Fries', 90.00, 40.00),
        ('Starters', 'Egg Pakoda', 110.00, 50.00),
        # Main Course
        ('Main Course', 'Chicken Curry', 180.00, 90.00),
        ('Main Course', 'Mutton Curry', 240.00, 130.00),
        ('Main Course', 'Paneer Butter Masala', 200.00, 100.00),
        ('Main Course', 'Dal Tadka', 130.00, 60.00),
        ('Main Course', 'Fish Curry', 220.00, 120.00),
        # Biriyani
        ('Biriyani', 'Chicken Biriyani', 220.00, 110.00),
        ('Biriyani', 'Mutton Biriyani', 280.00, 160.00),
        ('Biriyani', 'Egg Biriyani', 160.00, 80.00),
        ('Biriyani', 'Prawn Biriyani', 260.00, 150.00),
        # South Indian
        ('South Indian', 'Idli (2 pcs)', 40.00, 15.00),
        ('South Indian', 'Dosa', 50.00, 20.00),
        ('South Indian', 'Pongal', 70.00, 30.00),
        # Chinese
        ('Chinese', 'Veg Fried Rice', 120.00, 50.00),
        ('Chinese', 'Chicken Fried Rice', 140.00, 70.00),
        ('Chinese', 'Schezwan Noodles', 130.00, 60.00),
        # Beverages
        ('Beverages', 'Coca-Cola', 50.00, 15.00),
        ('Beverages', 'Lemon Juice', 40.00, 10.00),
        ('Beverages', 'Cold Coffee', 90.00, 30.00),
        ('Beverages', 'Tea', 25.00, 5.00),
        ('Beverages', 'Filter Coffee', 30.00, 10.00),
        # Desserts
        ('Desserts', 'Vanilla Ice Cream', 60.00, 25.00),
        ('Desserts', 'Chocolate Ice Cream', 70.00, 30.00),
        ('Desserts', 'Gulab Jamun', 80.00, 35.00)
    ]

    for cat, name, price, cost in menu_items:
        cur.execute("""
            INSERT IGNORE INTO menu_items (category_id, name, price, cost_price)
            VALUES ((SELECT id FROM categories WHERE name=%s), %s, %s, %s)
        """, (cat, name, price, cost))
    conn.commit()

    # -------- Recipes --------
    recipes = [
        ('Chicken 65', ['Chicken', 'Oil', 'Chilli Powder', 'Salt']),
        ('Paneer Tikka', ['Paneer', 'Chilli Powder', 'Garam Masala', 'Oil']),
        ('Gobi Manchurian', ['Flour', 'Oil', 'Salt', 'Tomato']),
        ('French Fries', ['Oil', 'Salt']),
        ('Egg Pakoda', ['Egg', 'Flour', 'Oil']),
        ('Chicken Curry', ['Chicken', 'Onion', 'Tomato', 'Oil', 'Chilli Powder']),
        ('Mutton Curry', ['Mutton', 'Onion', 'Tomato', 'Garam Masala', 'Oil']),
        ('Paneer Butter Masala', ['Paneer', 'Butter', 'Tomato', 'Garam Masala']),
        ('Dal Tadka', ['Oil', 'Onion', 'Tomato', 'Salt']),
        ('Fish Curry', ['Fish', 'Onion', 'Tomato', 'Oil', 'Coriander']),
        ('Chicken Biriyani', ['Rice', 'Chicken', 'Onion', 'Tomato', 'Ghee']),
        ('Mutton Biriyani', ['Rice', 'Mutton', 'Onion', 'Ghee']),
        ('Egg Biriyani', ['Rice', 'Egg', 'Ghee']),
        ('Prawn Biriyani', ['Rice', 'Prawns', 'Onion', 'Tomato', 'Oil']),
        ('Idli (2 pcs)', ['Rice', 'Salt']),
        ('Dosa', ['Rice', 'Oil']),
        ('Pongal', ['Rice', 'Ghee', 'Pepper', 'Salt']),
        ('Veg Fried Rice', ['Rice', 'Oil', 'Salt']),
        ('Chicken Fried Rice', ['Rice', 'Chicken', 'Oil']),
        ('Schezwan Noodles', ['Flour', 'Oil', 'Chilli Powder', 'Salt']),
        ('Coca-Cola', ['Coke Syrup']),
        ('Lemon Juice', ['Sugar']),
        ('Cold Coffee', ['Milk', 'Coffee Powder', 'Sugar']),
        ('Tea', ['Milk', 'Tea Leaves', 'Sugar']),
        ('Filter Coffee', ['Milk', 'Coffee Powder', 'Sugar']),
        ('Vanilla Ice Cream', ['Milk', 'Ice Cream Mix']),
        ('Chocolate Ice Cream', ['Milk', 'Ice Cream Mix', 'Sugar']),
        ('Gulab Jamun', ['Flour', 'Sugar', 'Ghee'])
    ]

    for dish, ing_list in recipes:
        for ing in ing_list:
            cur.execute("""
                INSERT IGNORE INTO recipe (menu_item_id, ingredient_id, qty_needed)
                SELECT m.id, i.id, 0.1
                FROM menu_items m, ingredients i
                WHERE m.name=%s AND i.name=%s
            """, (dish, ing))
    conn.commit()

    # -------- Tables --------
    tables = [('T1', 4), ('T2', 2), ('T3', 6), ('T4', 4), ('T5', 2), ('T6', 8), ('T7', 6), ('T8', 4)]
    cur.executemany("INSERT IGNORE INTO restaurant_tables (name, seats) VALUES (%s,%s)", tables)
    conn.commit()

    cur.close()
    conn.close()
    print("✅ Full shopkeeper data seeded successfully with 25+ dishes and 25 ingredients.")

if __name__ == "__main__":
    seed_shopkeeper()
