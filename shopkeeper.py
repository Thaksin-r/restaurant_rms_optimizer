#!/usr/bin/env python3
"""
Restaurant RMS - Shopkeeper Management
--------------------------------------
Modules:
1. Category Management
2. Menu Management
3. Inventory (Ingredients)
4. Recipe Mapping (Dish → Ingredients)
5. Table Management
"""

import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
import sys

# ---------- MySQL Configuration ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',
    'database': 'restaurant_rms',
    'raise_on_warnings':True,
}

# ---------- Utility Functions ----------
def get_conn():
    """Establish database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print("❌ Database connection failed:", err)
        sys.exit(1)

def fm(value):
    """Format Decimal as money (₹x.xx)."""
    if value is None:
        return "0.00"
    return f"{Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"

def read_decimal(prompt):
    """Read decimal input safely."""
    val = input(prompt).strip()
    try:
        return Decimal(val) if val else Decimal('0')
    except:
        return Decimal('0')

def read_int(prompt):
    """Read integer safely."""
    val = input(prompt).strip()
    try:
        return int(val) if val else 0
    except:
        return 0

# =========================================================
# CATEGORY MANAGEMENT
# =========================================================
def list_categories(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name, description FROM categories ORDER BY name")
    rows = cur.fetchall()
    if not rows:
        print("No categories found.")
    else:
        print("\nCATEGORIES:")
        for r in rows:
            print(f"[{r['id']}] {r['name']} - {r['description'] or ''}")
    cur.close()

def add_category(conn):
    name = input("Category name: ").strip()
    if not name:
        print("⚠️ Category name cannot be blank.")
        return
    desc = input("Description (optional): ").strip() or None
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO categories (name, description) VALUES (%s, %s)", (name, desc))
        conn.commit()
        print("✅ Category added.")
    except mysql.connector.IntegrityError:
        print("⚠️ Category already exists.")
    cur.close()

# =========================================================
# MENU MANAGEMENT
# =========================================================
def list_menu(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT m.id, m.name, m.price, m.is_available, c.name AS category
        FROM menu_items m
        LEFT JOIN categories c ON c.id = m.category_id
        ORDER BY c.name, m.name
    """)
    rows = cur.fetchall()
    if not rows:
        print("No menu items yet.")
    else:
        print("\nMENU ITEMS:")
        for r in rows:
            print(f"[{r['id']}] {r['name']} - ₹{fm(r['price'])} | {r['category'] or 'Uncategorized'} | {'✅' if r['is_available'] else '❌'}")
    cur.close()

def add_menu_item(conn):
    name = input("Dish name: ").strip()
    if not name:
        print("⚠️ Name required.")
        return
    price = read_decimal("Selling price (blank=0): ")
    cost = read_decimal("Cost price (blank=0): ")
    prep_time = read_int("Prep time in minutes (blank=0): ")

    # category
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    cats = cur.fetchall()
    cat_id = None
    if cats:
        print("Existing categories:")
        for c in cats:
            print(f"  {c[0]} - {c[1]}")
        csel = input("Enter category id (or blank for none): ").strip()
        if csel:
            try:
                cat_id = int(csel)
            except:
                cat_id = None
    else:
        print("No categories found, will create uncategorized item.")

    cur.execute("""
        INSERT INTO menu_items (category_id, name, price, cost_price, prep_time)
        VALUES (%s, %s, %s, %s, %s)
    """, (cat_id, name, price, cost, prep_time))
    conn.commit()
    print("✅ Menu item added.")
    cur.close()

def edit_menu_item(conn):
    list_menu(conn)
    mid = input("Enter menu item ID to edit (blank=cancel): ").strip()
    if not mid:
        return
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM menu_items WHERE id=%s", (mid,))
    r = cur.fetchone()
    if not r:
        print("❌ Not found.")
        return
    newname = input(f"New name [{r['name']}]: ").strip() or r['name']
    newprice = read_decimal(f"New price [{r['price']}]: ") or Decimal(r['price'])
    avail_in = input(f"Available (y/n) [{'y' if r['is_available'] else 'n'}]: ").strip().lower()
    avail = 1 if avail_in in ('y', 'yes', '') else 0
    cur2 = conn.cursor()
    cur2.execute("UPDATE menu_items SET name=%s, price=%s, is_available=%s WHERE id=%s",
                 (newname, newprice, avail, mid))
    conn.commit()
    print("✅ Updated.")
    cur2.close(); cur.close()

def delete_menu_item(conn):
    list_menu(conn)
    mid = input("Menu item id to delete (blank=cancel): ").strip()
    if not mid:
        return
    confirm = input("Are you sure? (y/n): ").strip().lower()
    if confirm != 'y':
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM menu_items WHERE id=%s", (mid,))
    conn.commit()
    print("✅ Deleted.")
    cur.close()

# =========================================================
# INVENTORY
# =========================================================
def list_ingredients(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM ingredients ORDER BY name")
    rows = cur.fetchall()
    if not rows:
        print("No ingredients yet.")
    else:
        print("\nINGREDIENTS:")
        for r in rows:
            alert = "⚠️ LOW" if r['stock'] <= r['min_required'] else ""
            print(f"[{r['id']}] {r['name']} - {r['stock']} {r['unit']} {alert}")
    cur.close()

def add_ingredient(conn):
    name = input("Ingredient name: ").strip()
    if not name:
        print("⚠️ Ingredient name required.")
        return
    unit = input("Unit (e.g., kg/g/pcs/ltr): ").strip() or "unit"
    stock = read_decimal("Initial stock (blank=0): ")
    minreq = read_decimal("Min required threshold (blank=0): ")
    maxcap = read_decimal("Max capacity (blank=100): ")
    cost = read_decimal("Cost per unit (blank=0): ")
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ingredients (name, unit, stock, min_required, max_capacity, cost_price)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (name, unit, stock, minreq, maxcap, cost))
        conn.commit()
        print("✅ Ingredient added.")
    except mysql.connector.IntegrityError:
        print("⚠️ Already exists.")
    cur.close()

