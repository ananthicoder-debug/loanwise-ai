#!/usr/bin/env python3
"""
generate_synthetic_dataset.py
--------------------------------
Creates synthetic datasets for LoanAssist AI:
 - lenders.csv
 - loan_products.csv
 - borrowers.csv
 - historical_loans.csv
 - installment_payments.csv

Produces a preview (20 rows) and full datasets (sizes defined below).
This script uses only Python stdlib + pandas/numpy which are already
present in the project's requirements. It is deterministic by default
(seeded) so results are reproducible.

Usage:
  python tools/generate_synthetic_dataset.py --preview
  python tools/generate_synthetic_dataset.py --full

"""
import argparse
import math
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT_DIR, exist_ok=True)


def make_lenders():
    # Verified set of Indian lenders with official websites
    lenders = [
        ("L001", "State Bank of India", "Bank", "Mumbai", "Maharashtra", "https://sbi.co.in"),
        ("L002", "HDFC Bank", "Bank", "Mumbai", "Maharashtra", "https://www.hdfcbank.com"),
        ("L003", "ICICI Bank", "Bank", "Mumbai", "Maharashtra", "https://www.icicibank.com"),
        ("L004", "Axis Bank", "Bank", "Mumbai", "Maharashtra", "https://www.axisbank.com"),
        ("L005", "Punjab National Bank", "Bank", "New Delhi", "Delhi", "https://www.pnbindia.in"),
        ("L006", "Bank of Baroda", "Bank", "Vadodara", "Gujarat", "https://www.bankofbaroda.in"),
        ("L007", "Canara Bank", "Bank", "Bengaluru", "Karnataka", "https://www.canarabank.com"),
        ("L008", "Kotak Mahindra Bank", "Bank", "Mumbai", "Maharashtra", "https://www.kotak.com"),
        ("L009", "IDFC FIRST Bank", "Bank", "Mumbai", "Maharashtra", "https://www.idfcfirstbank.com"),
        ("L010", "IndusInd Bank", "Bank", "Mumbai", "Maharashtra", "https://indusind.com"),
        ("L011", "Bajaj Finance", "NBFC", "Pune", "Maharashtra", "https://www.bajajfinserv.in"),
        ("L012", "Tata Capital", "NBFC", "Mumbai", "Maharashtra", "https://www.tatacapital.com"),
    ]
    rows = []
    for lid, name, ltype, city, state, url in lenders:
        rows.append({
            "Lender_ID": lid,
            "Lender_Name": name,
            "Lender_Type": ltype,
            "Headquarters_City": city,
            "State": state,
            "Official_Website": url,
            "Verification_Status": "Verified",
            "Dataset_Type": "Verified_Product_Catalogue",
        })
    return pd.DataFrame(rows)


