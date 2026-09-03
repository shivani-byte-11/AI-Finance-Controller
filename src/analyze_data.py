import pandas as pd
from pathlib import Path


# -----------------------------------
# Load dataset
# -----------------------------------

project_root = Path(__file__).resolve().parent.parent
data_file = project_root / "data" / "transactions.csv"

df = pd.read_csv(data_file)


# -----------------------------------
# Basic financial calculations
# -----------------------------------

income = df.loc[
    df["transaction_type"] == "Income",
    "amount"
].sum()

expenses = df.loc[
    df["transaction_type"] == "Expense",
    "amount"
].sum()

savings = income - expenses

savings_rate = (
    (savings / income) * 100
    if income > 0
    else 0
)

average_expense = df.loc[
    df["transaction_type"] == "Expense",
    "amount"
].mean()


# -----------------------------------
# Category-wise spending
# -----------------------------------

expense_df = df[
    df["transaction_type"] == "Expense"
]

category_spending = (
    expense_df
    .groupby("category")["amount"]
    .sum()
    .sort_values(ascending=False)
)


# -----------------------------------
# Largest transactions
# -----------------------------------

largest_transactions = (
    expense_df
    .sort_values("amount", ascending=False)
    .head(10)
)


# -----------------------------------
# Display results
# -----------------------------------

print("\n" + "=" * 60)
print("        AI FINANCE CONTROLLER - FINANCIAL ANALYSIS")
print("=" * 60)

print(f"\nTotal Income      : ₹{income:,.2f}")
print(f"Total Expenses    : ₹{expenses:,.2f}")
print(f"Net Savings       : ₹{savings:,.2f}")
print(f"Savings Rate      : {savings_rate:.2f}%")
print(f"Average Expense   : ₹{average_expense:,.2f}")


print("\n" + "-" * 60)
print("SPENDING BY CATEGORY")
print("-" * 60)

for category, amount in category_spending.items():
    print(f"{category:<20} ₹{amount:,.2f}")


print("\n" + "-" * 60)
print("TOP 10 LARGEST EXPENSES")
print("-" * 60)

print(
    largest_transactions[
        [
            "date",
            "category",
            "merchant",
            "amount",
            "payment_method"
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 60)