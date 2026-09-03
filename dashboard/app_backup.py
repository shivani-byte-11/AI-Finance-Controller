import streamlit as st
import pandas as pd
from pathlib import Path
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Finance Controller",
    page_icon="💰",
    layout="wide"
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

if gemini_api_key:
    client = genai.Client(api_key=gemini_api_key)
else:
    client = None


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "transactions.csv"
EXCEPTIONS_FILE = BASE_DIR / "results" / "exceptions.csv"


# ============================================================
# LOAD TRANSACTION DATA
# ============================================================

df = pd.read_csv(DATA_FILE)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df["amount"] = pd.to_numeric(
    df["amount"],
    errors="coerce"
).fillna(0)


# ============================================================
# LOAD AI EXCEPTIONS
# ============================================================

if EXCEPTIONS_FILE.exists():

    exceptions_df = pd.read_csv(EXCEPTIONS_FILE)

    if not exceptions_df.empty:

        if "date" in exceptions_df.columns:
            exceptions_df["date"] = pd.to_datetime(
                exceptions_df["date"],
                errors="coerce"
            )

        if "amount" in exceptions_df.columns:
            exceptions_df["amount"] = pd.to_numeric(
                exceptions_df["amount"],
                errors="coerce"
            ).fillna(0)

else:
    exceptions_df = pd.DataFrame()


# ============================================================
# TITLE
# ============================================================

st.title("💰 AI Finance Controller")

st.markdown(
    "### Personal Finance Dashboard"
)

st.caption(
    "Track spending, identify financial risk, and use Gemini AI "
    "to understand unusual transactions."
)

st.divider()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Filters")

categories = ["All"] + sorted(
    df["category"].dropna().unique().tolist()
)

selected_category = st.sidebar.selectbox(
    "Category",
    categories
)

payment_methods = ["All"] + sorted(
    df["payment_method"].dropna().unique().tolist()
)

selected_payment = st.sidebar.selectbox(
    "Payment Method",
    payment_methods
)

filtered_df = df.copy()

if selected_category != "All":
    filtered_df = filtered_df[
        filtered_df["category"] == selected_category
    ]

if selected_payment != "All":
    filtered_df = filtered_df[
        filtered_df["payment_method"] == selected_payment
    ]


st.sidebar.info(
    "Financial Risk uses your full transaction history. "
    "Filters narrow spending and exception analysis only."
)


# ============================================================
# FILTER AI EXCEPTIONS TO MATCH THE ACTIVE DATASET
# ============================================================
# The exceptions file may not contain payment_method. When it does not,
# enrich it from the original transaction data using stable transaction
# fields before applying the active filters. This keeps risk metrics and
# all AI features consistent with the dashboard filters.
active_exceptions_df = exceptions_df.copy()

if not active_exceptions_df.empty:

    match_columns = [
        column
        for column in [
            "date",
            "category",
            "merchant",
            "amount"
        ]
        if column in active_exceptions_df.columns
        and column in df.columns
    ]

    if "payment_method" not in active_exceptions_df.columns and match_columns:
        payment_lookup = (
            df[match_columns + ["payment_method"]]
            .drop_duplicates(subset=match_columns)
        )

        active_exceptions_df = active_exceptions_df.merge(
            payment_lookup,
            on=match_columns,
            how="left"
        )

    if selected_category != "All" and "category" in active_exceptions_df.columns:
        active_exceptions_df = active_exceptions_df[
            active_exceptions_df["category"] == selected_category
        ]

    if selected_payment != "All" and "payment_method" in active_exceptions_df.columns:
        active_exceptions_df = active_exceptions_df[
            active_exceptions_df["payment_method"] == selected_payment
        ]


# ============================================================
# FINANCIAL METRICS — OVERALL HEALTH + FILTERED SPENDING VIEW
# ============================================================
# Important: category/payment filters are useful for spending analysis,
# but they should not redefine a user's total income or overall risk.
# Example: filtering to Groceries can legitimately show ₹0 income.
# That must NOT make the user's overall financial health look worse.

