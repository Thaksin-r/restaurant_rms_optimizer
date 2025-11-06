import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
import sys

# ---------- Database Configuration ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'thaksin',
    'database': 'restaurant_rms',
    'raise_on_warnings': True,
}

def fm(value):
    if value is None:
        return "0.00"
    value = Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return f"{value:.2f}"

def get_conn():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print("Database connection error:", err)
        sys.exit(1)

# ---------- SMART INTERACTIVE MEAL RECOMMENDER ----------
def smart_meal_recommender(conn):
    print("\n👋 Welcome to our Smart Meal Assistant!")
    name = input("May I have your name please? ").strip() or "Guest"
    budget = Decimal(input(f"Nice to meet you {name}! What’s your budget for today (₹)? ").strip() or "500")

    print(f"\nGot it, ₹{fm(budget)} it is.")
    choice = input("Would you like me to recommend dishes based on your budget? (yes/no): ").strip().lower()
    if choice not in ('yes', 'y'):
        print("Alright, feel free to browse our menu anytime. 😊")
        return

    pref = input("What’s your preference today? (Veg / Non-Veg / Mixed): ").strip().lower()

    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT m.id, m.name, m.price, c.name AS category
        FROM menu_items m
        JOIN categories c ON c.id = m.category_id
        WHERE c.name LIKE '%Main%' AND m.is_available = 1
        ORDER BY m.name
    """)
    mains = cur.fetchall()

    if pref == 'veg':
        mains = [m for m in mains if 'Paneer' in m['name'] or 'Veg' in m['name']]
    elif pref == 'non-veg':
        mains = [m for m in mains if 'Chicken' in m['name'] or 'Mutton' in m['name'] or 'Fish' in m['name']]

    if not mains:
        print("Sorry, no dishes match your preference today.")
        return

    print("\nHere are some main courses you might like:")
    for m in mains:
        print(f"[{m['id']}] {m['name']} - ₹{fm(m['price'])}")

    main_id = int(input("\nWhich one would you like to try? (Enter dish ID): ").strip())
    chosen_main = next((m for m in mains if m['id'] == main_id), None)
    if not chosen_main:
        print("Invalid choice.")
        return

    main_price = Decimal(chosen_main['price'])
    remaining = budget - main_price
    if remaining <= 0:
        print(f"\n⚠️ Your budget ₹{fm(budget)} is not enough for {chosen_main['name']} (₹{fm(main_price)}).")
        return

    print(f"\nExcellent choice! 🍛 {chosen_main['name']} costs ₹{fm(main_price)}.")
    print(f"You’ve got ₹{fm(remaining)} left. Let me find the perfect add-ons for you...")

    # Fetch all other dishes (excluding main)
    cur.execute("""
        SELECT m.id, m.name, m.price, c.name AS category
        FROM menu_items m
        JOIN categories c ON c.id = m.category_id
        WHERE m.id <> %s AND m.is_available = 1
        ORDER BY m.price ASC
    """, (main_id,))
    items = cur.fetchall()
    cur.close()

    weights = [float(r['price']) for r in items]
    values = [float(r['price']) for r in items]  # price as value
    n = len(items)
    W = int(remaining)

    # Knapsack DP
    dp = [[0 for _ in range(W + 1)] for _ in range(n + 1)]
    for i in range(1, n + 1):
        for w in range(W + 1):
            if weights[i - 1] <= w:
                dp[i][w] = max(values[i - 1] + dp[i - 1][int(w - weights[i - 1])], dp[i - 1][w])
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtrack
    res = dp[n][W]
    w = W
    selected = []
    for i in range(n, 0, -1):
        if res <= 0:
            break
        if res == dp[i - 1][w]:
            continue
        else:
            selected.append(i - 1)
            res -= values[i - 1]
            w -= int(weights[i - 1])

    # Interact with user
    print("\n🍽️ Based on your taste and budget, here’s what I recommend:\n")
    total = main_price
    accepted_items = []
    for i in selected[::-1]:
        dish = items[i]
        suggestion = input(f"Would you like to add {dish['name']} ({dish['category']}) for ₹{fm(dish['price'])}? (yes/no): ").strip().lower()
        if suggestion in ('yes', 'y'):
            accepted_items.append(dish)
            total += Decimal(dish['price'])
            remaining -= Decimal(dish['price'])
            print(f"Added ✅ {dish['name']}. Remaining budget: ₹{fm(remaining)}")
        else:
            print(f"Skipped ❌ {dish['name']}.")

    print("\n=================== 🧾 YOUR FINAL ORDER SUMMARY ===================")
    print(f"Customer: {name}")
    print(f"Preference: {pref.capitalize()}")
    print(f"Total Budget: ₹{fm(budget)}")
    print("-------------------------------------------------------------------")
    print(f"🍲 Main Course: {chosen_main['name']} - ₹{fm(main_price)}")
    if accepted_items:
        print("\n🥗 Add-ons:")
        for d in accepted_items:
            print(f"  • {d['name']} ({d['category']}) - ₹{fm(d['price'])}")
    else:
        print("\n🥗 No add-ons selected.")
    print("-------------------------------------------------------------------")
    print(f"Grand Total: ₹{fm(total)} / ₹{fm(budget)}")
    print(f"Remaining Balance: ₹{fm(remaining)}")
    print("===================================================================")
    print("🍽️ Thank you for dining smartly with our AI Recommender! Bon Appétit 😋\n")

# ---------- Run ----------
if __name__ == "__main__":
    print("Starting Interactive Smart Meal Recommender...")
    conn = get_conn()
    smart_meal_recommender(conn)
    conn.close()