def make_loan_products(lenders_df, target_count=60, seed=42):
    random.seed(seed)
    products = []
    categories = ["Personal Loan", "Home Loan", "Vehicle Loan", "Education Loan", "Gold Loan", "Business Loan", "Consumer Durable Loan"]

    for _, lender in lenders_df.iterrows():
        lid = lender.Lender_ID
        lname = lender.Lender_Name
        for cat in categories:
            if random.random() < 0.7:
                pid = f"{lid}_{cat.split()[0][:3].upper()}_{random.randint(100,999)}"
                name = f"{lname} {cat}"
                min_amount = 10000 if cat == "Personal Loan" else (50000 if cat == "Vehicle Loan" else 5000)
                max_amount = 2000000 if cat == "Home Loan" else (200000 if cat == "Business Loan" else 1000000)
                min_tenure = 6 if cat == "Personal Loan" else 12
                max_tenure = 60 if cat == "Personal Loan" else (240 if cat == "Home Loan" else 84)
                rate_min = round(random.uniform(8.9, 11.5), 2) if cat in ("Home Loan",) else round(random.uniform(10.5, 24.0), 2)
                rate_max = round(rate_min + random.uniform(0.5, 3.5), 2)
                processing_fee = "Not publicly specified"
                collateral = "Yes" if cat in ("Home Loan", "Business Loan") else "No"
                coapp = "Yes" if cat in ("Home Loan", "Vehicle Loan") else "Depends"
                min_cibil = "Not publicly specified"
                min_income = 25000 if cat == "Personal Loan" else (50000 if cat == "Home Loan" else 20000)

                products.append({
                    "Product_ID": pid,
                    "Lender_ID": lid,
                    "Lender_Name": lname,
                    "Lender_Type": lender.Lender_Type,
                    "Loan_Category": cat,
                    "Product_Name": name,
                    "Product_Status": "Active",
                    "Official_Product_URL": lender.Official_Website,
                    "Source_Date": datetime.utcnow().date().isoformat(),
                    "Minimum_Age": 18,
                    "Maximum_Age": 70,
                    "Minimum_Income": min_income,
                    "Employment_Type_Requirement": "Not publicly specified",
                    "Minimum_CIBIL_If_Publicly_Stated": min_cibil,
                    "Minimum_Loan_Amount": min_amount,
                    "Maximum_Loan_Amount": max_amount,
                    "Minimum_Tenure_Months": min_tenure,
                    "Maximum_Tenure_Months": max_tenure,
                    "Interest_Rate_Min": rate_min,
                    "Interest_Rate_Max": rate_max,
                    "Processing_Fee": processing_fee,
                    "Collateral_Required": collateral,
                    "Coapplicant_Allowed": coapp,
                    "Primary_Eligibility_Conditions": "Not publicly specified",
                    "Documents_Required": "Identity, Address, Income proof",
                    "Product_Benefits": "Not publicly specified",
                    "Purpose": cat,
                    "Verification_Status": "Verified",
                    "Dataset_Type": "Verified_Product_Catalogue",
                })
    df = pd.DataFrame(products)
    if len(df) > target_count:
        df = df.sample(n=target_count, random_state=seed).reset_index(drop=True)
    return df


def rnd_name(gender=None):
    first_male = ["Arjun","Ravi","Karthik","Suresh","Anand","Vikram","Rahul","Amit","Siddharth","Karan"]
    first_female = ["Priya","Sneha","Divya","Meena","Lakshmi","Ananya","Pooja","Shruti","Anita","Rekha"]
    last = ["Sharma","Iyer","Reddy","Kumar","Menon","Patel","Singh","Gupta","Verma","Nair"]
    if gender == "Male":
        return f"{random.choice(first_male)} {random.choice(last)}"
    elif gender == "Female":
        return f"{random.choice(first_female)} {random.choice(last)}"
    else:
        return f"{random.choice(first_male+first_female)} {random.choice(last)}"