overall_income = df.loc[
    df["transaction_type"] == "Income", "amount"
].sum()

overall_expenses = df.loc[
    df["transaction_type"] == "Expense", "amount"
].sum()

overall_net_savings = overall_income - overall_expenses

overall_savings_rate = (
    (overall_net_savings / overall_income) * 100
    if overall_income > 0 else 0
)

filtered_income = filtered_df.loc[
    filtered_df["transaction_type"] == "Income", "amount"
].sum()

filtered_expenses = filtered_df.loc[
    filtered_df["transaction_type"] == "Expense", "amount"
].sum()

filtered_net_savings = filtered_income - filtered_expenses

expense_df = filtered_df[
    filtered_df["transaction_type"] == "Expense"
]

average_expense = (
    expense_df["amount"].mean()
    if not expense_df.empty else 0
)

# Backward-compatible aliases used by the AI and alert sections.
# These now intentionally refer to OVERALL financial health.
total_income = overall_income
total_expenses = overall_expenses
net_savings = overall_net_savings
savings_rate = overall_savings_rate


# ============================================================
# INTELLIGENT FINANCIAL RISK SCORE — OVERALL PROFILE
# ============================================================

expense_income_ratio = (
    overall_expenses / overall_income
    if overall_income > 0 else 1.0
)

# 1. Savings health — maximum 40 points
if overall_income <= 0:
    savings_risk = 40
elif overall_savings_rate < -20:
    savings_risk = 40
elif overall_savings_rate < -10:
    savings_risk = 35
elif overall_savings_rate < 0:
    savings_risk = 30
elif overall_savings_rate < 10:
    savings_risk = 20
elif overall_savings_rate < 20:
    savings_risk = 10
else:
    savings_risk = 0

# 2. Spending pressure — maximum 25 points
if expense_income_ratio >= 1.20:
    spending_risk = 25
elif expense_income_ratio >= 1.00:
    spending_risk = 20
elif expense_income_ratio >= 0.80:
    spending_risk = 12
elif expense_income_ratio >= 0.60:
    spending_risk = 6
else:
    spending_risk = 0

# 3. Suspicious activity — maximum 20 points
overall_suspicious_count = len(exceptions_df)
filtered_suspicious_count = len(active_exceptions_df)

if overall_suspicious_count >= 50:
    suspicious_risk = 20
elif overall_suspicious_count >= 25:
    suspicious_risk = 16
elif overall_suspicious_count >= 10:
    suspicious_risk = 12
elif overall_suspicious_count >= 5:
    suspicious_risk = 8
elif overall_suspicious_count > 0:
    suspicious_risk = 4
else:
    suspicious_risk = 0

# 4. Large transaction exposure — maximum 15 points
overall_expense_df = df[
    df["transaction_type"] == "Expense"
]

if not overall_expense_df.empty and overall_income > 0:
    largest_expense_for_risk = overall_expense_df["amount"].max()
    largest_expense_ratio = (
        largest_expense_for_risk / overall_income
    )
else:
    largest_expense_for_risk = 0
    largest_expense_ratio = 0

if largest_expense_ratio >= 0.08:
    large_transaction_risk = 15
elif largest_expense_ratio >= 0.05:
    large_transaction_risk = 12
elif largest_expense_ratio >= 0.03:
    large_transaction_risk = 8
elif largest_expense_ratio >= 0.01:
    large_transaction_risk = 4
else:
    large_transaction_risk = 0

risk_score = min(
    100,
    savings_risk
    + spending_risk
    + suspicious_risk
    + large_transaction_risk
)

if risk_score >= 70:
    risk_level = "High Risk"
    risk_icon = "🔴"
elif risk_score >= 45:
    risk_level = "Moderate Risk"
    risk_icon = "🟠"
elif risk_score >= 25:
    risk_level = "Low-Moderate Risk"
    risk_icon = "🟡"
else:
    risk_level = "Low Risk"
    risk_icon = "🟢"

# ============================================================
# PROFESSIONAL KPI SUMMARY
# ============================================================

