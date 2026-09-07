from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import random

RANDOM_SEED = 42
PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "expenses.csv"
random.seed(RANDOM_SEED)

categories = [
    "Housing",
    "Utilities",
    "Groceries",
    "Restaurants",
    "Coffee",
    "Delivery",
    "Transportation",
    "Beauty",
    "Gym",
    "Health Insurance",
    "AI Tools",
    "Shopping",
    "Entertainment",
    "Travel",
    "Subscriptions",
    "Other"
]

descriptions = {
    "Housing": ["Rent"],
    "Utilities": ["Electricity", "Water", "Internet", "Mobile Phone"],
    "Groceries": ["Supermarket", "Local Market", "Grocery Store"],
    "Restaurants": ["Restaurant", "Fast Food", "Brunch", "Dinner Out"],
    "Coffee": ["Coffee Shop", "Starbucks", "EspressoLab"],
    "Delivery": ["Food Delivery", "Grocery Delivery"],
    "Transportation": ["Metro", "Bus", "Taxi", "Fuel"],
    "Beauty": ["Nail Salon", "Hair Salon", "Skincare", "Beauty Treatment"],
    "Gym": ["Gym Membership"],
    "Health Insurance": ["Health Insurance Payment"],
    "AI Tools": ["AI Subscription"],
    "Shopping": ["Clothing", "Cosmetics", "Electronics", "Online Shopping"],
    "Entertainment": ["Cinema", "Concert", "Night Out", "Event"],
    "Travel": ["Flight", "Hotel", "Train", "Travel Expense"],
    "Subscriptions": ["Netflix", "Spotify", "Cloud Storage"],
    "Other": ["Miscellaneous Expense"]
}

amount_ranges = {
    "Housing": (12000, 12000),
    "Utilities": (300, 1800),
    "Groceries": (300, 1500),
    "Restaurants": (300, 1800),
    "Coffee": (100, 400),
    "Delivery": (250, 1200),
    "Transportation": (30, 900),
    "Beauty": (800, 2500),
    "Gym": (1500, 1500),
    "Health Insurance": (1500, 1500),
    "AI Tools": (1500, 1500),
    "Shopping": (400, 3500),
    "Entertainment": (250, 2000),
    "Travel": (800, 5000),
    "Subscriptions": (100, 600),
    "Other": (100, 1200)
}

monthly_frequencies = {
    "Housing": 1,
    "Utilities": 4,
    "Groceries": 8,
    "Restaurants": 6,
    "Coffee": 10,
    "Delivery": 4,
    "Transportation": 12,
    "Beauty": 1,
    "Gym": 1,
    "Health Insurance": 1,
    "AI Tools": 1,
    "Shopping": 4,
    "Entertainment": 3,
    "Travel": 2,
    "Other": 2
}

recurring_expenses = {
    "Subscriptions": {
        "Netflix": 250,
        "Spotify": 100,
        "Cloud Storage": 150
    }
}

months = [
    date(2026, 9, 1),
    date(2026, 10, 1),
    date(2026, 11, 1),
]

transactions = []

for month_start in months:
    for category, frequency in monthly_frequencies.items():
        for _ in range(frequency):
            description = random.choice(descriptions[category])

            min_amount, max_amount = amount_ranges[category]
            amount = random.randint(min_amount, max_amount)

            day_offset = random.randint(0, 29)
            transaction_date = month_start + timedelta(days=day_offset)

            transactions.append({
                "category": category,
                "description": description,
                "amount": amount,
                "date": transaction_date,
            })

    for category, services in recurring_expenses.items():
        for service_name, amount in services.items():
            day_offset = random.randint(0, 29)
            transaction_date = month_start + timedelta(days=day_offset)

            transactions.append({
                "category": category,
                "description": service_name,
                "amount": amount,
                "date": transaction_date,
            })

for transaction in transactions[:10]:
    print(transaction)

expenses_df = pd.DataFrame(transactions)
print(expenses_df.head())

DATA_PATH.parent.mkdir(exist_ok=True)
expenses_df.to_csv(DATA_PATH, index=False)
print(f"Data saved to {DATA_PATH}")