def make_borrowers(n=5000, seed=123):
    random.seed(seed)
    np.random.seed(seed)
    states_cities = {
        "Tamil Nadu": ["Chennai","Coimbatore","Madurai","Tiruchirappalli","Salem","Tirunelveli"],
        "Karnataka": ["Bengaluru","Mysuru","Mangalore","Hubli"],
        "Kerala": ["Kochi","Thiruvananthapuram","Kozhikode","Kollam"],
        "Maharashtra": ["Mumbai","Pune","Nagpur","Nashik"],
        "Telangana": ["Hyderabad","Warangal"],
        "Andhra Pradesh": ["Visakhapatnam","Vijayawada"],
        "Delhi": ["New Delhi"],
        "Gujarat": ["Ahmedabad","Surat"],
        "Rajasthan": ["Jaipur","Jodhpur"],
        "West Bengal": ["Kolkata","Siliguri"],
        "Uttar Pradesh": ["Lucknow","Kanpur","Noida"],
        "Punjab": ["Chandigarh","Ludhiana"],
        "Haryana": ["Gurgaon","Faridabad"],
        "Bihar": ["Patna"],
        "Odisha": ["Bhubaneswar"],
        "Madhya Pradesh": ["Bhopal","Indore"]
    }
    education = ["10th","12th","Diploma","Graduate","Postgraduate","Professional Degree"]
    employment_types = ["Salaried","Self-Employed","Government Employee","PSU Employee","Defence Employee","Private Employee","Professional","Business Owner"]
    residence_types = ["Owned","Rented","Family","Company Provided"]
    loan_categories = ["Personal Loan","Home Loan","Vehicle Loan","Education Loan","Gold Loan","Business Loan","Consumer Durable Loan"]

    rows = []
    for i in range(1, n+1):
        applicant_id = f"APP{str(i).zfill(6)}"
        application_id = f"APL{str(i).zfill(6)}"
        age = int(np.clip(np.random.normal(35, 9), 18, 70))
        gender = random.choices(["Male","Female","Other"], weights=[0.55,0.43,0.02])[0]
        marital = random.choices(["Married","Single","Divorced"], weights=[0.55,0.4,0.05])[0]
        state = random.choice(list(states_cities.keys()))
        city = random.choice(states_cities[state])
        edu = random.choices(education, weights=[0.05,0.1,0.15,0.45,0.18,0.07])[0]
        emp = random.choices(employment_types, weights=[0.45,0.18,0.06,0.02,0.01,0.18,0.05,0.05])[0]
        employer_cat = random.choice(["Private","MNC","Small Business","Government","PSU","Self"])
        years_employed = int(max(0, np.random.poisson(5))) if emp != "Student" else 0
        monthly_income = int(np.round(np.exp(np.random.normal(np.log(40000), 0.9))))
        monthly_income = int(np.clip(monthly_income, 12000, 500000))
        annual_income = monthly_income * 12
        dependents = int(np.random.poisson(1))
        residence = random.choice(residence_types)
        residential_assets = int(np.clip(monthly_income * random.uniform(10,60), 0, 50000000))
        commercial_assets = int(np.clip(monthly_income * random.uniform(0,80) if random.random()<0.12 else 0, 0, 200000000))
        vehicle = random.choice(["Car","Two Wheeler","None"]) if random.random() < 0.6 else "None"
        existing_loan_count = int(np.random.poisson(0.6))
        existing_emi = int(existing_loan_count * monthly_income * random.uniform(0.05,0.3))
        outstanding_debt = int(existing_loan_count * monthly_income * random.uniform(1,12))
        cc_outstanding = int(max(0, np.random.normal(5000, 15000)))
        util = round(min(1.0, cc_outstanding / max(1, monthly_income*0.5)), 2)
        cibil = int(np.clip(int(np.random.normal(700, 70)), 300, 900))
        prev_loan_count = int(np.random.poisson(1.0))
        prev_repayment = random.choices(["Excellent","Good","Fair","Delayed","Poor"], weights=[0.25,0.4,0.2,0.1,0.05])[0]
        missed = int(np.random.poisson(0.4))
        late = int(np.random.poisson(0.6))
        avg_days_late = int(np.clip(np.random.normal(5+late*3, 4), 0, 90))
        banking_years = int(np.clip(np.random.exponential(3), 0, 40))

        req_cat = random.choices(loan_categories, weights=[0.35,0.15,0.18,0.05,0.02,0.15,0.1])[0]
        if req_cat == "Personal Loan":
            req_amount = int(np.clip(int(np.random.normal(monthly_income*6, monthly_income*4)), 20000, 1000000))
            tenure = int(np.clip(int(np.random.normal(36, 18)), 6, 84))
            purpose = random.choice(["Medical Emergency","Wedding","Travel","Home Renovation","Education","Debt Consolidation","Emergency Expense","Consumer Purchase"])
        elif req_cat == "Home Loan":
            req_amount = int(np.clip(int(np.random.normal(8000000, 3000000)), 200000, 20000000))
            tenure = int(np.clip(int(np.random.normal(180, 60)), 60, 360))
            purpose = random.choice(["Home Purchase","Home Construction","Home Renovation"])
        elif req_cat == "Vehicle Loan":
            req_amount = int(np.clip(int(np.random.normal(600000, 300000)), 30000, 5000000))
            tenure = int(np.clip(int(np.random.normal(60, 24)), 12, 120))
            purpose = random.choice(["New Car","Used Car","Two Wheeler","Electric Vehicle"])
        elif req_cat == "Education Loan":
            req_amount = int(np.clip(int(np.random.normal(300000,150000)), 20000, 5000000))
            tenure = int(np.clip(int(np.random.normal(84, 36)), 12, 180))
            purpose = random.choice(["Higher Education","Professional Course","Overseas Education"]) 
        elif req_cat == "Business Loan":
            req_amount = int(np.clip(int(np.random.normal(1000000,800000)), 50000, 10000000))
            tenure = int(np.clip(int(np.random.normal(60,30)), 12, 120))
            purpose = random.choice(["Working Capital","Business Expansion","Equipment Purchase"]) 
        elif req_cat == "Gold Loan":
            req_amount = int(np.clip(int(np.random.normal(100000,50000)), 5000, 2000000))
            tenure = int(np.clip(int(np.random.normal(12,6)), 1, 36))
            purpose = "Not specified"
        else:
            req_amount = int(np.clip(int(np.random.normal(40000,20000)), 5000, 300000))
            tenure = int(np.clip(int(np.random.normal(24,12)), 6, 60))
            purpose = "Consumer Purchase"

        coapp = "Yes" if random.random() < 0.12 else "No"
        coapp_income = int(np.random.normal(30000,20000)) if coapp == "Yes" else None

        dti = round((existing_emi + outstanding_debt/12) / max(1, annual_income), 2)
        emi_to_income = round((existing_emi + (req_amount / max(1, tenure))) / max(1, monthly_income), 2)

        score = 0
        score += (cibil - 300) / 600
        score += min(1.0, monthly_income / max(1, req_amount/ (tenure/12 + 0.1))) * 0.7
        score -= min(1.0, existing_emi / max(1, monthly_income)) * 0.8
        score += min(1.0, years_employed / 10) * 0.3
        score -= max(0, (dependents - 1)) * 0.05
        elig_prob = 1 / (1 + math.exp(-5*(score-0.9)))
        eligibility = "Eligible" if random.random() < elig_prob else "Not_Eligible"

        proposed_emi = int(round((req_amount * 0.01 * (1+random.uniform(0,0.02))) / (1 if tenure==0 else tenure)))
        aff_score = 0
        aff_score += monthly_income / (proposed_emi*12 + 1)
        aff_score -= (missed * 0.5 + late * 0.3)
        aff_score -= emi_to_income * 2
        aff_prob = 1 / (1 + math.exp(-0.0001*(aff_score*1000 - 100)))
        affordability = "Manageable" if random.random() < aff_prob else "Not_Manageable"

        rows.append({
            "Applicant_ID": applicant_id,
            "Application_ID": application_id,
            "Full_Name": rnd_name(gender),
            "Age": age,
            "Gender": gender,
            "Marital_Status": marital,
            "State": state,
            "City": city,
            "Education": edu,
            "Employment_Type": emp,
            "Employer_Category": employer_cat,
            "Years_of_Employment": years_employed,
            "Monthly_Income": monthly_income,
            "Annual_Income": annual_income,
            "Number_of_Dependents": dependents,
            "Residence_Type": residence,
            "Residential_Assets_Value": residential_assets,
            "Commercial_Assets_Value": commercial_assets,
            "Vehicle_Owned": vehicle,
            "Existing_Loan_Count": existing_loan_count,
            "Existing_Emi_Amount": existing_emi,
            "Outstanding_Debt": outstanding_debt,
            "Credit_Card_Outstanding": cc_outstanding,
            "Credit_Utilization_Ratio": util,
            "CIBIL_Score": cibil,
            "Previous_Loan_Count": prev_loan_count,
            "Previous_Loan_Repayment_Status": prev_repayment,
            "Missed_Payment_Count": missed,
            "Late_Payment_Count": late,
            "Average_Days_Late": avg_days_late,
            "Banking_Relationship_Years": banking_years,
            "Requested_Loan_Category": req_cat,
            "Requested_Loan_Amount": req_amount,
            "Requested_Loan_Tenure": tenure,
            "Loan_Purpose": purpose,
            "Coapplicant": coapp,
            "Coapplicant_Income": coapp_income,
            "Debt_to_Income_Ratio": dti,
            "EMI_to_Income_Ratio": emi_to_income,
            "Eligibility_Target": eligibility,
            "Affordability_Target": affordability,
            "Dataset_Type": "Synthetic_Borrower_Data",
        })
    return pd.DataFrame(rows)


