#!/usr/bin/env python3
"""
restaurant_rms.py — Restaurant Management System (Main Entry)
-------------------------------------------------------------
Home launcher that allows choosing between:
👨‍🍳 Shopkeeper Mode  — manage menu, inventory, recipes, and optimizer.
🍗 Customer Mode      — place orders, view menu, make payments.

Runs shopkeeper.py or customer.py seamlessly.
"""

import sys
import subprocess
import os

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    while True:
        clear()
        print("=" * 60)
        print("🍴 WELCOME TO RESTAURANT RMS 🍽️".center(60))
        print("=" * 60)
        print("\nPlease select a mode:")
        print("1️⃣  Shopkeeper Mode (Manage Restaurant)")
        print("2️⃣  Customer Mode (Place Orders)")
        print("0️⃣  Exit System")
        print("-" * 60)
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            clear()
            print("👨‍🍳 Launching Shopkeeper Mode...\n")
            try:
                subprocess.run([sys.executable, "shopkeeper.py"], check=False)
            except KeyboardInterrupt:
                print("\n⚠️ Shopkeeper Mode interrupted.")
            input("\nPress Enter to return to main menu...")

        elif choice == "2":
            clear()
            print("🍗 Launching Customer Mode...\n")
            try:
                subprocess.run([sys.executable, "customer.py"], check=False)
            except KeyboardInterrupt:
                print("\n⚠️ Customer Mode interrupted.")
            input("\nPress Enter to return to main menu...")

        elif choice == "0":
            print("\n👋 Thank you for using Restaurant RMS!")
            print("💡 Tip: Run this again anytime to manage or order food.")
            print("=" * 60)
            sys.exit(0)

        else:
            print("⚠️ Invalid input, please choose 1, 2, or 0.")
            input("Press Enter to retry...")

if __name__ == "__main__":
    main()
