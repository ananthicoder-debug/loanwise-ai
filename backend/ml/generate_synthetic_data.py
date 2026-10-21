"""
ml/generate_synthetic_data.py
-------------------------------
Generates SYNTHETIC training datasets for Model 1 and Model 2.
- 2,000 borrower/application records with logically consistent Indian financial values
- Uses RANDOM_SEED = 42 for reproducibility
- Outputs:
    backend/data/raw/eligibility_dataset.csv   (Model 1 training)
    backend/data/raw/affordability_dataset.csv (Model 2 training)

IMPORTANT: This is SYNTHETIC data generated for ML training purposes.
It does NOT contain real customer information.

Run: python ml/generate_synthetic_data.py  (from backend/)
"""

import os
import sys
import random
import math
import numpy as np
import pandas as pd
from pathlib import Path

RANDOM_SEED = 42
N_RECORDS   = 2000
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ?? Indian demographic constants ???????????????????????????????
STATES = ["Maharashtra","Tamil Nadu","Karnataka","Delhi","Telangana","Gujarat",
          "Rajasthan","Uttar Pradesh","West Bengal","Kerala","Madhya Pradesh",
          "Punjab","Haryana","Bihar","Andhra Pradesh"]

CITIES = {"Maharashtra":["Mumbai","Pune","Nagpur"],"Tamil Nadu":["Chennai","Coimbatore","Madurai"],
          "Karnataka":["Bengaluru","Mysuru","Hubballi"],"Delhi":["New Delhi","Noida","Gurugram"],
          "Telangana":["Hyderabad","Warangal"],"Gujarat":["Ahmedabad","Surat","Vadodara"],
          "Rajasthan":["Jaipur","Jodhpur"],"Uttar Pradesh":["Lucknow","Kanpur","Agra"],
          "West Bengal":["Kolkata","Howrah"],"Kerala":["Thiruvananthapuram","Kochi","Kozhikode"],
          "Madhya Pradesh":["Bhopal","Indore"],"Punjab":["Chandigarh","Ludhiana","Amritsar"],
          "Haryana":["Gurugram","Faridabad","Ambala"],"Bihar":["Patna","Gaya"],
          "Andhra Pradesh":["Visakhapatnam","Vijayawada"]}

EMPLOYMENT_TYPES = ["Salaried","Self-Employed","Business Owner","Government Employee",
                    "PSU Employee","Professional","Private Employee"]
EDUCATION_LEVELS = ["Post Graduate","Graduate","Graduate","12th","Graduate","Post Graduate"]
LOAN_CATEGORIES  = ["Personal Loan","Home Loan","Vehicle Loan","Education Loan",
                    "Business Loan","Gold Loan","Consumer Durable Loan"]
PURPOSES = {"Personal Loan":["Medical Emergency","Debt Consolidation","Home Renovation","Travel","Wedding"],
            "Home Loan":["Home Purchase","Home Construction","Home Renovation"],
            "Vehicle Loan":["New Car","Used Car","Two Wheeler"],
            "Education Loan":["Undergraduate","Postgraduate","Professional Course"],
            "Business Loan":["Working Capital","Business Expansion","Equipment Purchase"],
            "Gold Loan":["Emergency","Business","Medical"],
            "Consumer Durable Loan":["Electronics","Appliances","Furniture"]}

INCOME_BY_EMP = {
    "Government Employee": (40000, 200000),
    "PSU Employee":        (35000, 180000),
    "Salaried":            (20000, 300000),
    "Private Employee":    (18000, 250000),
    "Professional":        (50000, 500000),
    "Business Owner":      (30000, 400000),
    "Self-Employed":       (15000, 200000),
}
LOAN_AMOUNT_RANGES = {
    "Personal Loan":       (50000, 1500000),
    "Home Loan":           (1000000, 15000000),
    "Vehicle Loan":        (100000, 2000000),
    "Education Loan":      (100000, 2000000),
    "Business Loan":       (200000, 5000000),
    "Gold Loan":           (20000, 500000),
    "Consumer Durable Loan":(10000, 200000),
}
TENURE_RANGES = {
    "Personal Loan":       (12, 60),
    "Home Loan":           (60, 240),
    "Vehicle Loan":        (12, 84),
    "Education Loan":      (12, 84),
    "Business Loan":       (12, 84),
    "Gold Loan":           (6, 24),
    "Consumer Durable Loan":(6, 36),
}