def format_inr_compact(value):
    """Display large INR values in a compact, readable format."""
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)

    if value >= 1e7:
        return f"{sign}₹{value / 1e7:.2f} Cr"
    elif value >= 1e5:
        return f"{sign}₹{value / 1e5:.2f} L"
    elif value >= 1e3:
        return f"{sign}₹{value / 1e3:.1f} K"
    else:
        return f"{sign}₹{value:,.0f}"


st.subheader("📌 Financial Summary")
st.caption(
    "Overall financial health is calculated from all transactions; "
    "the active filters affect the detailed spending view below."
)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(
        "💰 Total Income",
        format_inr_compact(overall_income)
    )

with kpi2:
    st.metric(
        "💸 Total Expenses",
        format_inr_compact(overall_expenses)
    )

with kpi3:
    st.metric(
        "💵 Net Savings",
        format_inr_compact(overall_net_savings),
        delta=f"{overall_savings_rate:.2f}% savings"
    )

with kpi4:
    st.metric(
        "📊 Savings Rate",
        f"{overall_savings_rate:.2f}%"
    )

with kpi5:
    st.metric(
        "🚨 Risk Score",
        f"{risk_score}/100",
        delta=risk_level,
        delta_color="inverse"
    )


# ============================================================
# FINANCIAL HEALTH STATUS
# ============================================================

st.subheader("🚨 Financial Health")

health_col1, health_col2 = st.columns([1, 3])

with health_col1:
    st.metric(
        "Risk Level",
        f"{risk_icon} {risk_level}"
    )

with health_col2:

    if risk_score >= 70:

        st.error(
            "⚠️ **High Financial Risk** — "
            "Your financial profile shows significant risk. "
            "Review your spending, negative savings, and "
            "flagged transactions."
        )

    elif risk_score >= 45:

        st.warning(
            "⚠️ **Moderate Financial Risk** — "
            "Your financial profile needs attention. "
            "Consider reducing discretionary spending and "
            "building a stronger savings buffer."
        )

    else:

        st.success(
            "✅ **Healthy Financial Position** — "
            "Your current income and spending pattern show "
            "relatively low financial risk."
        )


# ============================================================
# RISK SCORE BREAKDOWN
# ============================================================

st.markdown("#### 🧩 Risk Score Breakdown")
st.caption(
    "The score combines savings health, spending pressure, "
    "suspicious activity, and large-transaction exposure. "
    "Maximum score: 100. Higher means greater financial risk."
)

risk_breakdown = pd.DataFrame({
    "Risk Factor": [
        "Savings Health",
        "Spending Pressure",
        "Suspicious Activity",
        "Large Transaction Exposure"
    ],
    "Points": [
        savings_risk,
        spending_risk,
        suspicious_risk,
        large_transaction_risk
    ],
    "Maximum": [40, 25, 20, 15]
})

risk_breakdown["Contribution"] = (
    risk_breakdown["Points"] / risk_breakdown["Maximum"] * 100
).round(0).astype(int).astype(str) + "%"

st.dataframe(
    risk_breakdown,
    hide_index=True,
    use_container_width=True
)

# ============================================================
# VISUAL RISK GAUGE
# ============================================================

st.markdown("#### 🎯 Overall Risk Gauge")

# Dynamic, color-coded gauge for a clearer buildathon demo.
if risk_score >= 70:
    gauge_color = "#ef4444"
elif risk_score >= 25:
    gauge_color = "#f59e0b"
else:
    gauge_color = "#22c55e"

gauge_width = max(2, min(100, risk_score))

