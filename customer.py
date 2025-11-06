#!/usr/bin/env python3
"""
customer_kfc.py (Enhanced)
--------------------------
Customer-facing KFC-style ordering system with:
- Add/remove/view items
- Live subtotal
- Full upfront payment (no split)
- Input validation (safe and robust)
"""

import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
import sys

# ---------- Database Config ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',
    'database': 'restaurant_rms',
    'raise_on_warnings': True,
}

TAX_RATE = Decimal('0.05')  # 5% GST

# ---------- Utilities ----------
def fm(v):
    """Format decimal as money"""
    if v is None:
        v = Decimal('0.00')
    return f"{Decimal(v).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"

def get_conn():
    """Create MySQL connection"""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print("❌ Database connection error:", err)
        sys.exit(1)

# ---------- DB Helper Functions ----------
def get_menu(conn):
    """Fetch all available dishes grouped by category"""
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT c.name AS category, m.id, m.name, m.price
        FROM menu_items m
        LEFT JOIN categories c ON c.id = m.category_id
        WHERE m.is_available = 1
        ORDER BY c.name, m.name
    """)
    data = {}
    for r in cur.fetchall():
        cat = r['category'] or 'Uncategorized'
        data.setdefault(cat, []).append(r)
    cur.close()
    return data

def create_customer(conn, name):
    cur = conn.cursor()
    cur.execute("INSERT INTO customers (name) VALUES (%s)", (name,))
    conn.commit()
    cid = cur.lastrowid
    cur.close()
    return cid

def create_order(conn, customer_id):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (order_type, status, customer_id)
        VALUES ('takeaway', 'open', %s)
    """, (customer_id,))
    conn.commit()
    oid = cur.lastrowid
    cur.close()
    return oid

def add_order_item(conn, order_id, menu_id, qty):
    """Add dish to order"""
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT name, price FROM menu_items WHERE id=%s AND is_available=1", (menu_id,))
    r = cur.fetchone()
    if not r:
        print("❌ Invalid item ID or unavailable.")
        cur.close()
        return
    price = Decimal(r['price'])
    line_total = price * qty
    cur.close()

    cur2 = conn.cursor()
    cur2.execute("""
        INSERT INTO order_items (order_id, menu_item_id, qty, unit_price, line_total)
        VALUES (%s,%s,%s,%s,%s)
    """, (order_id, menu_id, qty, price, line_total))
    conn.commit()
    cur2.close()
    print(f"✅ Added {qty} × {r['name']} (₹{fm(price)} each).")

def view_cart(conn, order_id):
    """Show items in cart with subtotal"""
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT oi.id, m.name, oi.qty, oi.unit_price, oi.line_total
        FROM order_items oi
        JOIN menu_items m ON m.id=oi.menu_item_id
        WHERE oi.order_id=%s
    """, (order_id,))
    rows = cur.fetchall()
    cur.close()
    if not rows:
        print("\n🛒 Your cart is empty.")
        return Decimal('0.00')

    subtotal = Decimal('0.00')
    print("\n🧾 Current Cart:")
    for r in rows:
        subtotal += Decimal(r['line_total'])
        print(f"[{r['id']}] {r['name']} × {r['qty']} = ₹{fm(r['line_total'])}")
    print("Subtotal: ₹", fm(subtotal))
    return subtotal

def remove_item(conn, order_id):
    """Remove one item from cart"""
    subtotal = view_cart(conn, order_id)
    if subtotal == 0:
        return
    rid = input("Enter the ID of the item to remove (or blank to cancel): ").strip()
    if not rid:
        return
    if not rid.isdigit():
        print("⚠️ Invalid ID.")
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM order_items WHERE id=%s AND order_id=%s", (rid, order_id))
    conn.commit()
    if cur.rowcount > 0:
        print("🗑️ Item removed successfully.")
    else:
        print("⚠️ No such item found in your order.")
    cur.close()

def deduct_ingredients(conn, order_id):
    """Deduct stock based on recipe quantities"""
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT rec.ingredient_id, SUM(rec.qty_needed * oi.qty) AS needed, i.stock, i.name, i.unit
        FROM order_items oi
        JOIN recipe rec ON rec.menu_item_id = oi.menu_item_id
        JOIN ingredients i ON i.id = rec.ingredient_id
        WHERE oi.order_id=%s
        GROUP BY rec.ingredient_id
    """, (order_id,))
    reqs = cur.fetchall()
    cur.close()

    insufficient = []
    for r in reqs:
        if Decimal(r['stock']) < Decimal(r['needed']):
            insufficient.append(f"{r['name']} (need {fm(r['needed'])}{r['unit']}, have {fm(r['stock'])}{r['unit']})")

    if insufficient:
        return False, "\n⚠️ Insufficient stock:\n" + "\n".join(insufficient)

    cur2 = conn.cursor()
    for r in reqs:
        cur2.execute("UPDATE ingredients SET stock = stock - %s WHERE id=%s", (r['needed'], r['ingredient_id']))
    conn.commit()
    cur2.close()
    return True, None