# ?? Helper functions ????????????????????????????????????????????
def clamp(val, lo, hi): return max(lo, min(hi, val))

def emi_calc(P, r_annual_pct, n_months):
    r = (r_annual_pct / 12) / 100
    if r == 0: return round(P / n_months, 2)
    return round(P * r * (1+r)**n_months / ((1+r)**n_months - 1), 2)

# ?? Record generator ?????????????????????????????????????????????
def generate_record(idx):
    # Demographics
    age = int(np.random.normal(35, 10))
    age = clamp(age, 21, 62)

    state = random.choice(STATES)
    city  = random.choice(CITIES[state])
    emp_type = random.choice(EMPLOYMENT_TYPES)
    education = random.choice(EDUCATION_LEVELS)

    years_emp = clamp(np.random.exponential(6), 0.5, min(age - 20, 35))
    years_emp = round(years_emp, 1)

    # Income: base from employment type + age effect
    inc_lo, inc_hi = INCOME_BY_EMP[emp_type]
    age_factor = 1 + (age - 25) * 0.015
    base_income = random.uniform(inc_lo, inc_hi) * age_factor
    monthly_income = round(clamp(base_income, 12000, 500000), -2)
    annual_income  = monthly_income * 12

    # Dependents
    dependents = int(clamp(np.random.poisson(1.2), 0, 5))

    # CIBIL: correlated with employment stability, age, dependents
    base_cibil = 620 + (years_emp * 3) - (dependents * 5)
    if emp_type in ["Government Employee","PSU Employee"]: base_cibil += 30
    if emp_type in ["Self-Employed","Business Owner"]:     base_cibil -= 20
    cibil = int(clamp(np.random.normal(base_cibil, 60), 300, 900))

    # Existing obligations
    existing_loans = int(clamp(np.random.poisson(0.8), 0, 5))
    existing_emi   = round(monthly_income * random.uniform(0, 0.35) * existing_loans, -2)
    outstanding_debt = existing_emi * random.randint(6, 30) if existing_loans > 0 else 0

    # Payment history
    prev_loans = existing_loans + int(np.random.poisson(1))
    missed_payments = int(np.random.poisson(0.3 if cibil >= 700 else 1.2))
    late_payments   = int(np.random.poisson(0.5 if cibil >= 700 else 2.0))
    avg_days_late   = round(max(0, np.random.normal(3, 5) if late_payments > 0 else 0), 1)

    # Credit card
    cc_outstanding    = round(monthly_income * random.uniform(0, 0.2), -2) if random.random() < 0.5 else 0
    credit_utilization = round(clamp(cc_outstanding / (monthly_income * 0.3 + 1), 0, 1), 2)

    # Asset values
    res_asset = round(monthly_income * random.uniform(0, 60), -4) if random.random() < 0.4 else 0
    com_asset = round(monthly_income * random.uniform(0, 40), -4) if random.random() < 0.2 else 0
    vehicle   = random.choice(["None","Two Wheeler","Car"])

    # Loan request
    loan_category = random.choice(LOAN_CATEGORIES)
    amt_lo, amt_hi = LOAN_AMOUNT_RANGES[loan_category]
    max_eligible = monthly_income * 60  # rough affordability cap
    requested_amount = round(clamp(random.uniform(amt_lo, min(amt_hi, max_eligible)), amt_lo, amt_hi), -3)
    ten_lo, ten_hi = TENURE_RANGES[loan_category]
    tenure = int(random.choice(range(ten_lo, ten_hi+1, 6)))
    purpose = random.choice(PURPOSES[loan_category])

    # Coapplicant
    coapplicant = random.random() < 0.25
    coapplicant_income = round(monthly_income * random.uniform(0.3, 0.8), -2) if coapplicant else 0

    # Derived ratios
    dti = round(outstanding_debt / (annual_income + 1), 4)
    test_rate = 12.0
    proposed_emi = emi_calc(requested_amount, test_rate, tenure)
    eti = round((existing_emi + proposed_emi) / (monthly_income + 1), 4)

    # ?? Eligibility target (Model 1) ??????????????????????????????
    eligibility_score = 0
    eligibility_score += 25 if cibil >= 750 else (15 if cibil >= 700 else (5 if cibil >= 650 else -10))
    eligibility_score += 20 if annual_income >= requested_amount * 0.25 else (10 if annual_income >= requested_amount * 0.15 else -5)
    eligibility_score += 10 if years_emp >= 3 else (5 if years_emp >= 1 else -5)
    eligibility_score -= existing_loans * 4
    eligibility_score -= missed_payments * 8
    eligibility_score -= max(0, dti - 0.3) * 30
    if coapplicant: eligibility_score += 8
    eligibility_score += np.random.normal(0, 5)

    eligibility_prob = 1 / (1 + math.exp(-eligibility_score / 20))
    eligibility_target = "Eligible" if eligibility_prob > 0.5 else "Not_Eligible"

    # ?? Affordability target (Model 2) ????????????????????????????
    afford_score = 0.9
    afford_score -= eti * 1.5
    afford_score -= (outstanding_debt / (annual_income + 1)) * 0.5
    afford_score -= missed_payments * 0.08
    afford_score -= late_payments * 0.03
    afford_score += (cibil - 650) / 1000
    afford_score += np.random.normal(0, 0.05)
    afford_score = clamp(afford_score, 0.01, 0.99)
    affordability_target = "Manageable" if afford_score > 0.5 else "Not_Manageable"

    return {
        "Applicant_ID":         f"APP{idx:06d}",
        "Application_ID":       f"APL{idx:06d}",
        "Age":                  age,
        "Gender":               random.choice(["Male","Male","Female","Female","Other"]),
        "Marital_Status":       random.choice(["Married","Single","Single","Married","Divorced"]),
        "State":                state,
        "City":                 city,
        "Education":            education,
        "Employment_Type":      emp_type,
        "Employer_Category":    "Government" if "Government" in emp_type or "PSU" in emp_type or "Defence" in emp_type else ("Self" if emp_type in ["Self-Employed","Business Owner"] else "Private"),
        "Years_of_Employment":  years_emp,
        "Monthly_Income":       monthly_income,
        "Annual_Income":        annual_income,
        "Number_of_Dependents": dependents,
        "Residence_Type":       random.choice(["Own","Rented","Rented","Family","Company Provided"]),
        "Residential_Assets_Value": res_asset,
        "Commercial_Assets_Value":  com_asset,
        "Vehicle_Owned":        vehicle,
        "Existing_Loan_Count":  existing_loans,
        "Existing_Emi_Amount":  existing_emi,
        "Outstanding_Debt":     outstanding_debt,
        "Credit_Card_Outstanding": cc_outstanding,
        "Credit_Utilization_Ratio": credit_utilization,
        "CIBIL_Score":          cibil,
        "Previous_Loan_Count":  prev_loans,
        "Missed_Payment_Count": missed_payments,
        "Late_Payment_Count":   late_payments,
        "Average_Days_Late":    avg_days_late,
        "Requested_Loan_Category": loan_category,
        "Requested_Loan_Amount":   requested_amount,
        "Requested_Loan_Tenure":   tenure,
        "Loan_Purpose":         purpose,
        "Coapplicant":          "Yes" if coapplicant else "No",
        "Coapplicant_Income":   coapplicant_income,
        "Debt_to_Income_Ratio": dti,
        "EMI_to_Income_Ratio":  eti,
        "Eligibility_Target":   eligibility_target,
        "Affordability_Target": affordability_target,
        "Dataset_Type":         "Synthetic_Borrower_Data",
    }