# Use HTML/CSS so the gauge color reflects the actual risk level.
st.markdown(
    f"""
    <div style="margin: 8px 0 18px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:1rem; font-weight:600;">Risk Level: {risk_score}/100 — {risk_level}</span>
            <span style="background:{gauge_color}; color:white; padding:4px 10px; border-radius:999px; font-size:0.85rem; font-weight:700;">{risk_level}</span>
        </div>
        <div style="height:18px; background:#262936; border-radius:999px; overflow:hidden; border:1px solid #343746;">
            <div style="width:{gauge_width}%; height:100%; background:{gauge_color}; border-radius:999px; transition:width .3s ease;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:7px; color:#aeb3c2; font-size:0.8rem;">
            <span>0</span><span>25</span><span>70</span><span>100</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

gauge_col1, gauge_col2, gauge_col3 = st.columns(3)

with gauge_col1:
    st.caption("🟢 0–24: Low Risk")

with gauge_col2:
    st.caption("🟡 25–69: Moderate / Watch")

with gauge_col3:
    st.caption("🔴 70–100: High Risk")


st.divider()

# ============================================================
# RISK DRIVER BREAKDOWN — BUILDATHON EXPLAINABILITY LAYER
# ============================================================

st.subheader("🧭 Why is your risk score high?")
st.caption("The score is calculated from four transparent risk drivers.")

risk_drivers = pd.DataFrame({
    "Risk Driver": [
        "Savings Health",
        "Spending Pressure",
        "Suspicious Activity",
        "Large Transaction Exposure"
    ],
    "Score": [
        savings_risk,
        spending_risk,
        suspicious_risk,
        large_transaction_risk
    ],
    "Maximum": [40, 25, 20, 15]
})

risk_drivers["Utilization"] = (
    risk_drivers["Score"] / risk_drivers["Maximum"] * 100
).round(0).astype(int)

risk_drivers["Status"] = risk_drivers["Utilization"].apply(
    lambda x: "🔴 Critical" if x >= 75 else (
        "🟠 Watch" if x >= 40 else "🟢 Healthy"
    )
)

st.dataframe(
    risk_drivers[["Risk Driver", "Score", "Maximum", "Utilization", "Status"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.NumberColumn(format="%d"),
        "Maximum": st.column_config.NumberColumn(format="%d"),
        "Utilization": st.column_config.ProgressColumn(
            "Risk Utilization",
            min_value=0,
            max_value=100,
            format="%d%%"
        )
    }
)

# Identify the dominant contributor to the current risk score.
driver_values = {
    "Savings Health": savings_risk,
    "Spending Pressure": spending_risk,
    "Suspicious Activity": suspicious_risk,
    "Large Transaction Exposure": large_transaction_risk
}

top_risk_driver = max(driver_values, key=driver_values.get)
top_risk_points = driver_values[top_risk_driver]

if top_risk_driver == "Savings Health":
    next_best_action = "Reduce the expense-to-income gap and protect cash reserves."
elif top_risk_driver == "Spending Pressure":
    next_best_action = "Review the largest spending categories and cut avoidable expenses."
elif top_risk_driver == "Suspicious Activity":
    next_best_action = "Verify flagged transactions before taking further financial action."
else:
    next_best_action = "Review the largest transactions and confirm they are expected."

risk_col1, risk_col2 = st.columns(2)

with risk_col1:
    st.metric(
        "🎯 Biggest Risk Driver",
        top_risk_driver,
        f"{top_risk_points} points"
    )

with risk_col2:
    st.info(f"**Next best action:** {next_best_action}")


# ============================================================
# AI ACTION CENTER — BUILDATHON DEMO LAYER
# ============================================================

st.subheader("🎯 AI Financial Action Center")
st.caption(
    "Turn detected financial risks into clear next actions — powered by your actual transaction data."
)

# Identify the biggest spending category at this point in the dashboard.
early_category_spending = (
    expense_df.groupby("category")["amount"]
    .sum()
    .sort_values(ascending=False)
)

if not early_category_spending.empty:
    action_category = early_category_spending.index[0]
    action_category_amount = early_category_spending.iloc[0]
else:
    action_category = "your spending"
    action_category_amount = 0

action_items = []

if net_savings < 0:
    action_items.append((
        "🔴 ACT NOW",
        "Control the spending gap",
        f"You are spending {format_inr_compact(abs(net_savings))} more than your income.",
        "Review your largest discretionary expenses and reduce non-essential spending first."
    ))
elif savings_rate < 20:
    action_items.append((
        "🟠 PRIORITY",
        "Improve your savings rate",
        f"Your current savings rate is {savings_rate:.2f}%.",
        "Identify recurring expenses that can be reduced and redirect the savings toward your buffer."
    ))
else:
    action_items.append((
        "🟢 MAINTAIN",
        "Protect your savings",
        f"Your savings rate is {savings_rate:.2f}%.",
        "Continue tracking monthly spending and avoid allowing discretionary expenses to grow faster than income."
    ))

if filtered_suspicious_count > 0:
    action_items.append((
        "🟠 REVIEW",
        "Verify flagged transactions",
        f"The AI exception detector found {filtered_suspicious_count} suspicious transaction(s).",
        "Open the Suspicious Transaction Analyzer below and verify unusual merchants, amounts, categories, and reasons."
    ))
else:
    action_items.append((
        "🟢 MONITOR",
        "Keep transaction monitoring active",
        "No suspicious transactions are currently flagged.",
        "Continue reviewing new transactions so unusual activity can be caught early."
    ))

action_items.append((
    "🟡 OPTIMIZE",
    f"Review {action_category} spending",
    f"{format_inr_compact(action_category_amount)} is your highest spending category.",
    "Use the category and monthly charts below to identify repeat purchases and opportunities to reduce spending."
))

act_cols = st.columns(3)

for i, (badge, title, reason, action) in enumerate(action_items[:3]):
    with act_cols[i]:
        st.markdown(f"**{badge}**")
        st.markdown(f"### {title}")
        st.caption(reason)
        st.info(f"**What to do:** {action}")

st.markdown(
    "**Demo flow:** Detect risk → Explain the cause → Recommend an action → Verify the transaction.",
    help="This is the core AI-assisted finance workflow demonstrated by the dashboard."
)

st.divider()



# ============================================================
# ADDITIONAL FINANCIAL METRIC
# ============================================================

st.subheader("📈 Expense Statistics")

stat1, stat2 = st.columns(2)

with stat1:
    st.metric(
        "Average Expense",
        f"₹{average_expense:,.2f}"
    )

with stat2:
    st.metric(
        "Suspicious Transactions",
        overall_suspicious_count,
        delta=f"{filtered_suspicious_count} in current view"
    )


st.divider()


# ============================================================
# SPENDING INSIGHTS
# ============================================================

st.subheader("📊 Spending Insights")

category_spending = (
    expense_df
    .groupby("category")["amount"]
    .sum()
    .sort_values(ascending=False)
)

if not category_spending.empty:

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:

        st.markdown("#### 🛒 Spending by Category")

        st.bar_chart(
            category_spending
        )

    with chart_col2:

        st.markdown("#### 💳 Spending by Payment Method")

        payment_spending = (
            expense_df
            .groupby("payment_method")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        st.bar_chart(
            payment_spending
        )

else:

    st.info(
        "No expense data available for the selected filters."
    )


# ============================================================
# MONTHLY ANALYSIS
# ============================================================

st.subheader("📈 Monthly Financial Trend")

if not filtered_df.empty:

    monthly = (
        filtered_df
        .assign(
            month=filtered_df["date"]
            .dt.to_period("M")
            .astype(str)
        )
        .groupby(
            ["month", "transaction_type"]
        )["amount"]
        .sum()
        .unstack(
            fill_value=0
        )
        .sort_index()
    )

    st.line_chart(monthly)

    if "Income" in monthly.columns and "Expense" in monthly.columns:

        monthly["Net Savings"] = (
            monthly["Income"] -
            monthly["Expense"]
        )

        st.markdown("#### 💾 Monthly Net Savings")

        st.bar_chart(
            monthly["Net Savings"]
        )

else:

    st.info("No monthly data available.")


# ============================================================
# TOP EXPENSES
# ============================================================

st.subheader("🏆 Top 10 Largest Expenses")

top_expenses = (
    expense_df
    .sort_values(
        "amount",
        ascending=False
    )
    .head(10)
)

if not top_expenses.empty:

    display_columns = [
        column
        for column in [
            "date",
            "category",
            "merchant",
            "amount",
            "payment_method"
        ]
        if column in top_expenses.columns
    ]

    st.dataframe(
        top_expenses[display_columns],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No expenses available.")


# ============================================================
# AI DETECTED EXCEPTIONS
# ============================================================

st.divider()

st.subheader("🤖 AI Detected Exceptions")

if not active_exceptions_df.empty:

    exception_count = filtered_suspicious_count

    st.warning(
        f"🚨 {exception_count} suspicious transaction(s) detected."
    )

    if "type" in active_exceptions_df.columns:

        exception_summary = (
            active_exceptions_df["type"]
            .value_counts()
            .rename_axis("Exception Type")
            .reset_index(name="Count")
        )

        st.dataframe(
            exception_summary,
            hide_index=True,
            use_container_width=True
        )

    st.markdown("#### 🔍 Suspicious Transactions")

    available_columns = [
        column
        for column in [
            "date",
            "type",
            "category",
            "merchant",
            "amount",
            "reason"
        ]
        if column in active_exceptions_df.columns
    ]

    display_exceptions = (
        active_exceptions_df[available_columns]
        .sort_values(
            "amount",
            ascending=False
        )
    )

    st.dataframe(
        display_exceptions,
        hide_index=True,
        use_container_width=True
    )

else:

    st.success(
        "✅ No suspicious transactions detected."
    )


# ============================================================
# FINANCIAL CONTEXT FOR GEMINI
# ============================================================

if not category_spending.empty:

    highest_category = category_spending.index[0]
    highest_category_amount = category_spending.iloc[0]

else:

    highest_category = "N/A"
    highest_category_amount = 0


if not expense_df.empty:

    largest_row = expense_df.loc[
        expense_df["amount"].idxmax()
    ]

    largest_expense = largest_row["amount"]
    largest_merchant = largest_row.get(
        "merchant",
        "N/A"
    )
    largest_category = largest_row.get(
        "category",
        "N/A"
    )

else:

    largest_expense = 0
    largest_merchant = "N/A"
    largest_category = "N/A"


suspicious_count = filtered_suspicious_count


financial_data = f"""
Active Filters:
Category: {selected_category}
Payment Method: {selected_payment}

Overall financial health metrics are calculated from the full transaction dataset.
Filtered metrics describe the current Category/Payment Method view.

OVERALL FINANCIAL HEALTH
Total Income:
₹{overall_income:,.2f}

Total Expenses:
₹{overall_expenses:,.2f}

Net Savings:
₹{overall_net_savings:,.2f}

Savings Rate:
{overall_savings_rate:.2f}%

Average Expense:
₹{average_expense:,.2f}

Financial Risk Score:
{risk_score}/100

Financial Risk Level:
{risk_level}

Risk Score Breakdown:
Savings Health: {savings_risk}/40
Spending Pressure: {spending_risk}/25
Suspicious Activity: {suspicious_risk}/20
Large Transaction Exposure: {large_transaction_risk}/15

Expense-to-Income Ratio:
{expense_income_ratio:.2f}x

Highest Spending Category:
{highest_category}

Highest Category Spending:
₹{highest_category_amount:,.2f}

Largest Expense:
₹{largest_expense:,.2f}

Largest Expense Merchant:
{largest_merchant}

Largest Expense Category:
{largest_category}

Overall Suspicious Transactions:
{overall_suspicious_count}

Filtered View
Category: {selected_category}
Payment Method: {selected_payment}
Filtered Income: ₹{filtered_income:,.2f}
Filtered Expenses: ₹{filtered_expenses:,.2f}
Filtered Net: ₹{filtered_net_savings:,.2f}
Filtered Suspicious Transactions: {filtered_suspicious_count}

Top Spending Categories:
{category_spending.head(5).to_string()}
"""


# ============================================================
# GEMINI AI FUNCTION
# ============================================================

def ask_finance_ai(question, financial_data):

    if client is None:

        return (
            "⚠️ Gemini API key is not configured. "
            "Please check your .env file."
        )

    instructions = """
You are Finance AI inside a personal finance dashboard.

Use ONLY the financial information supplied to you.

Rules:
1. Never invent financial numbers.
2. Never change supplied numbers.
3. Use Indian Rupee (₹).
3a. Treat the supplied Active Filters as the scope of the analysis.
3b. Do not use assumptions or global/unfiltered metrics outside that scope.
4. Explain financial information in simple language.
5. Give concise and useful answers.
6. If the supplied data is insufficient, say so.
7. Never claim a transaction is fraud unless the supplied
   data proves it.
8. General budgeting suggestions are allowed.
9. Do not provide professional investment, tax, legal,
   or financial advice.
"""

    prompt = f"""
Financial information:

{financial_data}

User question:

{question}
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=instructions
            )
        )

        return response.text

    except Exception as e:

        return f"⚠️ Finance AI error: {str(e)}"


