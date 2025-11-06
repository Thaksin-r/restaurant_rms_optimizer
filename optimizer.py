#!/usr/bin/env python3
"""
optimizer.py
-------------
Analyzes restaurant menu data using knapsack optimization.
Works directly with your restaurant_rms schema.
Automatically fixes precision issues (e.g., avg_profit_margin truncation).
Generates clear, structured output with profitability and stock analytics.
"""

import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import random

# ---------- DB Configuration ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',
    'database': 'restaurant_rms',
    'raise_on_warnings':True,
}

# ---------- Helpers ----------
def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def fm(value):
    """Format decimals safely."""
    return f"{Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"

def separator(title=None):
    print("\n" + "=" * 60)
    if title:
        print(f"📊 {title}")
        print("=" * 60)

# ---------- Knapsack Algorithms ----------
def zero_one_knapsack(items, capacity):
    n = len(items)
    dp = [[0 for _ in range(int(capacity * 1000) + 1)] for _ in range(n + 1)]
    keep = [[0 for _ in range(int(capacity * 1000) + 1)] for _ in range(n + 1)]

    for i in range(1, n + 1):
        wt = int(items[i - 1]['weight'] * 1000)
        val = float(items[i - 1]['profit'])
        for w in range(int(capacity * 1000) + 1):
            if wt <= w and (val + dp[i - 1][w - wt]) > dp[i - 1][w]:
                dp[i][w] = val + dp[i - 1][w - wt]
                keep[i][w] = 1
            else:
                dp[i][w] = dp[i - 1][w]

    res = []
    w = int(capacity * 1000)
    for i in range(n, 0, -1):
        if keep[i][w] == 1:
            res.append(items[i - 1])
            w -= int(items[i - 1]['weight'] * 1000)
    return res[::-1], Decimal(str(dp[n][int(capacity * 1000)]))

def fractional_knapsack(items, capacity):
    items = sorted(items, key=lambda x: x['profit'] / x['weight'], reverse=True)
    total_profit = Decimal('0.00')
    used = []
    remaining = capacity
    for it in items:
        if it['weight'] <= remaining:
            used.append((it, 1.0))
            total_profit += it['profit']
            remaining -= it['weight']
        else:
            frac = remaining / it['weight']
            used.append((it, frac))
            total_profit += it['profit'] * Decimal(str(frac))
            break
    return used, total_profit

# ---------- Auto Schema Fix ----------
def ensure_cost_analysis_precision(conn):
    """Ensure avg_profit_margin column has sufficient precision."""
    cur = conn.cursor()
    cur.execute("SHOW COLUMNS FROM cost_analysis LIKE 'avg_profit_margin'")
    row = cur.fetchone()
    if row and "decimal" in row[1].lower():
        # Modify only if too low precision
        if "decimal(5" in row[1].lower() or "decimal(6" in row[1].lower():
            print("🧩 Adjusting avg_profit_margin precision to DECIMAL(10,4)...")
            cur.execute("ALTER TABLE cost_analysis MODIFY COLUMN avg_profit_margin DECIMAL(10,4)")
            conn.commit()
            print("✅ Precision updated.")
    cur.close()

