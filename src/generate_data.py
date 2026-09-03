import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
from pathlib import Path

fake = Faker()

# -----------------------------
# Configuration
# -----------------------------
NUM_TRANSACTIONS = 2000

categories = [
    "Food",
    "Shopping",
    "Transport",
    "Bills",
    "Entertainment",
    "Healthcare",
    "Education",
    "Travel",
    "Groceries",
    "Salary",
    "Freelance",
    "Investment",
    "Other"
]

payment_methods = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Cash",
    "Bank Transfer"
]

merchants = [
    "Amazon",
    "Flipkart",
    "Swiggy",
    "Zomato",
    "Uber",
    "Ola",
    "Netflix",
    "Spotify",
    "Myntra",
    "BigBasket",
    "DMart",
    "Airtel",
    "Jio",
    "Electricity Board",
    "College",
    "Hospital",
    "IRCTC",
    "BookMyShow"
]

# -----------------------------
# Generate transactions
# -----------------------------
transactions = []

start_date = datetime(2025, 1, 1)

for i in range(NUM_TRANSACTIONS):

    date = start_date + timedelta(
        days=random.randint(0, 365)
    )

    transaction_type = random.choices(
        ["Expense", "Income"],
        weights=[85, 15]
    )[0]

    if transaction_type == "Income":

        category = random.choice([
            "Salary",
            "Freelance",
            "Investment"
        ])

        amount = round(
            random.uniform(5000, 80000),
            2
        )

        merchant = random.choice([
            "Company",
            "Client",
            "Bank",
            "Investment Account"
        ])

    else:

        category = random.choice([
            "Food",
            "Shopping",
            "Transport",
            "Bills",
            "Entertainment",
            "Healthcare",
            "Education",
            "Travel",
            "Groceries",
            "Other"
        ])

        merchant = random.choice(merchants)

        amount = round(
            random.uniform(50, 15000),
            2
        )

    payment_method = random.choice(payment_methods)

    transactions.append({
        "transaction_id": f"TXN{i + 1:05d}",
        "date": date.strftime("%Y-%m-%d"),
        "transaction_type": transaction_type,
        "category": category,
        "merchant": merchant,
        "amount": amount,
        "payment_method": payment_method
    })


# -----------------------------
# Create DataFrame
# -----------------------------
df = pd.DataFrame(transactions)

# Sort by date
df = df.sort_values("date").reset_index(drop=True)


# -----------------------------
# Add some realistic anomalies
# -----------------------------
anomaly_indices = random.sample(
    range(len(df)),
    40
)

for index in anomaly_indices:

    if df.loc[index, "transaction_type"] == "Expense":

        df.loc[index, "amount"] = round(
            random.uniform(20000, 100000),
            2
        )


# -----------------------------
# Save dataset
# -----------------------------
project_root = Path(__file__).resolve().parent.parent

data_folder = project_root / "data"

data_folder.mkdir(
    exist_ok=True
)

output_file = data_folder / "transactions.csv"

df.to_csv(
    output_file,
    index=False
)


# -----------------------------
# Display result
# -----------------------------
print("=" * 50)
print("FINANCE DATASET GENERATED SUCCESSFULLY")
print("=" * 50)

print(f"Total transactions : {len(df)}")
print(f"Dataset location   : {output_file}")

print("\nFirst 5 transactions:")
print(df.head())

print("\nTransaction types:")
print(df["transaction_type"].value_counts())

print("\nCategories:")
print(df["category"].value_counts())