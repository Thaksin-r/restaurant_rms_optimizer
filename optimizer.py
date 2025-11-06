#!/usr/bin/env python3
"""
optimizer.py — Restaurant RMS Optimization & Analytics (Schema Matched)

Dynamic Programming:
    • 0/1 Knapsack — Ingredient-aware dish optimization.
    • LIS (Longest Increasing Subsequence) — Trending analysis.

Greedy:
    • Price optimization, ingredient efficiency, discount suggestions.

Divide & Conquer:
    • QuickSort — Ranking dishes by profit margin.

Additional:
    • Cost analysis saved in `cost_analysis` table.
    • Pareto 80/20 analysis for top-selling dishes.
    • Low stock alerts and management suggestions.
    • Readable, sectioned, emoji-rich output.
"""

import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import List, Dict

# ==============================
# Database Configuration
# ==============================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "thaksin",  # change if needed
    "database": "restaurant_rms",
    "raise_on_warnings": True,
}

# ==============================
# Helpers
# ==============================
def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def fm(val):
    if val is None:
        val = Decimal('0.00')
    return f"{Decimal(val).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"

def sep(title=None):
    print("\n" + "=" * 70)
    if title:
        print(f"📊 {title}")
        print("=" * 70)

# ==============================
# Algorithms
# ==============================
def quicksort(items, key_func):
    if len(items) <= 1:
        return items
    pivot = items[0]
    left = [x for x in items[1:] if key_func(x) >= key_func(pivot)]
    right = [x for x in items[1:] if key_func(x) < key_func(pivot)]
    return quicksort(left, key_func) + [pivot] + quicksort(right, key_func)

def longest_increasing_subsequence(seq):
    if not seq:
        return 0
    n = len(seq)
    dp = [1] * n
    for i in range(1, n):
        for j in range(i):
            if seq[i] > seq[j]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)

