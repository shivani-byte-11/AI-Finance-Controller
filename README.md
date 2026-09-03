# AI Finance Controller

An AI-powered personal finance dashboard that analyzes transactions, detects financial risks and anomalies, and provides actionable recommendations using data analysis and Gemini AI.

## 🚀 Overview

Managing financial transactions can make it difficult to identify overspending, unusual transactions, and potential financial risks.

**AI Finance Controller** converts raw transaction data into meaningful financial insights through automated analysis, risk scoring, anomaly detection, and AI-powered explanations.

The application supports both **demo data** and **custom CSV uploads**, allowing users to analyze their own transaction history.

## ✨ Key Features

### 📊 Financial Overview
- Total income
- Total expenses
- Net savings
- Savings rate
- Monthly financial trends

### 🛡️ Financial Risk Score
Calculates an overall financial risk score based on:
- Savings health
- Spending pressure
- Suspicious activity
- Large transaction exposure

The dashboard categorizes the result as:
- Low Risk
- Low-Moderate Risk
- Moderate Risk
- High Risk

### 🔎 Exception & Anomaly Detection
Automatically identifies potentially unusual financial activity, including:
- Duplicate transactions
- Unusually large expenses
- Category spending outliers

### 🤖 AI Financial Recommendations
Gemini AI analyzes financial metrics and provides:
- Personalized recommendations
- Spending optimization suggestions
- Risk explanations
- Actionable financial guidance

### 🚨 Suspicious Transaction Analyzer
Users can select flagged transactions and ask the AI:
- Why was this transaction flagged?
- What unusual signals were detected?
- What should be verified?

The system does not automatically claim that a transaction is fraudulent.

### 🎯 AI Financial Action Center
Prioritizes financial actions into:
- ACT NOW
- REVIEW
- OPTIMIZE

### 📁 Custom CSV Upload
Users can upload their own transaction data instead of relying only on demo data.

Required columns:

```text
transaction_id
date
transaction_type
category
merchant
amount
payment_method
