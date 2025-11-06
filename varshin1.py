import mysql.connector
from mysql.connector import errorcode
from decimal import Decimal, ROUND_HALF_UP
import getpass
import sys
import datetime
import os

#create connection
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',
    'database': 'restaurant_rms',
    'raise_on_warnings':True,
}

#format money
def fm(value):
    if value is None:
        return "0.00"
    value = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return f"{value:.2f}"


#create connection
def get_conn():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print("Database connection error:", err)
        sys.exit(1)

# ---------- Menu management ----------
def list_menu_items(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT m.id, m.name, m.price, m.is_available, c.name AS category
        FROM menu_items m
        LEFT JOIN categories c ON c.id = m.category_id
        ORDER BY c.name, m.name
    """)
    rows = cur.fetchall()
    if not rows:
        print("No menu items.")
    else:
        print("Menu items:")
        for r in rows:
            avail = "YES" if r['is_available'] else "NO"
            print(f"[{r['id']}] {r['name']} -- ₹{fm(r['price'])} -- Category: {r['category'] or 'Uncategorized'} -- Available: {avail}")
    cur.close()

def add_menu_item(conn):
    name = input("Dish name: ").strip()
    price = Decimal(input("Price: ").strip())
    cost_price = Decimal(input("Cost price (optional, 0 if unknown): ").strip() or "0")
    # choose or create category
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    cats = cur.fetchall()
    cat_id = None
    if cats:
        print("Categories:")
        for cid, cname in cats:
            print(cid, cname)
        choose = input("Enter category id or leave blank to create/new: ").strip()
        if choose:
            cat_id = int(choose)
    if not cat_id:
        newcat = input("New category name (leave blank for none): ").strip()
        if newcat:
            cur.execute("INSERT INTO categories (name) VALUES (%s)", (newcat,))
            conn.commit()
            cat_id = cur.lastrowid
    cur.execute("""INSERT INTO menu_items (category_id, name, price, cost_price) VALUES (%s,%s,%s,%s)""",
                (cat_id, name, price, cost_price))
    conn.commit()
    print("Inserted menu item id:", cur.lastrowid)
    cur.close()

def edit_menu_item(conn):
    list_menu_items(conn)
    mid = input("Menu item id to edit: ").strip()
    if not mid: return
    mid = int(mid)
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, is_available FROM menu_items WHERE id=%s", (mid,))
    r = cur.fetchone()
    if not r:
        print("Not found.")
        cur.close(); return
    newname = input(f"New name [{r[1]}]: ").strip() or r[1]
    newprice = input(f"New price [{r[2]}]: ").strip() or str(r[2])
    avail = input(f"Available? (y/n) [{ 'y' if r[3] else 'n' }]: ").strip().lower()
    is_avail = 1 if avail in ('y','') else 0 if avail in ('n','no') else r[3]
    cur.execute("UPDATE menu_items SET name=%s, price=%s, is_available=%s WHERE id=%s",
                (newname, Decimal(newprice), is_avail, mid))
    conn.commit()
    print("Updated.")
    cur.close()

def delete_menu_item(conn):
    list_menu_items(conn)
    mid = input("Menu item id to delete (or blank): ").strip()
    if not mid:
        return
    mid = int(mid)
    confirm = input("Are you sure? This will remove item and its recipes (y/n): ").strip().lower()
    if confirm!='y':
        print("Cancelled.")
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM menu_items WHERE id=%s", (mid,))
    conn.commit()
    print("Deleted.")
    cur.close()

# ---------- Inventory ----------
def list_ingredients(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name, unit, stock, min_required FROM ingredients ORDER BY name")
    rows = cur.fetchall()
    if not rows:
        print("No ingredients.")
    else:
        print("Ingredients (stock):")
        for r in rows:
            low = " <LOW>" if Decimal(r['stock']) <= Decimal(r['min_required']) else ""
            print(f"[{r['id']}] {r['name']} : {r['stock']} {r['unit']}{low}")
    cur.close()

def add_ingredient(conn):
    name = input("Ingredient name: ").strip()
    unit = input("Unit (kg,g,pcs,ltr): ").strip()
    stock = Decimal(input("Initial stock (number): ").strip() or "0")
    minreq = Decimal(input("Min required (low stock threshold): ").strip() or "0")
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO ingredients (name, unit, stock, min_required) VALUES (%s,%s,%s,%s)",
                    (name, unit, stock, minreq))
        conn.commit()
        print("Added ingredient id:", cur.lastrowid)
    except mysql.connector.IntegrityError:
        print("Ingredient already exists.")
    cur.close()

def update_stock(conn):
    list_ingredients(conn)
    iid = input("Ingredient id to update: ").strip()
    if not iid: return
    iid = int(iid)
    change = input("Add or set? (a/s): ").strip().lower()
    cur = conn.cursor()
    if change=='a':
        amt = Decimal(input("Amount to add (use negative to subtract): ").strip())
        cur.execute("UPDATE ingredients SET stock = stock + %s WHERE id=%s", (amt, iid))
    else:
        amt = Decimal(input("Set stock to: ").strip())
        cur.execute("UPDATE ingredients SET stock = %s WHERE id=%s", (amt, iid))
    conn.commit()
    print("Updated stock.")
    cur.close()

def list_low_stock(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name, stock, unit, min_required FROM ingredients WHERE stock <= min_required")
    rows = cur.fetchall()
    if not rows:
        print("No low-stock ingredients.")
    else:
        print("LOW STOCK:")
        for r in rows:
            print(f"[{r['id']}] {r['name']}: {r['stock']} {r['unit']} (min {r['min_required']})")
    cur.close()

# ---------- Recipes (map menu->ingredients) ----------
def manage_recipes(conn):
    while True:
        print("\nRecipe manager: 1=list recipes 2=add recipe item 3=remove recipe item 4=back")
        c = input("Choice: ").strip()
        if c=='1':
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT r.id, m.name as dish, i.name as ingredient, r.qty_needed, i.unit
                FROM recipe r
                JOIN menu_items m ON m.id = r.menu_item_id
                JOIN ingredients i ON i.id = r.ingredient_id
                ORDER BY m.name
            """)
            for row in cur.fetchall():
                print(f"[{row['id']}] {row['dish']} -> {row['ingredient']} : {row['qty_needed']} {row['unit']}")
            cur.close()
        elif c=='2':
            list_menu_items(conn)
            mid = int(input("Menu item id: ").strip())
            list_ingredients(conn)
            iid = int(input("Ingredient id: ").strip())
            qty = Decimal(input("Qty needed per serving: ").strip())
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO recipe (menu_item_id, ingredient_id, qty_needed) VALUES (%s,%s,%s)",
                            (mid, iid, qty))
                conn.commit()
                print("Recipe entry added.")
            except mysql.connector.IntegrityError:
                print("Recipe entry exists. Update instead.")
            cur.close()
        elif c=='3':
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT r.id, m.name dish, i.name ingredient, r.qty_needed
                FROM recipe r JOIN menu_items m ON m.id=r.menu_item_id JOIN ingredients i ON i.id=r.ingredient_id
            """)
            rows = cur.fetchall()
            for row in rows:
                print(f"[{row['id']}] {row['dish']} -> {row['ingredient']} {row['qty_needed']}")
            rid = input("Recipe id to delete: ").strip()
            if rid:
                cur2 = conn.cursor()
                cur2.execute("DELETE FROM recipe WHERE id=%s", (int(rid),))
                conn.commit()
                cur2.close()
            cur.close()
        else:
            break

# ---------- Order flow ----------
TAX_RATE = Decimal("0.05")  # 5% GST, change as required

def create_order(conn):
    t = input("Order type (dine-in/takeaway) [d/t]: ").strip().lower()
    if t in ('d',''):
        order_type = 'dine-in'
        # list tables
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name, seats FROM restaurant_tables ORDER BY name")
        rows = cur.fetchall()
        print("Tables:")
        for r in rows:
            print(f"[{r['id']}] {r['name']} seats:{r['seats']}")
        tid = input("Table id (or leave blank to auto-assign): ").strip()
        table_id = int(tid) if tid else None
        cur.close()
    else:
        order_type = 'takeaway'
        table_id = None

    cur = conn.cursor()
    cur.execute("INSERT INTO orders (order_type, table_id, status) VALUES (%s,%s,'open')", (order_type, table_id))
    conn.commit()
    oid = cur.lastrowid
    print("Created order id:", oid)
    cur.close()
    manage_order(conn, oid)

def manage_order(conn, order_id=None):
    if not order_id:
        order_id = int(input("Order id to manage: ").strip())
    while True:
        print(f"\nManage order [{order_id}]: 1=add item 2=list items 3=remove item 4=finalize 5=cancel 6=back")
        choice = input("Choice: ").strip()
        if choice=='1':
            list_menu_items(conn)
            mid = int(input("Menu item id: ").strip())
            qty = int(input("Quantity: ").strip() or "1")
            # fetch price
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT price FROM menu_items WHERE id=%s AND is_available=1", (mid,))
            rec = cur.fetchone()
            cur.close()
            if not rec:
                print("Menu item not found or not available.")
                continue
            price = Decimal(rec['price'])
            line_total = price * qty
            cur2 = conn.cursor()
            cur2.execute("INSERT INTO order_items (order_id, menu_item_id, qty, unit_price, line_total) VALUES (%s,%s,%s,%s,%s)",
                         (order_id, mid, qty, price, line_total))
            conn.commit()
            cur2.close()
            print("Added.")
        elif choice=='2':
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT oi.id, m.name, oi.qty, oi.unit_price, oi.line_total
                FROM order_items oi JOIN menu_items m ON m.id=oi.menu_item_id
                WHERE oi.order_id=%s
            """, (order_id,))
            rows = cur.fetchall()
            if not rows:
                print("No items.")
            else:
                subtotal = Decimal("0")
                for r in rows:
                    subtotal += Decimal(r['line_total'])
                    print(f"[{r['id']}] {r['name']} x{r['qty']} @ {fm(r['unit_price'])} = {fm(r['line_total'])}")
                print("Subtotal:", fm(subtotal))
            cur.close()
        elif choice=='3':
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id, menu_item_id, qty, line_total FROM order_items WHERE order_id=%s", (order_id,))
            rows = cur.fetchall()
            for r in rows:
                print(f"[{r['id']}] item_id:{r['menu_item_id']} qty:{r['qty']} line:{r['line_total']}")
            rid = input("order_item id to remove: ").strip()
            if rid:
                cur2 = conn.cursor()
                cur2.execute("DELETE FROM order_items WHERE id=%s", (int(rid),))
                conn.commit()
                cur2.close()
            cur.close()
        elif choice=='4':  # finalize = compute totals, deduct inventory, create payment record
            finalize_order(conn, order_id)
            break
        elif choice=='5':
            cancel = input("Confirm cancel order? (y/n): ").strip().lower()
            if cancel=='y':
                cur = conn.cursor()
                cur.execute("UPDATE orders SET status='cancelled', closed_at=NOW() WHERE id=%s", (order_id,))
                conn.commit()
                cur.close()
                print("Order cancelled.")
                break
        else:
            break