def knapsack(items, capacity):
    n = len(items)
    dp = [[Decimal(0)] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wt = items[i - 1]['weight']
        val = items[i - 1]['profit']
        for c in range(1, capacity + 1):
            if wt <= c:
                dp[i][c] = max(val + dp[i - 1][c - wt], dp[i - 1][c])
            else:
                dp[i][c] = dp[i - 1][c]
    selected = []
    c = capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            selected.append(items[i - 1])
            c -= items[i - 1]['weight']
    return selected[::-1], dp[n][capacity]

# ==============================
# Analytics Runner
# ==============================
def run_optimizer():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    sep("Initializing Restaurant Optimizer")

    # 1️⃣ Fetch menu items
    cur.execute("SELECT * FROM menu_items WHERE is_available = 1")
    menu_items = cur.fetchall()
    if not menu_items:
        print("❌ No menu items available.")
        return

    # 2️⃣ Compute ingredient-based cost & weight
    items = []
    for item in menu_items:
        cur.execute("""
            SELECT SUM(r.qty_needed) AS total_qty,
                   SUM(i.cost_price * r.qty_needed) AS ingredient_cost
            FROM recipe r
            JOIN ingredients i ON r.ingredient_id = i.id
            WHERE r.menu_item_id = %s
        """, (item['id'],))
        rec = cur.fetchone()
        ingredient_cost = Decimal(rec['ingredient_cost'] or 0)
        total_qty = int(rec['total_qty'] or 1)
        profit = Decimal(item['price']) - ingredient_cost
        items.append({
            'id': item['id'],
            'name': item['name'],
            'price': Decimal(item['price']),
            'profit': profit,
            'weight': max(1, total_qty)
        })

    sep("1️⃣ Menu Items & Profit Analysis")
    for it in items:
        print(f"- {it['name']:<30} ₹{fm(it['price'])} | Profit ₹{fm(it['profit'])} | Weight {it['weight']}")

    # 3️⃣ Compute ingredient stock capacity
    cur.execute("SELECT SUM(stock) AS total_stock FROM ingredients")
    total_stock = int(cur.fetchone()['total_stock'] or 100)
    capacity = min(total_stock, 1000)  # prevent over-scaling

    sep("2️⃣ Ingredient Stock Capacity")
    print(f"Total available ingredient units: {capacity}")

    # 4️⃣ Knapsack (optimal dish set)
    selected, max_profit = knapsack(items, capacity)
    sep("3️⃣ Optimal Dish Combination (Knapsack DP)")
    for it in selected:
        print(f"✅ {it['name']:<25} | Profit ₹{fm(it['profit'])} | Weight {it['weight']}")
    print(f"💰 Estimated Total Profit: ₹{fm(max_profit)}")

    # 5️⃣ Trending analysis (LIS)
    cur.execute("SELECT orders_sold FROM menu_stats ORDER BY menu_item_id")
    seq = [int(x['orders_sold']) for x in cur.fetchall()]
    trend_score = longest_increasing_subsequence(seq)
    sep("4️⃣ Trending Analysis (LIS)")
    print(f"🔥 Trending Growth Length: {trend_score}")

    # 6️⃣ Price optimizer
    sep("5️⃣ Dynamic Price Suggestions")
    for it in items:
        cost = it['price'] - it['profit']
        margin = (it['profit'] / max(cost, Decimal(1)))
        if margin < Decimal('0.2'):
            print(f"🔼 Increase {it['name']} by 10% (Low margin {margin:.2%})")
        elif margin > Decimal('0.6'):
            print(f"🔽 Decrease {it['name']} by 5% (High margin {margin:.2%})")
        else:
            print(f"➖ Keep {it['name']} stable ({margin:.2%})")

    # 7️⃣ Low stock alert
    sep("6️⃣ Low Stock Alerts")
    cur.execute("SELECT name, stock, min_required, max_capacity FROM ingredients")
    low_stock = [i for i in cur.fetchall() if i['stock'] <= i['min_required']]
    if low_stock:
        for i in low_stock:
            print(f"⚠ {i['name']}: Stock {fm(i['stock'])}/{fm(i['min_required'])}")
    else:
        print("✅ All ingredient levels sufficient.")

    # 8️⃣ Profit margin ranking
    sep("7️⃣ Profit Margin Ranking (QuickSort)")
    sorted_items = quicksort(items, lambda x: x['profit'] / max(x['price'] - x['profit'], Decimal(1)))
    for it in sorted_items[:5]:
        margin = (it['profit'] / max(it['price'] - it['profit'], Decimal(1))) * 100
        print(f"{it['name']:<25} → Margin {fm(margin)}%")

    # 9️⃣ Pareto (80/20) analysis
    sep("8️⃣ Pareto Analysis (Top 20% dishes)")
    cur.execute("SELECT menu_item_id, orders_sold FROM menu_stats ORDER BY orders_sold DESC")
    stats = cur.fetchall()
    total_sales = sum(int(s['orders_sold']) for s in stats) or 0
    if total_sales == 0:
        print("No sales data available yet.")
    else:
        cumulative = 0
        top = []
        for s in stats:
            cumulative += s['orders_sold']
            cur.execute("SELECT name FROM menu_items WHERE id=%s", (s['menu_item_id'],))
            name = cur.fetchone()['name']
            top.append(name)
            if cumulative / total_sales >= 0.8:
                break
        print("Top dishes contributing ~80% of sales:")
        print(", ".join(top))

    # 🔟 Discount suggestions
    sep("9️⃣ Discount Suggestions (Greedy)")
    discount_list = [it for it in items if it['profit'] > 50]
    for it in discount_list[:5]:
        print(f"💸 Suggest 10% off on {it['name']} (High margin ₹{fm(it['profit'])})")

    # 🧾 Save in cost_analysis and reports
    sep("🔟 Saving Analytics to Database")
    total_cost = sum(it['price'] - it['profit'] for it in items)
    total_revenue = sum(it['price'] for it in items)
    avg_margin = ((total_revenue - total_cost) / max(total_cost, Decimal(1))) * 100
    loss = max(total_cost - total_revenue, Decimal('0.00'))

    cur.execute("""
        INSERT INTO cost_analysis (date_generated, total_cost, total_revenue, avg_profit_margin, max_profit, loss, suggestions)
        VALUES (CURDATE(), %s, %s, %s, %s, %s, %s)
    """, (total_cost, total_revenue, round(avg_margin, 4), max_profit, loss, "Auto-Optimizer Results"))
    conn.commit()
    print("✅ cost_analysis entry inserted.")

    top_dish = selected[0]['name'] if selected else 'N/A'
    least_dish = items[-1]['name']
    cur.execute("""
        INSERT INTO reports (report_date, top_dish, least_dish, total_sales, total_profit)
        VALUES (CURDATE(), %s, %s, %s, %s)
    """, (top_dish, least_dish, total_revenue, max_profit))
    conn.commit()
    print("✅ reports entry inserted.")

    sep("✅ Optimization Complete")
    print("✨ Analytics run finished successfully.\n")

    cur.close()
    conn.close()

# ==============================
# Run once
# ==============================
if __name__ == "__main__":
    run_optimizer()
