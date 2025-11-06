#!/usr/bin/env python3
"""
feed_customers_full.py
----------------------
Creates 25+ customers with random orders, items, and payments (down_payment).
"""

import mysql.connector
import random
from decimal import Decimal, ROUND_HALF_UP

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',
    'database': 'restaurant_rms',
    'raise_on_warnings':True,
}


TAX_RATE = Decimal("0.05")  # 5% GST

def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def fm(value):
    return f"{Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"

def seed_customers_with_orders():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    print("🌱 Creating sample customers with random orders...")

    # Step 1️⃣ Create sample customers
    names = [
        "Selva Kumar", "Aarthi", "Naveen", "Surya", "Deepika", "Kavya", "Sanjay",
        "Harish", "Bharathi", "Karthik", "Vijay", "Meena", "Tharun", "Anand",
        "Ramya", "Prakash", "Anjali", "Ramesh", "Rohit", "Swetha", "Manoj",
        "Priya", "Dinesh", "Divya", "Saranya", "Vimal", "Latha", "Aravind",
        "Harini", "Abishek"
    ]

    cur.executemany("INSERT IGNORE INTO customers (name) VALUES (%s)", [(n,) for n in names])
    conn.commit()

    # Step 2️⃣ Get all menu items
    cur.execute("SELECT id, name, price FROM menu_items WHERE is_available=1")
    menu = cur.fetchall()
    if not menu:
        print("❌ No menu items found! Run feed_shopkeeper.py first.")
        conn.close()
        return

    # Step 3️⃣ Get each customer's ID
    cur.execute("SELECT id, name FROM customers")
    customer_rows = cur.fetchall()
    customers = {r['name']: r['id'] for r in customer_rows}

    # Step 4️⃣ Generate random orders
    order_count = 0
    item_count = 0

    for cust_name, cust_id in customers.items():
        # Each customer makes 1–2 orders
        for _ in range(random.randint(1, 2)):
            selected_items = random.sample(menu, k=random.randint(2, 4))
            subtotal = Decimal('0.00')

            # Create new order
            cur.execute("""
                INSERT INTO orders (order_type, status, subtotal, tax, total, customer_id)
                VALUES ('dine-in', 'open', 0, 0, 0, %s)
            """, (cust_id,))
            order_id = cur.lastrowid

            # Add order items
            for item in selected_items:
                qty = random.randint(1, 3)
                price = Decimal(item['price'])
                line_total = qty * price
                subtotal += line_total
                cur.execute("""
                    INSERT INTO order_items (order_id, menu_item_id, qty, unit_price, line_total)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_id, item['id'], qty, price, line_total))
                item_count += 1

            # Compute totals
            tax = (subtotal * TAX_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total = subtotal + tax

            # Update order totals
            cur.execute("""
                UPDATE orders
                SET subtotal=%s, tax=%s, total=%s, status='closed', closed_at=NOW()
                WHERE id=%s
            """, (subtotal, tax, total, order_id))

            # Insert payment (simple down_payment)
            cur.execute("""
                INSERT INTO payments (order_id, amount, method)
                VALUES (%s, %s, 'down_payment')
            """, (order_id, total))

            conn.commit()
            order_count += 1

    cur.close()
    conn.close()

    print(f"✅ Created {len(customers)} customers, {order_count} orders, {item_count} order_items.")

if __name__ == "__main__":
    seed_customers_with_orders()
