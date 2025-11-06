# ============================================================
# 🛒 Shopping Cart Optimizer using Dynamic Programming
# Author: [Your Name]
# College DSA Project
# ============================================================

# Problem:
# Given a list of items (name, price, and value),
# and a fixed budget, select the combination of items
# that maximizes total value without exceeding the budget.
# ============================================================

class Item:
    """Represents a shopping item with name, price, and value."""
    def __init__(self, name, price, value):
        self.name = name
        self.price = price
        self.value = value


def knapsack_optimizer(items, budget):
    """
    Solves the 0/1 Knapsack problem using Dynamic Programming.
    Returns the maximum achievable value and the chosen items.
    """
    n = len(items)
    dp = [[0 for _ in range(budget + 1)] for _ in range(n + 1)]

    # Build DP table
    for i in range(1, n + 1):
        for w in range(1, budget + 1):
            if items[i - 1].price <= w:
                dp[i][w] = max(
                    items[i - 1].value + dp[i - 1][w - items[i - 1].price],
                    dp[i - 1][w]
                )
            else:
                dp[i][w] = dp[i - 1][w]

    # Trace back to find selected items
    chosen = []
    w = budget
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            chosen.append(items[i - 1])
            w -= items[i - 1].price

    chosen.reverse()
    return dp[n][budget], chosen


def display_items(items):
    """Displays available items in a table format."""
    print("\nAvailable Items:")
    print("-" * 50)
    print(f"{'No.':<5}{'Item Name':<20}{'Price (₹)':<12}{'Value':<10}")
    print("-" * 50)
    for i, item in enumerate(items, 1):
        print(f"{i:<5}{item.name:<20}{item.price:<12}{item.value:<10}")
    print("-" * 50)


def main():
    print("=" * 60)
    print("🛒 SHOPPING CART OPTIMIZER — Using Dynamic Programming")
    print("=" * 60)

    # Sample inventory (you can make this dynamic)
    items = [
        Item("Laptop", 25000, 90),
        Item("Smartphone", 18000, 80),
        Item("Headphones", 4000, 40),
        Item("Smartwatch", 6000, 50),
        Item("Bluetooth Speaker", 3000, 30),
        Item("Backpack", 1500, 25),
        Item("Keyboard", 2000, 35),
        Item("External HDD", 5000, 45)
    ]

    display_items(items)

    # User input for budget
    while True:
        try:
            budget = int(input("\nEnter your shopping budget (₹): "))
            if budget <= 0:
                raise ValueError
            break
        except ValueError:
            print("❌ Please enter a valid positive number for budget.")

    # Compute optimal selection
    max_value, chosen = knapsack_optimizer(items, budget)

    # Display results
    print("\n" + "=" * 60)
    print("🧠 OPTIMIZATION RESULT")
    print("=" * 60)
    if chosen:
        print(f"{'Item Name':<25}{'Price (₹)':<12}{'Value':<10}")
        print("-" * 50)
        total_cost = 0
        for item in chosen:
            print(f"{item.name:<25}{item.price:<12}{item.value:<10}")
            total_cost += item.price
        print("-" * 50)
        print(f"{'TOTAL COST:':<25}₹{total_cost}")
        print(f"{'TOTAL VALUE:':<25}{max_value}")
        print(f"{'BUDGET LEFT:':<25}₹{budget - total_cost}")
        print("=" * 60)
        print("✅ These items give you the maximum value within your budget!")
    else:
        print("⚠️ No items can be purchased within your budget.")
    print("=" * 60)

    # Efficiency metric
    if chosen:
        efficiency = max_value / sum(item.price for item in chosen)
        print(f"💡 Value-to-Cost Efficiency: {efficiency:.2f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