# ============================================================
# AI FINANCIAL RECOMMENDATIONS
# ============================================================

st.subheader("🎯 AI Financial Recommendations")

st.markdown(
    "Turn your financial data into a clear, prioritized action plan."
)

if st.button(
    "✨ Generate AI Recommendations",
    type="secondary"
):

    if client is None:

        st.error(
            "⚠️ Gemini API key is not configured. "
            "Please check your .env file."
        )

    else:

        recommendation_prompt = f"""
You are the AI recommendation engine inside a personal finance controller.

Analyze ONLY this financial data:

{financial_data}

Return exactly 3 recommendations as valid JSON in this format:
[
  {{
    "priority": "High",
    "title": "short title",
    "reason": "one concise sentence using the supplied numbers",
    "action": "one concrete action the user can take"
  }}
]

Rules:
- Use only supplied numbers and facts.
- Never invent numbers.
- Use ₹ for currency.
- Do not call any transaction fraud.
- Prioritize overspending, low/negative savings, and suspicious transactions.
- Keep each field concise.
"""

        with st.spinner(
            "🤖 Gemini is generating your action plan..."
        ):

            try:

                recommendation_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=recommendation_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )

                import json

                raw_recommendations = recommendation_response.text.strip()

                if raw_recommendations.startswith("```"):
                    raw_recommendations = raw_recommendations.replace(
                        "```json", "", 1
                    ).replace("```", "").strip()

                recommendations = json.loads(raw_recommendations)

                st.markdown("### 💡 Your Personalized Action Plan")

                cols = st.columns(3)

                priority_icons = {
                    "High": "🔴",
                    "Medium": "🟠",
                    "Low": "🟢"
                }

                for index, recommendation in enumerate(recommendations[:3]):

                    priority = str(
                        recommendation.get("priority", "Medium")
                    ).title()

                    icon = priority_icons.get(
                        priority,
                        "🟠"
                    )

                    with cols[index]:

                        st.markdown(
                            f"### {icon} {priority} Priority"
                        )

                        st.markdown(
                            f"**{recommendation.get('title', 'Recommendation')}**"
                        )

                        st.caption("Why this matters")
                        st.write(
                            recommendation.get(
                                "reason",
                                "Review this area of your finances."
                            )
                        )

                        st.caption("Recommended action")
                        st.info(
                            recommendation.get(
                                "action",
                                "Review your recent spending."
                            )
                        )

            except Exception as e:

                st.error(
                    f"Finance AI error: {str(e)}"
                )