def emi_amount(principal, annual_rate_percent, tenure_months):
    r = annual_rate_percent / 12 / 100
    if tenure_months <= 0:
        return 0
    if r == 0:
        return principal / tenure_months
    factor = (1 + r) ** tenure_months
    return principal * r * factor / (factor - 1)


def make_historical_loans(borrowers_df, products_df, n_loans=10000, seed=2026):
    random.seed(seed)
    rows = []
    for i in range(1, n_loans+1):
        hid = f"HL{str(i).zfill(7)}"
        applicant = borrowers_df.sample(n=1, random_state=seed + i).iloc[0]
        product = products_df.sample(n=1, random_state=seed + i*3).iloc[0]
        loan_amount = int(min(product.Maximum_Loan_Amount, max(product.Minimum_Loan_Amount, int(np.random.normal(applicant.Monthly_Income*12*2, 200000)))))
        rate = round(random.uniform(product.Interest_Rate_Min, product.Interest_Rate_Max), 2)
        tenure = int(min(product.Maximum_Tenure_Months, max(product.Minimum_Tenure_Months, int(abs(int(np.random.normal(product.Minimum_Tenure_Months+12, 36)))))))
        emi = int(round(emi_amount(loan_amount, rate, tenure)))
        start_date = datetime.utcnow().date() - timedelta(days=random.randint(30, 3650))
        status = random.choices(["Active","Closed","Overdue","Settled"], weights=[0.45,0.35,0.1,0.1])[0]
        outstanding = int(max(0, loan_amount - emi * random.randint(1, max(1, tenure-1)))) if status != "Closed" else 0
        total_installments = tenure
        paid_installments = random.randint(0, total_installments)
        missed = max(0, int(np.random.poisson(1)))
        late = max(0, int(np.random.poisson(1)))
        avg_days = int(np.clip(np.random.normal(5+late*3, 4), 0, 90))
        late_charges = int(missed * emi * random.uniform(0.01, 0.05))
        early_closure = random.random() < 0.02
        repayment_status = random.choices(["Excellent","Good","Fair","Delayed","Poor"], weights=[0.25,0.4,0.2,0.1,0.05])[0]

        rows.append({
            "Historical_Loan_ID": hid,
            "Applicant_ID": applicant.Applicant_ID,
            "Product_ID": product.Product_ID,
            "Lender_Name": product.Lender_Name,
            "Loan_Category": product.Loan_Category,
            "Loan_Amount": loan_amount,
            "Interest_Rate": rate,
            "Tenure_Months": tenure,
            "EMI_Amount": emi,
            "Start_Date": start_date.isoformat(),
            "Loan_Status": status,
            "Outstanding_Amount": outstanding,
            "Total_Installments": total_installments,
            "Paid_Installments": paid_installments,
            "Missed_Installments": missed,
            "Late_Installments": late,
            "Average_Days_Late": avg_days,
            "Total_Late_Charges": int(late_charges),
            "Early_Closure": "Yes" if early_closure else "No",
            "Repayment_Status": repayment_status,
            "Dataset_Type": "Synthetic_Historical_Loan_Data",
        })
    return pd.DataFrame(rows)