def compute_order_totals(conn, order_id):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT SUM(line_total) as subtotal FROM order_items WHERE order_id=%s", (order_id,))
    r = cur.fetchone()
    cur.close()
    subtotal = Decimal(r['subtotal'] or 0)
    tax = (subtotal * TAX_RATE).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total = subtotal + tax
    return subtotal, tax, total

def deduct_inventory_for_order(conn, order_id):
    """
    Check recipe for each item and deduct from ingredients.
    If any ingredient insufficient -> rollback and return False + message
    """
    cur = conn.cursor(dictionary=True)
    # compute total quantities of each ingredient needed for this order
    cur.execute("""
        SELECT rec.ingredient_id, SUM(rec.qty_needed * oi.qty) AS total_needed, i.stock, i.unit, i.name
        FROM order_items oi
        JOIN recipe rec ON rec.menu_item_id = oi.menu_item_id
        JOIN ingredients i ON i.id = rec.ingredient_id
        WHERE oi.order_id=%s
        GROUP BY rec.ingredient_id
    """, (order_id,))
    reqs = cur.fetchall()
    if not reqs:
        # no recipes; nothing to deduct
        cur.close()
        return True, None
    # check sufficiency
    insufficient = []
    for r in reqs:
        if Decimal(r['stock']) < Decimal(r['total_needed']):
            insufficient.append((r['name'], r['stock'], r['total_needed'], r['unit']))
    if insufficient:
        cur.close()
        msg = "Insufficient ingredients:\n" + "\n".join([f"{x[0]}: have {x[1]} {x[3]}, need {x[2]}" for x in insufficient])
        return False, msg
    # deduct in transaction
    try:
        tcur = conn.cursor()
        for r in reqs:
            tcur.execute("UPDATE ingredients SET stock = stock - %s WHERE id=%s", (r['total_needed'], r['ingredient_id']))
        conn.commit()
        tcur.close()
        cur.close()
        return True, None
    except Exception as e:
        conn.rollback()
        cur.close()
        return False, str(e)

