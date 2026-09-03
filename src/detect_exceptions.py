import pandas as pd
from pathlib import Path


# -----------------------------
# LOAD TRANSACTIONS
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "transactions.csv"
RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_FILE)

df["date"] = pd.to_datetime(df["date"])
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")


# -----------------------------
# EXCEPTION DETECTION
# -----------------------------

exceptions = []


# 1. VERY LARGE TRANSACTIONS
threshold = df["amount"].quantile(0.99)

large_transactions = df[df["amount"] >= threshold]

for _, row in large_transactions.iterrows():
    exceptions.append({
        "date": row["date"],
        "transaction_id": row["transaction_id"],
        "type": "Large Transaction",
        "category": row["category"],
        "merchant": row["merchant"],
        "amount": row["amount"],
        "reason": f"Transaction is above the 99th percentile (₹{threshold:,.2f})"
    })


# 2. DUPLICATE TRANSACTIONS

duplicates = df[df.duplicated(
    subset=["date", "amount", "merchant", "payment_method"],
    keep=False
)]

for _, row in duplicates.iterrows():
    exceptions.append({
        "date": row["date"],
        "transaction_id": row["transaction_id"],
        "type": "Possible Duplicate",
        "category": row["category"],
        "merchant": row["merchant"],
        "amount": row["amount"],
        "reason": "Similar transaction appears more than once"
    })


# 3. UNUSUALLY LARGE CATEGORY TRANSACTIONS

category_mean = df.groupby("category")["amount"].transform("mean")

unusual_category = df[df["amount"] > category_mean * 3]

for _, row in unusual_category.iterrows():
    exceptions.append({
        "date": row["date"],
        "transaction_id": row["transaction_id"],
        "type": "Category Anomaly",
        "category": row["category"],
        "merchant": row["merchant"],
        "amount": row["amount"],
        "reason": "Amount is more than 3× the category average"
    })


# 4. NEGATIVE TRANSACTIONS

negative_transactions = df[df["amount"] < 0]

for _, row in negative_transactions.iterrows():
    exceptions.append({
        "date": row["date"],
        "transaction_id": row["transaction_id"],
        "type": "Negative Amount",
        "category": row["category"],
        "merchant": row["merchant"],
        "amount": row["amount"],
        "reason": "Transaction contains a negative amount"
    })


# -----------------------------
# SAVE RESULTS
# -----------------------------

exceptions_df = pd.DataFrame(exceptions)

output_file = RESULTS_DIR / "exceptions.csv"

exceptions_df.to_csv(output_file, index=False)


# -----------------------------
# DISPLAY RESULTS
# -----------------------------

print("=" * 70)
print("AI FINANCE CONTROLLER - EXCEPTION DETECTION")
print("=" * 70)

print(f"\nTotal transactions checked : {len(df):,}")
print(f"Exceptions detected        : {len(exceptions_df):,}")

print("\nEXCEPTION SUMMARY")
print("-" * 70)

if len(exceptions_df) > 0:

    print(
        exceptions_df["type"]
        .value_counts()
        .to_string()
    )

    print("\nTOP EXCEPTIONS")
    print("-" * 70)

    print(
        exceptions_df[
            [
                "date",
                "type",
                "category",
                "merchant",
                "amount",
                "reason"
            ]
        ]
        .sort_values("amount", ascending=False)
        .head(10)
        .to_string(index=False)
    )

else:
    print("No exceptions detected.")

print("\nResults saved to:")
print(output_file)