def make_installment_payments(historical_loans_df, target_min_records=30000, seed=3030):
    random.seed(seed)
    rows = []
    pid = 1
    for _, loan in historical_loans_df.iterrows():
        installments = int(loan.Total_Installments)
        paid = int(loan.Paid_Installments)
        emi = int(loan.EMI_Amount)
        start = datetime.fromisoformat(loan.Start_Date)
        for inst in range(1, installments+1):
            due_date = (start + timedelta(days=30*(inst-1))).date()
            if inst <= paid:
                status = "Paid"
                paid_date = due_date + timedelta(days=random.randint(0,5))
                amt_paid = emi
                days_late = (paid_date - due_date).days
            else:
                r = random.random()
                if r < 0.1:
                    status = "Missed"
                    paid_date = ""
                    amt_paid = 0
                    days_late = ""
                elif r < 0.3:
                    status = "Late"
                    paid_date = due_date + timedelta(days=random.randint(6,40))
                    amt_paid = emi
                    days_late = (paid_date - due_date).days
                else:
                    status = "Pending"
                    paid_date = ""
                    amt_paid = 0
                    days_late = ""

            late_charge = int(max(0, days_late) * emi * 0.001) if isinstance(days_late, int) else 0
            rows.append({
                "Payment_ID": f"PM{str(pid).zfill(8)}",
                "Historical_Loan_ID": loan.Historical_Loan_ID,
                "Applicant_ID": loan.Applicant_ID,
                "Product_ID": loan.Product_ID,
                "Installment_Number": inst,
                "Due_Date": due_date.isoformat(),
                "Due_Amount": emi,
                "Principal_Component": int(emi * 0.8),
                "Interest_Component": int(emi * 0.2),
                "Paid_Date": paid_date if paid_date=="" else paid_date.isoformat(),
                "Amount_Paid": amt_paid,
                "Payment_Status": status,
                "Days_Late": days_late if days_late!="" else "",
                "Late_Charge": late_charge,
                "Dataset_Type": "Synthetic_Payment_History",
            })
            pid += 1
    return pd.DataFrame(rows)