# ---------- Optimization Runner ----------
def run_optimization():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    separator("Initializing Optimizer")

    # Step 1: Read menu and sales data
    cur.execute("""
        SELECT m.id, m.name, m.price, m.cost_price, IFNULL(SUM(oi.qty),0) AS sold
        FROM menu_items m
        LEFT JOIN order_items oi ON oi.menu_item_id = m.id
        GROUP BY m.id
    """)
    rows = cur.fetchall()

    if not rows:
        print("❌ No menu data found. Please run shopkeeper & customer feeds first.")
        return

    max_price = max(float(r['price']) for r in rows if r['price'])
    items = []

    separator("Menu Items with Computed Metrics")
    for r in rows:
        profit = Decimal(r['price']) - Decimal(r['cost_price'])
        weight = Decimal(r['price']) / Decimal(max_price)
        sold = r['sold']
        prep_time = random.choice([1, 8, 10, 15, 18])
        print(f" - {r['name']:<25} ₹{fm(r['price']):>6} | Profit ₹{fm(profit):>6} | Weight {fm(weight):>5} | Sold {sold}")
        items.append({
            'id': r['id'],
            'name': r['name'],
            'price': Decimal(r['price']),
            'profit': profit,
            'weight': weight,
            'sold': sold,
            'prep': prep_time
        })

    # Step 2: Rankings
    separator("Top Performers")
    print("🏆 By Popularity:")
    for it in sorted(items, key=lambda x: x['sold'], reverse=True)[:5]:
        print(f"  {it['name']:<25} Sold {it['sold']}")

    print("\n💰 By Profit:")
    for it in sorted(items, key=lambda x: x['profit'], reverse=True)[:5]:
        print(f"  {it['name']:<25} Profit ₹{fm(it['profit'])}")

    print("\n⏱️ By Preparation Time (Fastest):")
    for it in sorted(items, key=lambda x: x['prep'])[:5]:
        print(f"  {it['name']:<25} Prep {it['prep']} mins")

    # Step 3: Inventory health
    cur.execute("SELECT SUM(stock) AS total_stock, COUNT(*) AS items FROM ingredients")
    inv = cur.fetchone()
    storage_fraction = Decimal(inv['total_stock'] / (inv['items'] * 10)) if inv and inv['items'] else Decimal('0.75')
    storage_fraction = min(storage_fraction, Decimal('1.0'))
    print(f"\n📦 Storage Fraction: {fm(storage_fraction)} (stock/max ratio)")

    # Step 4: Knapsack Optimization
    separator("0/1 Knapsack (Full Selection)")
    full_combo, full_profit = zero_one_knapsack(items, storage_fraction)
    for it in full_combo:
        print(f"  {it['name']:<25} | Profit ₹{fm(it['profit'])} | Weight {fm(it['weight'])}")
    print(f"\nEstimated Total Profit (Full): ₹ {fm(full_profit)}")

    separator("Fractional Knapsack (Partial Combos)")
    frac_combo, frac_profit = fractional_knapsack(items, storage_fraction)
    for it, frac in frac_combo:
        print(f"  {it['name']:<25} | Fraction {frac:.2f} | Profit ₹{fm(it['profit'] * Decimal(str(frac)))}")
    print(f"\nEstimated Total Profit (Fractional): ₹ {fm(frac_profit)}")

    # Step 5: Discount Logic
    separator("Discount Suggestions")
    today = datetime.now().date()
    low_sales = [it for it in items if it['sold'] < 5 and it['profit'] > 50]
    if not low_sales:
        print("No discount suggestions at this time.")
    else:
        for it in low_sales:
            print(f"  {it['name']:<25} → 10% off ({it['sold']} sold, margin ₹{fm(it['profit'])})")

    # Step 6: Ensure table precision and log results
    ensure_cost_analysis_precision(conn)

    cur.execute("SHOW TABLES LIKE 'cost_analysis'")
    if cur.fetchone():
        total_cost = sum(it['price'] - it['profit'] for it in items)
        total_revenue = sum(it['price'] for it in items)
        avg_profit = (full_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        avg_profit = avg_profit.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

        cur.execute("""
            INSERT INTO cost_analysis (date_generated, total_cost, total_revenue, avg_profit_margin, max_profit, loss, suggestions)
            VALUES (CURDATE(), %s, %s, %s, %s, %s, %s)
        """, (total_cost, total_revenue, avg_profit, full_profit, Decimal('0.00'), "Knapsack optimizer results"))
        conn.commit()
        print("\n🧾 Cost analysis entry logged.")

    cur.execute("SHOW TABLES LIKE 'reports'")
    if cur.fetchone():
        cur.execute("""
            INSERT INTO reports (report_date, top_dish, least_dish, total_sales, total_profit)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            today,
            max(items, key=lambda x: x['sold'])['name'],
            min(items, key=lambda x: x['sold'])['name'],
            sum(Decimal(x['price'] * x['sold']) for x in items),
            sum(x['profit'] * x['sold'] for x in items)
        ))
        conn.commit()
        print("📊 Daily report logged.")

    separator("Optimization Completed")
    print("✨ All computations successful.\n")

    cur.close()
    conn.close()

# ---------- Run ----------
if __name__ == "__main__":
    run_optimization()
