#!/usr/bin/env python3
"""
feed_customers_full.py
----------------------
Creates 25–30 random customers, orders, and payments.
Updates menu_stats safely (MySQL 8.0+ compatible).
"""

import mysql.connector
import random
from decimal import Decimal, ROUND_HALF_UP

# ==============================
# Database Configuration
# ==============================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',  # change if needed
    'database': 'restaurant_rms',
    'raise_on_warnings': True
}

TAX_RATE = Decimal("0.05")  # 5% GST

# ==============================
# Helpers
# ==============================
def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def fm(value):
    return f"{Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"

# ==============================
# Main Seeder Function
# ==============================
def seed_customers_with_orders():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    print("🌱 Populating sample customers, orders, and payments...")

    # 1️⃣ Create sample customers
    names = [
        "Selva Kumar", "Aarthi", "Naveen", "Surya", "Deepika", "Kavya", "Sanjay",
        "Harish", "Bharathi", "Karthik", "Vijay", "Meena", "Tharun", "Anand",
        "Ramya", "Prakash", "Anjali", "Ramesh", "Rohit", "Swetha", "Manoj",
        "Priya", "Dinesh", "Divya", "Saranya", "Vimal", "Latha", "Aravind",
        "Harini", "Abishek"
    ]
    cur.executemany("INSERT IGNORE INTO customers (name) VALUES (%s)", [(n,) for n in names])
    conn.commit()

    # 2️⃣ Fetch available menu items
    cur.execute("SELECT id, name, price FROM menu_items WHERE is_available=1")
    menu = cur.fetchall()
    if not menu:
        print("❌ No menu items found! Please run shopkeeper feed first.")
        conn.close()
        return

    # 3️⃣ Get customers
    cur.execute("SELECT id, name FROM customers")
    customers = {r['name']: r['id'] for r in cur.fetchall()}

    order_count = 0
    item_count = 0

    # 4️⃣ Generate random orders
    for cust_name, cust_id in customers.items():
        for _ in range(random.randint(1, 2)):  # each customer orders 1–2 times
            selected_items = random.sample(menu, k=random.randint(2, 4))
            subtotal = Decimal('0.00')

            # Create new order
            cur.execute("""
                INSERT INTO orders (order_type, status, subtotal, tax, total, customer_id)
                VALUES ('dine-in', 'open', 0, 0, 0, %s)
            """, (cust_id,))
            order_id = cur.lastrowid

            # Add items
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

            # Finalize order
            cur.execute("""
                UPDATE orders
                SET subtotal=%s, tax=%s, total=%s, status='closed', closed_at=NOW()
                WHERE id=%s
            """, (subtotal, tax, total, order_id))

            # Record payment
            cur.execute("""
                INSERT INTO payments (order_id, amount, method)
                VALUES (%s, %s, 'down_payment')
            """, (order_id, total))

            conn.commit()
            order_count += 1

    # 5️⃣ Update menu_stats (MySQL 8.0 safe, DATE fix)
    print("📈 Updating menu_stats table...")
    cur.execute("""
        INSERT INTO menu_stats (menu_item_id, orders_sold, last_ordered)
        SELECT s.menu_item_id, s.total_sold, s.last_ordered
        FROM (
            SELECT 
                m.id AS menu_item_id,
                IFNULL(SUM(oi.qty), 0) AS total_sold,
                DATE(MAX(o.created_at)) AS last_ordered
            FROM menu_items m
            LEFT JOIN order_items oi ON oi.menu_item_id = m.id
            LEFT JOIN orders o ON o.id = oi.order_id
            GROUP BY m.id
        ) AS s
        ON DUPLICATE KEY UPDATE
            orders_sold = s.total_sold,
            last_ordered = s.last_ordered;
    """)
    conn.commit()

    # 6️⃣ Show top 5 updated stats
    cur.execute("""
        SELECT ms.menu_item_id, mi.name, ms.orders_sold
        FROM menu_stats ms
        JOIN menu_items mi ON mi.id = ms.menu_item_id
        ORDER BY ms.orders_sold DESC
        LIMIT 5
    """)
    print("\n🔥 Top 5 Selling Dishes (After Update):")
    for row in cur.fetchall():
        print(f"• {row['name']} — {row['orders_sold']} orders")

    # Done
    cur.close()
    conn.close()

    print(f"\n✅ Added {len(customers)} customers, {order_count} orders, {item_count} order_items.")
    print("📊 menu_stats refreshed successfully for analytics (LIS & Pareto ready).")

# ==============================
# Run
# ==============================
if __name__ == "__main__":
    seed_customers_with_orders()
