# AI Finance Controller

An AI-powered personal finance control system that analyzes transaction data, detects financial risks and anomalies, and provides actionable financial recommendations.

## 🚀 Overview

AI Finance Controller transforms raw transaction data into an intelligent financial health report.

Instead of simply displaying charts, the system answers:

- How financially healthy am I?
- Where is my money going?
- Are there unusual or suspicious transactions?
- What financial risks should I address?
- What should I do next?

## ✨ Key Features

### 📊 Financial Dashboard
- Total income
- Total expenses
- Net savings
- Savings rate
- Monthly financial trends
- Top spending categories
- Payment-method analysis
- Largest expenses

### 🛡️ Financial Risk Score

The application calculates a financial risk score from multiple signals:

- Savings health
- Spending pressure
- Suspicious activity
- Large transaction exposure

The result is classified as:

- 🟢 Low Risk
- 🟡 Low-Moderate Risk
- 🟠 Moderate Risk
- 🔴 High Risk

### 🔍 AI Detected Exceptions

Automatically identifies potentially important transaction anomalies such as:

- Duplicate transactions
- Unusually large expenses
- Category spending outliers
- Suspicious transaction patterns

### 🤖 AI Financial Recommendations

Gemini analyzes the user's financial data and provides personalized recommendations based on the detected risks and spending patterns.

### 🚨 Suspicious Transaction Analyzer

Users can select a flagged transaction and ask the AI:

- Why was this transaction flagged?
- What unusual signals were detected?
- What should be verified?

The system does not claim fraud without evidence.

### 🎯 AI Financial Action Center

Prioritizes financial actions using:

- ACT NOW
- REVIEW
- OPTIMIZE

This helps users focus on the most important financial decisions first.

### 💬 Ask Finance AI

Users can ask natural-language questions about their financial data and receive AI-generated explanations.

### 📥 Flexible Data Import

The application supports:

- Demo transaction data
- Custom CSV files
- PhonePe transaction statements

PhonePe Credit/Debit transactions are automatically normalized into Income/Expense categories.

## 🏗️ Architecture

```text
Transaction CSV / Statement
          ↓
   Data Import & Validation
          ↓
   Transaction Normalization
          ↓
 ┌────────┴─────────┐
 ↓                  ↓
Financial         Exception &
Analysis          Risk Detection
 ↓                  ↓
 └────────┬─────────┘
          ↓
      Gemini AI
          ↓
 ┌────────┼─────────────┐
 ↓        ↓             ↓
Insights Recommendations Actions
          ↓
     Streamlit Dashboard