def finalize_order(conn, order_id, subtotal):
    """Close the order and handle payment"""
    tax = (subtotal * TAX_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total = subtotal + tax

    ok, msg = deduct_ingredients(conn, order_id)
    if not ok:
        print(msg)
        return

    cur = conn.cursor()
    cur.execute("""
        UPDATE orders
        SET subtotal=%s, tax=%s, total=%s, status='closed', closed_at=NOW()
        WHERE id=%s
    """, (subtotal, tax, total, order_id))
    conn.commit()
    cur.close()

    print(f"\n✅ Final Bill — Subtotal ₹{fm(subtotal)} | Tax ₹{fm(tax)} | Total ₹{fm(total)}")
    amt = input(f"💳 Pay ₹{fm(total)} now (press Enter to confirm): ").strip()
    if amt == "":
        amt = total
    else:
        try:
            amt = Decimal(amt)
        except:
            print("⚠️ Invalid input. Assuming full payment.")
            amt = total

    cur2 = conn.cursor()
    cur2.execute("INSERT INTO payments (order_id, amount, method) VALUES (%s,%s,'cash')", (order_id, amt))
    conn.commit()
    cur2.close()
    print("\n🎉 Payment received! Order completed successfully.")

# ---------- Main Flow ----------
def main():
    conn = get_conn()
    print("\n🍗 Welcome to KFC Self-Order Kiosk 🍟")

    name = input("Enter your name: ").strip() or "Guest"
    cust_id = create_customer(conn, name)
    order_id = create_order(conn, cust_id)

    while True:
        menu = get_menu(conn)  # refreshed every time
        print("\n==============================")
        print("📋 Menu Options:")
        print("1) View Menu & Add Items")
        print("2) View Cart / Subtotal")
        print("3) Remove Item")
        print("4) Checkout & Pay")
        print("0) Cancel Order & Exit")
        print("==============================")
        choice = input("Choose: ").strip()

        if choice == "1":
            cats = list(menu.keys())
            for i, c in enumerate(cats, 1):
                print(f"{i}) {c}")
            ch = input("Select category (or blank to skip): ").strip()
            if not ch:
                continue
            if not ch.isdigit() or int(ch) not in range(1, len(cats)+1):
                print("⚠️ Invalid category choice.")
                continue

            cat = cats[int(ch)-1]
            items = menu[cat]
            valid_ids = [it['id'] for it in items]

            print(f"\n🍴 {cat} Menu:")
            for it in items:
                print(f"[{it['id']}] {it['name']} - ₹{fm(it['price'])}")
            print("0) Back")

            while True:
                mid = input("Enter item ID to add (or 0 to go back): ").strip()
                if mid == "0" or mid == "":
                    break
                if not mid.isdigit():
                    print("⚠️ Invalid ID — must be a number.")
                    continue

                mid = int(mid)
                if mid not in valid_ids:
                    print("❌ That item does not belong to this category or is unavailable.")
                    continue

                qty_in = input("Quantity: ").strip()
                if not qty_in.isdigit():
                    print("⚠️ Invalid quantity — must be a number.")
                    continue

                qty = int(qty_in)
                if qty <= 0:
                    print("⚠️ Quantity must be at least 1.")
                    continue

                add_order_item(conn, order_id, mid, qty)

        elif choice == "2":
            view_cart(conn, order_id)

        elif choice == "3":
            remove_item(conn, order_id)

        elif choice == "4":
            subtotal = view_cart(conn, order_id)
            if subtotal == 0:
                print("Your cart is empty.")
                continue
            finalize_order(conn, order_id, subtotal)
            break

        elif choice == "0":
            print("Order cancelled. Come again soon!")
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status='cancelled' WHERE id=%s", (order_id,))
            conn.commit()
            cur.close()
            break

        else:
            print("⚠️ Invalid option. Try again.")

    conn.close()
    print("\n👋 Thank you for dining with us!")

if __name__ == "__main__":
    main()