def write_preview_and_full(lenders_df, products_df, borrowers_df, hist_df, payments_df):
    lenders_df.head(20).to_csv(os.path.join(OUT_DIR, "lenders_preview.csv"), index=False)
    products_df.head(20).to_csv(os.path.join(OUT_DIR, "loan_products_preview.csv"), index=False)
    borrowers_df.head(20).to_csv(os.path.join(OUT_DIR, "borrowers_preview.csv"), index=False)
    hist_df.head(20).to_csv(os.path.join(OUT_DIR, "historical_loans_preview.csv"), index=False)
    payments_df.head(20).to_csv(os.path.join(OUT_DIR, "installment_payments_preview.csv"), index=False)

    lenders_df.to_csv(os.path.join(OUT_DIR, "lenders.csv"), index=False)
    products_df.to_csv(os.path.join(OUT_DIR, "loan_products.csv"), index=False)
    borrowers_df.to_csv(os.path.join(OUT_DIR, "borrowers.csv"), index=False)
    hist_df.to_csv(os.path.join(OUT_DIR, "historical_loans.csv"), index=False)
    payments_df.to_csv(os.path.join(OUT_DIR, "installment_payments.csv"), index=False)


def stats_and_checks(borrowers_df, products_df, hist_df, payments_df):
    stats = {}
    stats["borrowers_rows"] = len(borrowers_df)
    stats["borrowers_cols"] = borrowers_df.shape[1]
    stats["borrowers_missing_pct"] = borrowers_df.isna().mean().mean() * 100
    stats["duplicate_applicants"] = borrowers_df.Applicant_ID.duplicated().sum()
    stats["unique_borrowers"] = borrowers_df.Applicant_ID.nunique()
    stats["unique_lenders"] = products_df.Lender_ID.nunique()
    stats["unique_products"] = products_df.Product_ID.nunique()
    stats["eligibility_dist"] = borrowers_df.Eligibility_Target.value_counts().to_dict()
    stats["affordability_dist"] = borrowers_df.Affordability_Target.value_counts().to_dict()
    stats["loan_category_dist"] = borrowers_df.Requested_Loan_Category.value_counts().to_dict()
    stats["employment_dist"] = borrowers_df.Employment_Type.value_counts().to_dict()
    stats["avg_income"] = borrowers_df.Monthly_Income.mean()
    stats["median_income"] = borrowers_df.Monthly_Income.median()
    stats["avg_cibil"] = borrowers_df.CIBIL_Score.mean()
    stats["avg_loan_amount"] = hist_df.Loan_Amount.mean()
    stats["avg_emi"] = hist_df.EMI_Amount.mean()
    stats["avg_dti"] = borrowers_df.Debt_to_Income_Ratio.mean()
    return stats


def main(preview=False, full=False):
    lenders_df = make_lenders()
    products_df = make_loan_products(lenders_df, target_count=70)
    borrowers_df = make_borrowers(n=5000)
    hist_df = make_historical_loans(borrowers_df, products_df, n_loans=10000)
    payments_df = make_installment_payments(hist_df, target_min_records=30000)

    write_preview_and_full(lenders_df, products_df, borrowers_df, hist_df, payments_df)

    stats = stats_and_checks(borrowers_df, products_df, hist_df, payments_df)
    stats_path = os.path.join(OUT_DIR, "dataset_stats.txt")
    with open(stats_path, "w") as f:
        for k, v in stats.items():
            f.write(f"{k}: {v}\n")

    print("Generated datasets in:", OUT_DIR)
    print("Preview files and full CSVs written. Stats saved to dataset_stats.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    main(preview=args.preview, full=args.full)