def finalize_order(conn, order_id):
    # compute totals
    subtotal, tax, total = compute_order_totals(conn, order_id)
    if subtotal == 0:
        print("Order has no items, cannot finalize.")
        return
    print("Subtotal:", fm(subtotal), "Tax:", fm(tax), "Total:", fm(total))
    # check & deduct inventory
    ok, msg = deduct_inventory_for_order(conn, order_id)
    if not ok:
        print("Cannot finalize:", msg)
        return
    # record totals and close order
    cur = conn.cursor()
    cur.execute("UPDATE orders SET subtotal=%s, tax=%s, total=%s, status='closed', closed_at=NOW() WHERE id=%s",
                (subtotal, tax, total, order_id))
    conn.commit()
    # create payment entry
    method = input("Payment method (cash/card/upi/other) [cash]: ").strip().lower() or "cash"
    paid_amt = Decimal(input(f"Amount received (total {fm(total)}): ").strip() or str(total))
    cur.execute("INSERT INTO payments (order_id, amount, method) VALUES (%s,%s,%s)", (order_id, paid_amt, method))
    conn.commit()
    print("Order finalized. Change:", fm(paid_amt - total))
    cur.close()

# ---------- Reports ----------
def daily_sales_report(conn):
    date_str = input("Enter date (YYYY-MM-DD) or leave blank for today: ").strip()
    if not date_str:
        date_str = datetime.date.today().isoformat()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT o.id, o.created_at, o.total, p.amount as paid_amount
        FROM orders o
        LEFT JOIN payments p ON p.order_id = o.id
        WHERE DATE(o.created_at) = %s AND o.status='closed'
        ORDER BY o.created_at
    """, (date_str,))
    rows = cur.fetchall()
    total_sales = Decimal('0.00')
    print("Sales for", date_str)
    for r in rows:
        print(f"Order {r['id']} at {r['created_at']}: Total {fm(r['total'])}")
        total_sales += Decimal(r['total'] or 0)
    print("TOTAL SALES:", fm(total_sales))
    cur.close()

# ---------- Tables management ----------
def list_tables(conn):
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, name, seats FROM restaurant_tables ORDER BY name")
    for r in cur.fetchall():
        print(f"[{r['id']}] {r['name']} seats:{r['seats']}")
    cur.close()

def add_table(conn):
    name = input("Table name: ").strip()
    seats = int(input("Seats: ").strip() or "2")
    cur = conn.cursor()
    cur.execute("INSERT INTO restaurant_tables (name, seats) VALUES (%s,%s)", (name, seats))
    conn.commit()
    print("Added table id:", cur.lastrowid)
    cur.close()

# ---------- Seed sample data ----------
def seed_sample(conn):
    cur = conn.cursor()
    # add categories
    cats = ['Starters','Main Course','Beverages','Desserts']
    for c in cats:
        try:
            cur.execute("INSERT INTO categories (name) VALUES (%s)", (c,))
        except:
            pass
    # ingredients
    ingredients = [
        ('Tomato','kg',10,1),
        ('Cheese','kg',5,0.5),
        ('Flour','kg',20,2),
        ('Sugar','kg',10,1),
        ('Chicken','kg',8,1),
        ('Rice','kg',30,5),
        ('Oil','ltr',10,2)
    ]
    for name,unit,stock,minr in ingredients:
        try:
            cur.execute("INSERT INTO ingredients (name,unit,stock,min_required) VALUES (%s,%s,%s,%s)",
                        (name,unit,stock,minr))
        except:
            pass
    conn.commit()
    # menu items
    try:
        cur.execute("INSERT IGNORE INTO menu_items (category_id,name,price,cost_price) VALUES ((SELECT id FROM categories WHERE name='Main Course'), %s,%s,%s)",
                    ('Fried Rice', 120.00, 50.00))
        cur.execute("INSERT IGNORE INTO menu_items (category_id,name,price,cost_price) VALUES ((SELECT id FROM categories WHERE name='Main Course'), %s,%s,%s)",
                    ('Chicken Curry', 180.00, 90.00))
        cur.execute("INSERT IGNORE INTO menu_items (category_id,name,price,cost_price) VALUES ((SELECT id FROM categories WHERE name='Beverages'), %s,%s,%s)",
                    ('Lemonade', 40.00, 10.00))
    except Exception as e:
        pass
    conn.commit()
    # create simple recipes
    # find ids
    cur.execute("SELECT id FROM menu_items WHERE name='Fried Rice'")
    row = cur.fetchone()
    if row:
        mid = row[0]
        # map to rice and oil
        cur.execute("SELECT id FROM ingredients WHERE name='Rice'")
        rid = cur.fetchone()
        if rid:
            try:
                cur.execute("INSERT IGNORE INTO recipe (menu_item_id, ingredient_id, qty_needed) VALUES (%s,%s,%s)",
                            (mid, rid[0], 0.25))
            except:
                pass
    conn.commit()
    # tables
    try:
        cur.execute("INSERT IGNORE INTO restaurant_tables (name,seats) VALUES ('T1',4),('T2',2),('T3',6)")
    except:
        pass
    conn.commit()
    cur.close()
    print("Seed complete.")

# ---------- Main CLI ----------
def main_menu():
    conn = get_conn()
    while True:
        print("\n--- Restaurant RMS ---")
        print("1) Menu management")
        print("2) Inventory")
        print("3) Recipes")
        print("4) Orders")
        print("5) Tables")
        print("6) Reports")
        print("7) Seed sample data")
        print("0) Exit")
        choice = input("Choice: ").strip()
        if choice=='1':
            while True:
                print("\nMenu: 1=list 2=add 3=edit 4=delete 5=back")
                c = input("Choice: ").strip()
                if c=='1': list_menu_items(conn)
                elif c=='2': add_menu_item(conn)
                elif c=='3': edit_menu_item(conn)
                elif c=='4': delete_menu_item(conn)
                else: break
        elif choice=='2':
            while True:
                print("\nInv: 1=list 2=add ingredient 3=update stock 4=low stock 5=back")
                c = input("Choice: ").strip()
                if c=='1': list_ingredients(conn)
                elif c=='2': add_ingredient(conn)
                elif c=='3': update_stock(conn)
                elif c=='4': list_low_stock(conn)
                else: break
        elif choice=='3':
            manage_recipes(conn)
        elif choice=='4':
            while True:
                print("\nOrders: 1=create order 2=manage existing 3=back")
                c = input("Choice: ").strip()
                if c=='1': create_order(conn)
                elif c=='2':
                    oid = input("Order id: ").strip()
                    if oid:
                        manage_order(conn, int(oid))
                else: break
        elif choice=='5':
            while True:
                print("\nTables: 1=list 2=add 3=back")
                c = input("Choice: ").strip()
                if c=='1': list_tables(conn)
                elif c=='2': add_table(conn)
                else: break
        elif choice=='6':
            while True:
                print("\nReports: 1=daily sales 2=low stock 3=back")
                c = input("Choice: ").strip()
                if c=='1': daily_sales_report(conn)
                elif c=='2': list_low_stock(conn)
                else: break
        elif choice=='7':
            seed_sample(conn)
        elif choice=='0':
            conn.close()
            print("Bye.")
            break
        else:
            print("Unknown choice.")

if __name__ == '__main__':
    print("Starting RMS...")
    main_menu()