# ============================================================
# AI SUSPICIOUS TRANSACTION ANALYZER
# ============================================================

if not active_exceptions_df.empty:

    st.divider()

    st.subheader(
        "🧠 AI Suspicious Transaction Analyzer"
    )

    st.write(
        "Select a flagged transaction and let Finance AI explain "
        "why it may be unusual and what you should review."
    )

    analyzer_columns = [
        column
        for column in [
            "date",
            "type",
            "category",
            "merchant",
            "amount",
            "reason"
        ]
        if column in active_exceptions_df.columns
    ]

    analyzer_df = active_exceptions_df[
        analyzer_columns
    ].copy()

    if "amount" in analyzer_df.columns:

        analyzer_df = analyzer_df.sort_values(
            "amount",
            ascending=False
        )

    transaction_labels = []

    for _, row in analyzer_df.iterrows():

        merchant = row.get(
            "merchant",
            "Unknown merchant"
        )

        amount = row.get(
            "amount",
            0
        )

        exception_type = row.get(
            "type",
            "Unknown exception"
        )

        try:
            amount_text = f"₹{float(amount):,.2f}"
        except (TypeError, ValueError):
            amount_text = "₹0.00"

        transaction_labels.append(
            f"{merchant} — {amount_text} — {exception_type}"
        )

    if transaction_labels:

        selected_transaction = st.selectbox(
            "🔎 Select a suspicious transaction",
            transaction_labels
        )

        selected_position = transaction_labels.index(
            selected_transaction
        )

        selected_row = analyzer_df.iloc[
            selected_position
        ]

        if st.button(
            "🤖 Analyze Transaction with AI",
            type="primary"
        ):

            try:

                selected_amount = float(
                    selected_row.get(
                        "amount",
                        0
                    )
                )

            except (TypeError, ValueError):

                selected_amount = 0

            transaction_context = f"""
Suspicious transaction:

Date:
{selected_row.get('date', 'N/A')}

Type:
{selected_row.get('type', 'N/A')}

Category:
{selected_row.get('category', 'N/A')}

Merchant:
{selected_row.get('merchant', 'N/A')}

Amount:
₹{selected_amount:,.2f}

Detection reason:
{selected_row.get('reason', 'N/A')}

Overall financial context:

Risk Score:
{risk_score}/100

Risk Level:
{risk_level}

Savings Rate:
{savings_rate:.2f}%

Overall Suspicious Transactions:
{overall_suspicious_count}
Filtered Suspicious Transactions:
{filtered_suspicious_count}
"""

            transaction_question = f"""
Analyze this flagged transaction.

{transaction_context}

Explain in simple language:

1. Why the transaction was flagged based on the supplied data.
2. What makes it unusual, if the supplied data supports that.
3. What the user should review or verify.
4. Do not claim that it is fraud unless the supplied data proves it.
5. Do not invent any facts or numbers.
"""

            with st.spinner(
                "🤖 AI is analyzing the suspicious transaction..."
            ):

                analysis = ask_finance_ai(
                    transaction_question,
                    transaction_context
                )

            st.markdown(
                "### 🧠 AI Transaction Analysis"
            )

            st.info(analysis)


