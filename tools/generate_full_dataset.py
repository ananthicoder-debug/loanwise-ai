"""Generate the Synthetic Indian Loan Eligibility and Repayment Dataset.

Borrower, historical-loan, and payment records are synthetic. Lender and
product rows contain public catalogue references and are kept separate from
synthetic outcomes. The script is deterministic so the generated relational
IDs can be regenerated for experiments.
"""

from __future__ import annotations

import argparse
import math
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260923
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "raw"

LOCATIONS = {
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli"],
    "Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode"],
    "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    "Telangana": ["Hyderabad", "Warangal"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Tirupati"],
    "Delhi": ["New Delhi"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara"],
    "Rajasthan": ["Jaipur", "Udaipur", "Jodhpur"],
    "West Bengal": ["Kolkata", "Siliguri"],
    "Uttar Pradesh": ["Lucknow", "Noida", "Kanpur", "Varanasi"],
    "Madhya Pradesh": ["Indore", "Bhopal", "Gwalior"],
    "Punjab": ["Ludhiana", "Amritsar", "Chandigarh"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat"],
    "Bihar": ["Patna", "Gaya"],
    "Odisha": ["Bhubaneswar", "Cuttack"],
}

LENDERS = [
    ("L001", "State Bank of India", "Bank", "Mumbai", "Maharashtra", "https://sbi.co.in/"),
    ("L002", "HDFC Bank", "Bank", "Mumbai", "Maharashtra", "https://www.hdfcbank.com/"),
    ("L003", "ICICI Bank", "Bank", "Mumbai", "Maharashtra", "https://www.icicibank.com/"),
    ("L004", "Axis Bank", "Bank", "Mumbai", "Maharashtra", "https://www.axisbank.com/"),
    ("L005", "Punjab National Bank", "Bank", "New Delhi", "Delhi", "https://www.pnbindia.in/"),
    ("L006", "Bank of Baroda", "Bank", "Vadodara", "Gujarat", "https://www.bankofbaroda.in/"),
    ("L007", "Canara Bank", "Bank", "Bengaluru", "Karnataka", "https://canarabank.com/"),
    ("L008", "Indian Bank", "Bank", "Chennai", "Tamil Nadu", "https://www.indianbank.in/"),
    ("L009", "Kotak Mahindra Bank", "Bank", "Mumbai", "Maharashtra", "https://www.kotak.com/"),
    ("L010", "IDFC FIRST Bank", "Bank", "Mumbai", "Maharashtra", "https://www.idfcfirstbank.com/"),
    ("L011", "Tata Capital", "NBFC", "Mumbai", "Maharashtra", "https://www.tatacapital.com/"),
    ("L012", "Bajaj Finance", "NBFC", "Pune", "Maharashtra", "https://www.bajajfinserv.in/"),
]

PRODUCT_TEMPLATES = [
    ("L001", "Personal Loan", "SBI Xpress Credit", 25000, 3500000, 11.0, 15.0, 6, 84),
    ("L001", "Vehicle Loan", "SBI Car Loan", 100000, 10000000, 8.7, 12.5, 12, 84),
    ("L001", "Education Loan", "SBI Student Loan", 10000, 2000000, 8.0, 11.5, 12, 180),
    ("L001", "Gold Loan", "SBI Personal Gold Loan", 20000, 2000000, 8.7, 12.0, 3, 36),
    ("L002", "Personal Loan", "HDFC Bank Personal Loan", 50000, 4000000, 10.5, 21.0, 12, 60),
    ("L002", "Home Loan", "HDFC Bank Home Loan", 500000, 100000000, 8.7, 13.2, 12, 360),
    ("L003", "Personal Loan", "ICICI Bank Personal Loan", 50000, 5000000, 10.8, 19.0, 6, 72),
    ("L003", "Vehicle Loan", "ICICI Bank Car Loan", 100000, 10000000, 8.5, 14.0, 12, 84),
    ("L003", "Education Loan", "ICICI Bank Education Loan", 10000, 2000000, 9.0, 13.5, 12, 180),
    ("L004", "Personal Loan", "Axis Bank Personal Loan", 50000, 4000000, 10.5, 22.0, 12, 84),
    ("L004", "Home Loan", "Axis Bank Home Loan", 500000, 50000000, 8.7, 13.5, 12, 360),
    ("L005", "Personal Loan", "PNB Personal Loan", 25000, 2000000, 10.4, 16.5, 12, 84),
    ("L006", "Home Loan", "Baroda Home Loan", 500000, 50000000, 8.4, 12.5, 12, 360),
    ("L007", "Vehicle Loan", "Canara Vehicle Loan", 50000, 10000000, 8.8, 14.0, 12, 84),
    ("L008", "Education Loan", "Indian Bank Education Loan", 10000, 3000000, 8.5, 12.5, 12, 180),
    ("L009", "Personal Loan", "Kotak Mahindra Bank Personal Loan", 50000, 3000000, 10.9, 24.0, 12, 60),
    ("L010", "Personal Loan", "IDFC FIRST Bank Personal Loan", 50000, 5000000, 10.5, 20.0, 6, 84),
    ("L011", "Business Loan", "Tata Capital Business Loan", 100000, 7500000, 12.0, 25.0, 12, 84),
    ("L012", "Consumer Durable Loan", "Bajaj Finserv Consumer Durable Loan", 5000, 500000, 0.0, 24.0, 3, 24),
    ("L012", "Personal Loan", "Bajaj Finserv Personal Loan", 20000, 4000000, 11.0, 30.0, 6, 96),
]


def lenders_frame() -> pd.DataFrame:
    return pd.DataFrame([
        {"Lender_ID": i, "Lender_Name": n, "Lender_Type": t, "Headquarters_City": c,
         "State": s, "Official_Website": u, "Verification_Status": "SOURCE_REVIEW_REQUIRED",
         "Dataset_Type": "Verified_Product_Catalogue"}
        for i, n, t, c, s, u in LENDERS
    ])


def products_frame() -> pd.DataFrame:
    rows = []
    for number, (lid, category, name, low, high, rate_low, rate_high, term_low, term_high) in enumerate(PRODUCT_TEMPLATES, 1):
        lender = next(row for row in LENDERS if row[0] == lid)
        rows.append({
            "Product_ID": f"P{number:03d}", "Lender_ID": lid, "Lender_Name": lender[1],
            "Lender_Type": lender[2], "Loan_Category": category, "Product_Name": name,
            "Product_Status": "Active", "Official_Product_URL": lender[5], "Source_Date": "2026-09-23",
            "Minimum_Age": "Not publicly specified", "Maximum_Age": "Not publicly specified",
            "Minimum_Income": "Not publicly specified", "Employment_Type_Requirement": "Not publicly specified",
            "Minimum_CIBIL_If_Publicly_Stated": "Not publicly specified", "Minimum_Loan_Amount": low,
            "Maximum_Loan_Amount": high, "Minimum_Tenure_Months": term_low, "Maximum_Tenure_Months": term_high,
            "Interest_Rate_Min": rate_low, "Interest_Rate_Max": rate_high,
            "Processing_Fee": "Not publicly specified", "Collateral_Required": "Not publicly specified",
            "Coapplicant_Allowed": "Not publicly specified", "Primary_Eligibility_Conditions": "See official lender source",
            "Documents_Required": "Not publicly specified", "Product_Benefits": "See official lender source",
            "Purpose": category, "Verification_Status": "SOURCE_REVIEW_REQUIRED",
            "Dataset_Type": "Verified_Product_Catalogue",
        })
    return pd.DataFrame(rows)


def make_borrowers(n: int, rng: np.random.Generator) -> pd.DataFrame:
    states = rng.choice(list(LOCATIONS), n)
    cities = [rng.choice(LOCATIONS[state]) for state in states]
    income = np.clip(rng.lognormal(math.log(52000), 0.75, n), 12000, 500000).round().astype(int)
    age = np.clip(rng.normal(36, 10, n), 18, 70).round().astype(int)
    dependents = np.clip(rng.poisson(1.8, n), 0, 8)
    cibil = np.clip(rng.normal(710, 75, n), 300, 900).round().astype(int)
    existing_loans = np.clip(rng.poisson(1.0, n), 0, 7)
    existing_emi = (income * rng.uniform(0.02, 0.42, n)).round().astype(int)
    debt = (income * 12 * rng.uniform(0.05, 1.1, n)).round().astype(int)
    late = np.clip(rng.poisson(1.0, n), 0, 15)
    missed = np.clip(rng.poisson(0.35, n), 0, 8)
    amount = np.clip(income * rng.uniform(2, 18, n), 20000, 10000000).round().astype(int)
    tenure = rng.choice([12, 18, 24, 36, 48, 60, 84, 120], n, p=[.05, .05, .12, .24, .2, .18, .1, .06])
    annual = income * 12
    dti = ((existing_emi + amount / tenure) / np.maximum(income, 1)).round(4)
    stability = rng.uniform(0.2, 1.0, n)
    eligibility_score = (cibil - 650) / 160 + annual / np.maximum(amount * 8, 1) - dti + stability * .4 + rng.normal(0, .45, n)
    affordability_score = 1.4 - dti * 2.2 - missed * .16 - late * .04 - dependents * .035 + rng.normal(0, .35, n)
    purposes = {"Personal Loan": ["Medical Emergency", "Wedding", "Home Renovation", "Debt Consolidation"], "Vehicle Loan": ["New Car", "Used Car", "Two Wheeler", "Electric Vehicle"], "Home Loan": ["Home Purchase", "Home Construction", "Home Renovation"], "Education Loan": ["Higher Education", "Professional Course", "Overseas Education"], "Business Loan": ["Working Capital", "Business Expansion", "Equipment Purchase"], "Gold Loan": ["Emergency Expense", "Education"], "Consumer Durable Loan": ["Consumer Purchase"]}
    categories = rng.choice(list(purposes), n, p=[.34, .18, .16, .1, .1, .07, .05])
    purpose = [rng.choice(purposes[c]) for c in categories]
    rows = []
    for i in range(n):
        coapp = rng.random() < .28
        rows.append({
            "Applicant_ID": f"A{i+1:06d}", "Application_ID": f"APP{i+1:06d}", "Age": int(age[i]), "Gender": rng.choice(["Female", "Male", "Other"], p=[.45, .54, .01]), "Marital_Status": rng.choice(["Single", "Married", "Divorced", "Widowed"], p=[.32, .6, .05, .03]), "State": states[i], "City": cities[i], "Education": rng.choice(["10th", "12th", "Diploma", "Graduate", "Postgraduate", "Professional Degree"], p=[.04, .08, .1, .45, .22, .11]), "Employment_Type": rng.choice(["Salaried", "Self-Employed", "Government Employee", "PSU Employee", "Defence Employee", "Private Employee", "Professional", "Business Owner"], p=[.3, .1, .08, .04, .02, .3, .06, .1]), "Employer_Category": rng.choice(["Private", "Government", "PSU", "Self-Employed"], p=[.55, .15, .08, .22]), "Years_of_Employment": round(float(np.clip((age[i] - 21) * rng.uniform(.35, .85), 0, 40)), 1), "Monthly_Income": int(income[i]), "Annual_Income": int(annual[i]), "Number_of_Dependents": int(dependents[i]), "Residence_Type": rng.choice(["Owned", "Rented", "Family Owned"], p=[.35, .5, .15]), "Residential_Assets_Value": int(rng.choice([0, rng.uniform(500000, 25000000)])), "Commercial_Assets_Value": int(rng.choice([0, 0, rng.uniform(0, 10000000)])), "Vehicle_Owned": rng.choice(["Yes", "No"], p=[.62, .38]), "Existing_Loan_Count": int(existing_loans[i]), "Existing_Emi_Amount": int(existing_emi[i]), "Outstanding_Debt": int(debt[i]), "Credit_Card_Outstanding": int(rng.uniform(0, income[i] * 1.5)), "Credit_Utilization_Ratio": round(float(rng.uniform(.05, .95)), 4), "CIBIL_Score": int(cibil[i]), "Previous_Loan_Count": int(np.clip(existing_loans[i] + rng.poisson(1), 0, 10)), "Previous_Loan_Repayment_Status": rng.choice(["Excellent", "Good", "Fair", "Delayed", "Poor"], p=[.2, .4, .25, .12, .03]), "Missed_Payment_Count": int(missed[i]), "Late_Payment_Count": int(late[i]), "Average_Days_Late": round(float(np.clip(rng.normal(7 + late[i] * 2, 5), 0, 90)), 1), "Banking_Relationship_Years": round(float(np.clip(rng.normal(6, 4), .2, 30)), 1), "Requested_Loan_Category": categories[i], "Requested_Loan_Amount": int(amount[i]), "Requested_Loan_Tenure": int(tenure[i]), "Loan_Purpose": purpose[i], "Coapplicant": "Yes" if coapp else "No", "Coapplicant_Income": int(rng.uniform(18000, 120000)) if coapp else "", "Debt_to_Income_Ratio": round(float(debt[i] / max(annual[i], 1)), 4), "EMI_to_Income_Ratio": round(float(dti[i]), 4), "Eligibility_Target": "Eligible" if eligibility_score[i] > 0 else "Not_Eligible", "Affordability_Target": "Manageable" if affordability_score[i] > 0 else "Not_Manageable", "Dataset_Type": "Synthetic_Borrower_Data"
        })
    return pd.DataFrame(rows)


def make_history(borrowers: pd.DataFrame, products: pd.DataFrame, n: int, rng: np.random.Generator):
    rows, payments = [], []
    for i in range(n):
        borrower = borrowers.iloc[int(rng.integers(0, len(borrowers)))]
        category_products = products[products.Loan_Category == borrower.Requested_Loan_Category]
        product = category_products.iloc[int(rng.integers(0, len(category_products)))]
        loan_id = f"HL{i+1:07d}"; amount = int(np.clip(rng.lognormal(math.log(350000), 1.0), product.Minimum_Loan_Amount, product.Maximum_Loan_Amount)); term = int(rng.choice([12, 24, 36, 48, 60, 84])); rate = float(rng.uniform(product.Interest_Rate_Min, product.Interest_Rate_Max)); emi = calculate_emi(amount, rate, term); start = date(2021, 1, 1) + timedelta(days=int(rng.integers(0, 1600))); miss_rate = min(.25, .015 + borrower.Missed_Payment_Count * .012); missed = int(rng.binomial(term, miss_rate)); late = int(rng.binomial(term - missed, min(.5, .04 + borrower.Late_Payment_Count * .01))); paid = max(0, min(term, int((date.today() - start).days / 30.4))); status = "Closed" if paid >= term else ("Overdue" if missed > 0 else "Active"); repayment = "Poor" if missed > 3 else ("Delayed" if missed or late > 2 else ("Fair" if late else "Good")); rows.append({"Historical_Loan_ID": loan_id, "Applicant_ID": borrower.Applicant_ID, "Product_ID": product.Product_ID, "Lender_Name": product.Lender_Name, "Loan_Category": product.Loan_Category, "Loan_Amount": amount, "Interest_Rate": rate, "Tenure_Months": term, "EMI_Amount": emi, "Start_Date": start.isoformat(), "Loan_Status": status, "Outstanding_Amount": round(max(0, amount - paid * emi * .72), 2), "Total_Installments": term, "Paid_Installments": paid, "Missed_Installments": missed, "Late_Installments": late, "Average_Days_Late": round(float(late * 6 + rng.uniform(0, 8)), 1), "Total_Late_Charges": round(late * emi * .02, 2), "Early_Closure": "Yes" if status == "Closed" and paid < term else "No", "Repayment_Status": repayment, "Dataset_Type": "Synthetic_Historical_Loan_Data"})
        for installment in range(1, min(term, 6) + 1):
            due = start + timedelta(days=30 * installment); event = rng.random(); state = "Missed" if event < miss_rate else ("Late" if event < miss_rate + .12 else "Paid"); paid_date = due + timedelta(days=int(rng.integers(1, 25))) if state == "Late" else (due if state == "Paid" else None); days = 0 if state == "Paid" else (int((paid_date - due).days) if paid_date else 0); payments.append({"Payment_ID": f"PAY{i+1:07d}_{installment:02d}", "Historical_Loan_ID": loan_id, "Applicant_ID": borrower.Applicant_ID, "Product_ID": product.Product_ID, "Installment_Number": installment, "Due_Date": due.isoformat(), "Due_Amount": emi, "Principal_Component": round(emi * .72, 2), "Interest_Component": round(emi * .28, 2), "Paid_Date": paid_date.isoformat() if paid_date else "", "Amount_Paid": emi if state != "Missed" else 0, "Payment_Status": state, "Days_Late": days, "Late_Charge": round(emi * .02 * math.ceil(max(days, 0) / 30), 2), "Dataset_Type": "Synthetic_Payment_History"})
    return pd.DataFrame(rows), pd.DataFrame(payments)


def calculate_emi(principal, rate, term):
    monthly = rate / 1200
    return round(principal / term if monthly == 0 else principal * monthly * (1 + monthly) ** term / ((1 + monthly) ** term - 1), 2)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, default=DEFAULT_OUT); parser.add_argument("--borrowers", type=int, default=5000); parser.add_argument("--historical-loans", type=int, default=10000); args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True); rng = np.random.default_rng(SEED); borrowers = make_borrowers(args.borrowers, rng); lenders = lenders_frame(); products = products_frame(); historical, payments = make_history(borrowers, products, args.historical_loans, rng); frames = {"borrowers": borrowers, "lenders": lenders, "loan_products": products, "historical_loans": historical, "installment_payments": payments}; stats = []
    for name, frame in frames.items():
        frame.to_csv(args.out / f"{name}.csv", index=False); frame.head(20).to_csv(args.out / f"{name}_preview.csv", index=False); stats.append(f"{name}: rows={len(frame)}, columns={len(frame.columns)}, duplicates={frame.duplicated().sum()}, missing_pct={frame.isna().mean().mean() * 100:.2f}")
    (args.out / "dataset_stats.txt").write_text("Synthetic Indian Loan Eligibility and Repayment Dataset\n" + "\n".join(stats) + "\n", encoding="utf-8")
    print("\n".join(stats))


if __name__ == "__main__":
    main()