def run():
    print(f"Generating {N_RECORDS} synthetic Indian borrower records (seed={RANDOM_SEED})...")
    records = [generate_record(i+1) for i in range(N_RECORDS)]
    df = pd.DataFrame(records)

    # ?? Data quality summary ??????????????????????????????????????
    print(f"\n{'='*50}")
    print(f"DATASET VALIDATION SUMMARY")
    print(f"{'='*50}")
    print(f"Total records:       {len(df)}")
    print(f"Missing values:      {df.isnull().sum().sum()}")
    print(f"Duplicate IDs:       {df['Applicant_ID'].duplicated().sum()}")
    print(f"Income range:        Rs.{df['Monthly_Income'].min():,.0f} - Rs.{df['Monthly_Income'].max():,.0f}/month")
    print(f"CIBIL range:         {df['CIBIL_Score'].min()} - {df['CIBIL_Score'].max()}")
    print(f"Avg income:          Rs.{df['Monthly_Income'].mean():,.0f}/month")
    print(f"Avg loan amount:     Rs.{df['Requested_Loan_Amount'].mean():,.0f}")
    elig_dist = df['Eligibility_Target'].value_counts()
    afford_dist = df['Affordability_Target'].value_counts()
    print(f"Eligibility:         Eligible={elig_dist.get('Eligible',0)} | Not_Eligible={elig_dist.get('Not_Eligible',0)}")
    print(f"Affordability:       Manageable={afford_dist.get('Manageable',0)} | Not_Manageable={afford_dist.get('Not_Manageable',0)}")

    # ?? Save separate training datasets ??????????????????????????
    eligibility_cols = [
        "Applicant_ID","Age","Education","Employment_Type","Employer_Category",
        "Years_of_Employment","Monthly_Income","Annual_Income","Number_of_Dependents",
        "Existing_Loan_Count","Existing_Emi_Amount","Outstanding_Debt",
        "Credit_Card_Outstanding","Credit_Utilization_Ratio","CIBIL_Score",
        "Previous_Loan_Count","Missed_Payment_Count","Late_Payment_Count",
        "Average_Days_Late","Requested_Loan_Category","Requested_Loan_Amount",
        "Requested_Loan_Tenure","Coapplicant","Coapplicant_Income",
        "Debt_to_Income_Ratio","EMI_to_Income_Ratio","Eligibility_Target",
    ]
    affordability_cols = [
        "Applicant_ID","Monthly_Income","Number_of_Dependents","Existing_Loan_Count",
        "Existing_Emi_Amount","Outstanding_Debt","Credit_Card_Outstanding",
        "Credit_Utilization_Ratio","CIBIL_Score","Previous_Loan_Count",
        "Missed_Payment_Count","Late_Payment_Count","Average_Days_Late",
        "Requested_Loan_Amount","Requested_Loan_Tenure",
        "Debt_to_Income_Ratio","EMI_to_Income_Ratio","Affordability_Target",
    ]

    elig_path  = OUTPUT_DIR / "eligibility_dataset.csv"
    afford_path = OUTPUT_DIR / "affordability_dataset.csv"
    df[eligibility_cols].to_csv(elig_path, index=False)
    df[affordability_cols].to_csv(afford_path, index=False)

    print(f"\nSaved: {elig_path}")
    print(f"Saved: {afford_path}")
    print(f"\nNote: This is SYNTHETIC data for ML training only. Not real customer data.")
    return df


if __name__ == "__main__":
    run()