# ============================================================
# ASK FINANCE AI
# ============================================================

st.divider()

st.subheader("🧠 Ask Finance AI")

st.markdown(
    "Ask questions about your income, expenses, savings, "
    "spending patterns, risk, or suspicious transactions."
)

question = st.text_input(
    "💬 Ask a question",
    placeholder="Example: Why is my financial risk high?"
)

if question:

    with st.spinner(
        "🤖 Finance AI is analyzing your finances..."
    ):

        answer = ask_finance_ai(
            question,
            financial_data
        )

    st.markdown(
        "### 🤖 Finance AI Response"
    )

    st.info(answer)


# ============================================================
# FINANCIAL ALERT
# ============================================================

st.divider()

st.subheader("🚨 Financial Alert")
st.caption("Based on your overall financial profile, not the active spending filter.")

if net_savings < 0:

    st.error(
        f"⚠️ Your expenses are higher than your income. "
        f"You are overspending by ₹{abs(net_savings):,.2f}."
    )

elif savings_rate < 20:

    st.warning(
        f"⚠️ Your savings rate is {savings_rate:.2f}%. "
        "Consider reducing unnecessary expenses."
    )

else:

    st.success(
        f"✅ Good job! Your savings rate is "
        f"{savings_rate:.2f}%."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Finance Controller • "
    "Powered by Python, Pandas, Streamlit & Gemini AI • Buildathon Demo"
)