def update_stock(conn):
    list_ingredients(conn)
    iid = input("Ingredient ID (blank=cancel): ").strip()
    if not iid:
        return
    choice = input("Add (a) or Set new value (s): ").strip().lower()
    cur = conn.cursor()
    if choice == 'a':
        amt = read_decimal("Amount to add/subtract (negative allowed): ")
        cur.execute("UPDATE ingredients SET stock = stock + %s WHERE id=%s", (amt, iid))
    else:
        newval = read_decimal("Set new stock value: ")
        cur.execute("UPDATE ingredients SET stock = %s WHERE id=%s", (newval, iid))
    conn.commit()
    print("✅ Stock updated.")
    cur.close()

# =========================================================
# RECIPE MANAGEMENT
# =========================================================
def manage_recipes(conn):
    while True:
        print("\n--- Recipe Manager ---")
        print("1. View Recipes")
        print("2. Add Recipe")
        print("3. Delete Recipe")
        print("0. Back")
        ch = input("Choice: ").strip()
        if ch == '1':
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT r.id, m.name AS dish, i.name AS ingredient, r.qty_needed, i.unit
                FROM recipes r
                JOIN menu_items m ON m.id = r.menu_item_id
                JOIN ingredients i ON i.id = r.ingredient_id
                ORDER BY m.name
            """)
            rows = cur.fetchall()
            if not rows:
                print("No recipes yet.")
            else:
                for r in rows:
                    print(f"[{r['id']}] {r['dish']} → {r['ingredient']} : {r['qty_needed']} {r['unit']}")
            cur.close()
        elif ch == '2':
            list_menu(conn)
            mid = read_int("Menu item id: ")
            list_ingredients(conn)
            iid = read_int("Ingredient id: ")
            qty = read_decimal("Qty needed per serving: ")
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO recipes (menu_item_id, ingredient_id, qty_needed) VALUES (%s,%s,%s)",
                            (mid, iid, qty))
                conn.commit()
                print("✅ Recipe link added.")
            except mysql.connector.IntegrityError:
                print("⚠️ Already exists.")
            cur.close()
        elif ch == '3':
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT r.id, m.name dish, i.name ingredient
                FROM recipes r JOIN menu_items m ON m.id=r.menu_item_id
                JOIN ingredients i ON i.id=r.ingredient_id
            """)
            rows = cur.fetchall()
            for r in rows:
                print(f"[{r['id']}] {r['dish']} → {r['ingredient']}")
            rid = input("Recipe ID to delete: ").strip()
            if rid:
                cur2 = conn.cursor()
                cur2.execute("DELETE FROM recipes WHERE id=%s", (rid,))
                conn.commit()
                print("✅ Deleted.")
                cur2.close()
            cur.close()
        elif ch == '0':
            break

# =========================================================
# TABLE MANAGEMENT
# =========================================================
def manage_tables(conn):
    while True:
        print("\n--- Table Management ---")
        print("1. List Tables")
        print("2. Add Table")
        print("0. Back")
        ch = input("Choice: ").strip()
        if ch == '1':
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, name, seats FROM restaurant_tables ORDER BY name")
            for r in cur.fetchall():
                print(f"[{r['id']}] {r['name']} - {r['seats']} seats")
            cur.close()
        elif ch == '2':
            name = input("Table name: ").strip()
            if not name:
                print("⚠️ Table name required.")
                continue
            seats = read_int("Seats (blank=2): ") or 2
            cur = conn.cursor()
            cur.execute("INSERT INTO restaurant_tables (name, seats) VALUES (%s,%s)", (name, seats))
            conn.commit()
            print("✅ Table added.")
            cur.close()
        elif ch == '0':
            break

# =========================================================
# MAIN MENU
# =========================================================
def main():
    conn = get_conn()
    print("👨‍🍳 Restaurant RMS - Shopkeeper Mode\n")
    while True:
        print("\n=== SHOPKEEPER MENU ===")
        print("1. Categories")
        print("2. Menu Items")
        print("3. Ingredients (Inventory)")
        print("4. Recipes")
        print("5. Tables")
        print("0. Exit")
        ch = input("Choice: ").strip()
        if ch == '1':
            while True:
                print("\nCategories: 1=List 2=Add 0=Back")
                c = input("Choice: ").strip()
                if c == '1': list_categories(conn)
                elif c == '2': add_category(conn)
                elif c == '0': break
        elif ch == '2':
            while True:
                print("\nMenu: 1=List 2=Add 3=Edit 4=Delete 0=Back")
                c = input("Choice: ").strip()
                if c == '1': list_menu(conn)
                elif c == '2': add_menu_item(conn)
                elif c == '3': edit_menu_item(conn)
                elif c == '4': delete_menu_item(conn)
                elif c == '0': break
        elif ch == '3':
            while True:
                print("\nInventory: 1=List 2=Add Ingredient 3=Update Stock 0=Back")
                c = input("Choice: ").strip()
                if c == '1': list_ingredients(conn)
                elif c == '2': add_ingredient(conn)
                elif c == '3': update_stock(conn)
                elif c == '0': break
        elif ch == '4':
            manage_recipes(conn)
        elif ch == '5':
            manage_tables(conn)
        elif ch == '0':
            conn.close()
            print("\n👋 Exiting Shopkeeper RMS.")
            break
        else:
            print("⚠️ Invalid option.")

if __name__ == "__main__":
    main()
