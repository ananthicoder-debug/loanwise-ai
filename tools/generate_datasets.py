"""
tools/generate_datasets.py
---------------------------
Reproducible synthetic Indian loan dataset generator.
RANDOM_SEED = 42 — same seed always produces same data.

Generates:
  data/borrowers_2000.csv          — 2000 synthetic borrower records
  data/historical_loans_2000.csv   — 2000 synthetic historical loan records
  data/installment_payments.csv    — ~4000–6000 installment payment records

Run: python tools/generate_datasets.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

OUT_DIR = Path(__file__).resolve().parents[1] / "data"
OUT_DIR.mkdir(exist_ok=True)

# ─── Indian context data ──────────────────────────────────────────────────────

STATES_CITIES = {
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belagavi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    "Delhi": ["New Delhi", "Dwarka", "Rohini", "Lajpat Nagar", "Janakpuri"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Allahabad"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri"],
    "Telangana": ["Hyderabad", "Warangal", "Karimnagar", "Khammam", "Nizamabad"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain"],
    "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga"],
    "Haryana": ["Gurgaon", "Faridabad", "Panipat", "Ambala", "Karnal"],
    "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda"],
}

MALE_NAMES = ["Rajesh", "Amit", "Suresh", "Vikram", "Anil", "Pradeep", "Ravi",
              "Sanjay", "Manoj", "Deepak", "Arjun", "Karthik", "Nitin", "Vivek",
              "Rahul", "Rohit", "Sachin", "Vikas", "Ajay", "Naveen"]
FEMALE_NAMES = ["Priya", "Anita", "Sunita", "Rekha", "Meena", "Kavita", "Seetha",
                "Lakshmi", "Divya", "Pooja", "Sneha", "Neha", "Asha", "Usha",
                "Radha", "Geeta", "Nirmala", "Kamala", "Saranya", "Deepa"]
SURNAMES = ["Sharma", "Patel", "Kumar", "Singh", "Gupta", "Reddy", "Nair",
            "Iyer", "Menon", "Joshi", "Verma", "Rao", "Mishra", "Tiwari",
            "Das", "Bose", "Choudhury", "Mehta", "Shah", "Pillai"]

EMPLOYMENT_TYPES = ["Salaried", "Self-Employed", "Business Owner",
                    "Government Employee", "Private Employee", "Professional", "PSU Employee"]
EMPLOYER_CATS = ["Private", "Government", "IT/Tech", "PSU", "Self", "Defence", "Banking"]
EDUCATION_LEVELS = ["High School", "Diploma", "Graduate", "Post Graduate", "Professional Degree"]
RESIDENCE_TYPES = ["Owned", "Rented", "Family Owned"]
MARITAL_STATUSES = ["Married", "Single", "Divorced", "Widowed"]

LOAN_CATEGORIES = ["Personal Loan", "Home Loan", "Vehicle Loan", "Education Loan",
                   "Gold Loan", "Business Loan", "Consumer Durable Loan"]
LOAN_PURPOSES = {
    "Personal Loan":        ["Home renovation", "Medical emergency", "Wedding expenses",
                             "Debt consolidation", "Travel", "Education", "Electronics purchase"],
    "Home Loan":            ["Purchase", "Construction", "Renovation", "Extension"],
    "Vehicle Loan":         ["New car", "Used car", "New two-wheeler", "Used two-wheeler",
                             "Commercial vehicle"],
    "Education Loan":       ["Undergraduate", "Postgraduate", "MBA", "Engineering", "Medical",
                             "Study abroad"],
    "Gold Loan":            ["Emergency funds", "Business needs", "Agricultural", "Education"],
    "Business Loan":        ["Working capital", "Equipment purchase", "Expansion",
                             "Inventory", "Office setup"],
    "Consumer Durable Loan":["AC", "Refrigerator", "Washing machine", "TV", "Laptop",
                             "Mobile phone", "Furniture"],
}

LENDER_PRODUCT_IDS = [
    ("L001", "SBI"), ("L002", "HDFC Bank"), ("L003", "ICICI Bank"),
    ("L004", "Axis Bank"), ("L005", "PNB"), ("L006", "Bank of Baroda"),
    ("L007", "Canara Bank"), ("L008", "Kotak Mahindra Bank"),
    ("L009", "IDFC FIRST Bank"), ("L010", "IndusInd Bank"),
    ("L011", "Bajaj Finance"), ("L012", "Tata Capital"),
]

REPAYMENT_STATUSES = ["Good", "Occasional Late Payment", "Frequent Late Payment",
                      "Missed Payments", "Poor Repayment"]


# ─── Helper functions ─────────────────────────────────────────────────────────

def random_name(gender):
    first = random.choice(MALE_NAMES if gender == "Male" else FEMALE_NAMES)
    return f"{first} {random.choice(SURNAMES)}"


def cibil_from_profile(missed, late, existing_loans, years_emp):
    base = 700
    base -= missed * 40
    base -= late * 15
    base -= max(0, existing_loans - 2) * 20
    base += min(years_emp, 10) * 8
    noise = np.random.randint(-50, 50)
    return int(np.clip(base + noise, 300, 900))


def loan_amount_for_category(category, monthly_income, cibil):
    multiplier_min = {
        "Personal Loan": 3, "Home Loan": 36, "Vehicle Loan": 8,
        "Education Loan": 6, "Gold Loan": 2, "Business Loan": 6,
        "Consumer Durable Loan": 1
    }.get(category, 3)
    multiplier_max = {
        "Personal Loan": 24, "Home Loan": 200, "Vehicle Loan": 30,
        "Education Loan": 60, "Gold Loan": 15, "Business Loan": 48,
        "Consumer Durable Loan": 6
    }.get(category, 24)

    cibil_factor = max(0.5, (cibil - 300) / 600)
    min_amt = monthly_income * multiplier_min * cibil_factor
    max_amt = monthly_income * multiplier_max * cibil_factor

    # Round to nearest 10000
    amt = random.uniform(min_amt, max_amt)
    amt = round(amt / 10000) * 10000

    return max(10000, int(amt))


def eligible_label(cibil, annual_income, loan_amount, existing_loans,
                   missed, dti, eti):
    score = 0
    if cibil >= 750: score += 3
    elif cibil >= 700: score += 2
    elif cibil >= 650: score += 1
    elif cibil < 600: score -= 2

    if annual_income >= loan_amount * 0.3: score += 2
    elif annual_income >= loan_amount * 0.15: score += 1
    else: score -= 2

    if existing_loans == 0: score += 1
    elif existing_loans <= 2: score += 0
    else: score -= 1

    if missed == 0: score += 1
    elif missed <= 2: score -= 1
    else: score -= 3

    if dti < 0.3: score += 1
    elif dti > 0.6: score -= 2

    if eti < 0.3: score += 1
    elif eti > 0.5: score -= 2

    # Probabilistic with noise
    prob = np.clip(0.5 + score * 0.1 + np.random.normal(0, 0.08), 0.01, 0.99)
    return "Eligible" if np.random.rand() < prob else "Not_Eligible"


def manageable_label(monthly_income, existing_emi, proposed_emi, missed, cibil, dti):
    total_emi_ratio = (existing_emi + proposed_emi) / max(monthly_income, 1)
    score = 0
    if total_emi_ratio < 0.35: score += 3
    elif total_emi_ratio < 0.5: score += 1
    else: score -= 2

    if missed == 0: score += 2
    elif missed <= 1: score += 0
    elif missed <= 3: score -= 1
    else: score -= 3

    if cibil >= 700: score += 1
    elif cibil < 600: score -= 1

    if dti < 0.3: score += 1
    elif dti > 0.5: score -= 1

    prob = np.clip(0.5 + score * 0.1 + np.random.normal(0, 0.08), 0.01, 0.99)
    return "Manageable" if np.random.rand() < prob else "Not_Manageable"


# ─── DATASET 1: Borrowers ─────────────────────────────────────────────────────

def generate_borrowers(n=2000):
    print(f"Generating {n} borrower records (RANDOM_SEED={RANDOM_SEED})...")
    records = []

    for i in range(n):
        app_id = f"APP{i+1:06d}"
        appl_id = f"APPL{i+1:06d}"

        gender = random.choice(["Male", "Female"])
        age = random.randint(21, 65)
        marital = random.choices(["Married", "Single", "Divorced", "Widowed"],
                                 weights=[55, 30, 10, 5])[0]
        state = random.choice(list(STATES_CITIES.keys()))
        city = random.choice(STATES_CITIES[state])
        education = random.choices(EDUCATION_LEVELS, weights=[10, 15, 40, 25, 10])[0]
        emp_type = random.choices(EMPLOYMENT_TYPES, weights=[35, 20, 15, 10, 10, 7, 3])[0]
        emp_cat = random.choice(EMPLOYER_CATS)

        # Years of employment must be consistent with age
        max_years = max(1, age - 22)
        years_emp = round(random.uniform(0.5, min(max_years, 30)), 1)

        # Income — correlated with employment and education
        income_base = {
            "Salaried": 45000, "Private Employee": 38000, "Self-Employed": 50000,
            "Business Owner": 70000, "Government Employee": 42000,
            "Professional": 80000, "PSU Employee": 48000
        }.get(emp_type, 40000)
        edu_mult = {"High School": 0.6, "Diploma": 0.8, "Graduate": 1.0,
                    "Post Graduate": 1.3, "Professional Degree": 1.6}.get(education, 1.0)
        seniority_mult = 1 + min(years_emp, 20) * 0.025
        monthly_income = int(income_base * edu_mult * seniority_mult * random.uniform(0.7, 1.5))
        monthly_income = max(15000, min(500000, monthly_income))
        annual_income = monthly_income * 12

        dependents = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[20, 25, 30, 15, 6, 3, 1])[0]
        residence = random.choices(RESIDENCE_TYPES, weights=[45, 40, 15])[0]
        res_asset = int(random.uniform(0, monthly_income * 200)) if residence == "Owned" else 0
        comm_asset = int(random.uniform(0, monthly_income * 100)) if emp_type in ["Business Owner", "Self-Employed"] else 0
        vehicle = random.choices(["None", "Two Wheeler", "Car", "Both"],
                                 weights=[30, 40, 20, 10])[0]

        existing_loans = random.choices([0, 1, 2, 3, 4], weights=[35, 30, 20, 10, 5])[0]
        existing_emi = int(monthly_income * random.uniform(0, 0.35)) if existing_loans > 0 else 0
        outstanding_debt = existing_emi * random.randint(12, 48) if existing_loans > 0 else 0
        cc_outstanding = int(random.uniform(0, monthly_income * 2)) if random.random() < 0.3 else 0
        credit_util = round(min(cc_outstanding / max(monthly_income * 5, 1), 1.0), 2)

        previous_loans = existing_loans + random.randint(0, 4)
        missed = random.choices([0, 1, 2, 3, 4, 5], weights=[50, 20, 12, 8, 6, 4])[0]
        late = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[40, 22, 15, 10, 7, 4, 2])[0]
        avg_days_late = round(random.uniform(0, 25) if (missed > 0 or late > 0) else 0, 1)

        cibil = cibil_from_profile(missed, late, existing_loans, years_emp)

        category = random.choices(LOAN_CATEGORIES, weights=[35, 20, 15, 10, 8, 7, 5])[0]
        loan_amount = loan_amount_for_category(category, monthly_income, cibil)
        tenure = {
            "Personal Loan": random.choice([12, 24, 36, 48, 60]),
            "Home Loan": random.choice([60, 84, 120, 180, 240]),
            "Vehicle Loan": random.choice([24, 36, 48, 60, 84]),
            "Education Loan": random.choice([24, 36, 48, 60, 84]),
            "Gold Loan": random.choice([6, 12, 18, 24]),
            "Business Loan": random.choice([12, 24, 36, 48, 60]),
            "Consumer Durable Loan": random.choice([6, 12, 18, 24]),
        }.get(category, 36)
        purpose = random.choice(LOAN_PURPOSES.get(category, ["General"]))

        coapplicant = random.random() < 0.25
        coapplicant_income = int(monthly_income * random.uniform(0.3, 0.8)) if coapplicant else 0

        # Derived ratios
        dti = round(outstanding_debt / max(annual_income, 1), 4)
        eti = round(existing_emi / max(monthly_income, 1), 4)

        # Approximate proposed EMI for label calculation
        mid_rate = 12.0  # representative annual rate
        r = (mid_rate / 12) / 100
        proposed_emi = int(loan_amount * r * (1 + r) ** tenure / ((1 + r) ** tenure - 1))

        elig = eligible_label(cibil, annual_income, loan_amount, existing_loans, missed, dti, eti)
        mgbl = manageable_label(monthly_income, existing_emi, proposed_emi, missed, cibil, dti)

        records.append({
            "Application_ID": app_id,
            "Applicant_ID": appl_id,
            "Full_Name": random_name(gender),
            "Age": age,
            "Gender": gender,
            "Marital_Status": marital,
            "State": state,
            "City": city,
            "Education": education,
            "Employment_Type": emp_type,
            "Employer_Category": emp_cat,
            "Years_of_Employment": years_emp,
            "Monthly_Income": monthly_income,
            "Annual_Income": annual_income,
            "Number_of_Dependents": dependents,
            "Residence_Type": residence,
            "Residential_Assets_Value": res_asset,
            "Commercial_Assets_Value": comm_asset,
            "Vehicle_Owned": vehicle,
            "Existing_Loan_Count": existing_loans,
            "Existing_Emi_Amount": existing_emi,
            "Outstanding_Debt": outstanding_debt,
            "Credit_Card_Outstanding": cc_outstanding,
            "Credit_Utilization_Ratio": credit_util,
            "CIBIL_Score": cibil,
            "Previous_Loan_Count": previous_loans,
            "Missed_Payment_Count": missed,
            "Late_Payment_Count": late,
            "Average_Days_Late": avg_days_late,
            "Requested_Loan_Category": category,
            "Requested_Loan_Amount": loan_amount,
            "Requested_Loan_Tenure": tenure,
            "Loan_Purpose": purpose,
            "Coapplicant": coapplicant,
            "Coapplicant_Income": coapplicant_income,
            "Debt_to_Income_Ratio": dti,
            "EMI_to_Income_Ratio": eti,
            "Eligibility_Target": elig,
            "Affordability_Target": mgbl,
            "Dataset_Type": "Synthetic_Borrower_Data",
        })

    df = pd.DataFrame(records)
    out = OUT_DIR / "borrowers_2000.csv"
    df.to_csv(out, index=False)

    # Validation
    eligible_count = (df["Eligibility_Target"] == "Eligible").sum()
    manageable_count = (df["Affordability_Target"] == "Manageable").sum()
    print(f"\n=== Borrower Dataset Validation ===")
    print(f"Records:           {len(df)}")
    print(f"Missing values:    {df.isnull().sum().sum()}")
    print(f"Duplicate App IDs: {df['Application_ID'].duplicated().sum()}")
    print(f"Age range:         {df['Age'].min()}–{df['Age'].max()}")
    print(f"CIBIL range:       {df['CIBIL_Score'].min()}–{df['CIBIL_Score'].max()}")
    print(f"Income range:      ₹{df['Monthly_Income'].min():,}–₹{df['Monthly_Income'].max():,}")
    print(f"Avg income:        ₹{df['Monthly_Income'].mean():,.0f}/month")
    print(f"Avg loan amount:   ₹{df['Requested_Loan_Amount'].mean():,.0f}")
    print(f"Avg CIBIL:         {df['CIBIL_Score'].mean():.0f}")
    print(f"Eligible:          {eligible_count} ({eligible_count/len(df)*100:.1f}%)")
    print(f"Not Eligible:      {len(df)-eligible_count} ({(len(df)-eligible_count)/len(df)*100:.1f}%)")
    print(f"Manageable:        {manageable_count} ({manageable_count/len(df)*100:.1f}%)")
    print(f"Not Manageable:    {len(df)-manageable_count} ({(len(df)-manageable_count)/len(df)*100:.1f}%)")
    print(f"Saved: {out}")
    return df


# ─── DATASET 2: Historical Loans ──────────────────────────────────────────────

def generate_historical_loans(borrowers_df, n=2000):
    print(f"\nGenerating {n} historical loan records...")
    records = []
    appl_ids = borrowers_df["Applicant_ID"].tolist()

    for i in range(n):
        loan_id = f"HL{i+1:07d}"
        appl_id = random.choice(appl_ids)
        lender_code, lender_name = random.choice(LENDER_PRODUCT_IDS)
        category = random.choices(LOAN_CATEGORIES, weights=[35, 20, 15, 10, 8, 7, 5])[0]
        product_id = f"{lender_code}_{category[:3].upper()}_{random.randint(100, 999)}"

        # Loan amount ranges per category
        amt_ranges = {
            "Personal Loan": (50000, 1000000),
            "Home Loan": (500000, 10000000),
            "Vehicle Loan": (100000, 1500000),
            "Education Loan": (50000, 2000000),
            "Gold Loan": (10000, 500000),
            "Business Loan": (100000, 5000000),
            "Consumer Durable Loan": (10000, 200000),
        }
        lo, hi = amt_ranges.get(category, (50000, 1000000))
        loan_amount = round(random.randint(lo // 10000, hi // 10000) * 10000)

        rate_ranges = {
            "Personal Loan": (10.5, 24.0), "Home Loan": (8.5, 12.5),
            "Vehicle Loan": (9.0, 16.0), "Education Loan": (10.0, 15.0),
            "Gold Loan": (7.5, 17.0), "Business Loan": (11.0, 22.0),
            "Consumer Durable Loan": (12.0, 22.0),
        }
        lo_r, hi_r = rate_ranges.get(category, (10.0, 20.0))
        interest_rate = round(random.uniform(lo_r, hi_r), 2)

        tenure_months = random.choice({
            "Personal Loan": [12, 24, 36, 48, 60],
            "Home Loan": [120, 180, 240, 300],
            "Vehicle Loan": [24, 36, 48, 60, 84],
            "Education Loan": [36, 48, 60, 84],
            "Gold Loan": [6, 12, 18, 24],
            "Business Loan": [24, 36, 48, 60],
            "Consumer Durable Loan": [6, 12, 18, 24],
        }.get(category, [36]))

        r = (interest_rate / 12) / 100
        emi_amount = round(loan_amount * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1), 2)

        # Random start date between 2018 and 2024
        start_dt = datetime(2018, 1, 1) + timedelta(days=random.randint(0, 365 * 6))
        start_date = start_dt.strftime("%Y-%m-%d")

        # Loan status
        loan_status = random.choices(["Closed", "Active", "Defaulted"],
                                     weights=[50, 40, 10])[0]

        total_installments = tenure_months
        if loan_status == "Closed":
            paid_installments = total_installments
            missed_installments = random.choices([0, 1, 2, 3], weights=[70, 15, 10, 5])[0]
            late_installments = random.choices([0, 1, 2, 3, 4], weights=[50, 20, 15, 10, 5])[0]
        elif loan_status == "Active":
            months_elapsed = min(tenure_months - 1, random.randint(3, tenure_months))
            paid_installments = months_elapsed - random.randint(0, 2)
            paid_installments = max(0, paid_installments)
            missed_installments = random.choices([0, 1, 2], weights=[65, 25, 10])[0]
            late_installments = random.choices([0, 1, 2, 3], weights=[55, 25, 15, 5])[0]
        else:  # Defaulted
            paid_installments = random.randint(1, tenure_months // 2)
            missed_installments = random.randint(3, 8)
            late_installments = random.randint(2, 6)

        avg_days_late = round(random.uniform(5, 30) if late_installments > 0 else 0, 1)
        total_late_charges = round(emi_amount * 0.02 * late_installments, 2)
        outstanding_amount = round(max(0, loan_amount - (emi_amount * paid_installments * 0.6)), 2)

        # Repayment status
        if missed_installments == 0 and late_installments <= 1:
            repayment_status = "Good"
        elif missed_installments == 0 and late_installments <= 3:
            repayment_status = "Occasional Late Payment"
        elif missed_installments <= 2 and late_installments <= 5:
            repayment_status = "Frequent Late Payment"
        elif missed_installments <= 4:
            repayment_status = "Missed Payments"
        else:
            repayment_status = "Poor Repayment"

        records.append({
            "Historical_Loan_ID": loan_id,
            "Applicant_ID": appl_id,
            "Product_ID": product_id,
            "Lender_ID": lender_code,
            "Lender_Name": lender_name,
            "Loan_Category": category,
            "Loan_Amount": loan_amount,
            "Interest_Rate": interest_rate,
            "Tenure_Months": tenure_months,
            "EMI_Amount": emi_amount,
            "Start_Date": start_date,
            "Loan_Status": loan_status,
            "Outstanding_Amount": outstanding_amount,
            "Total_Installments": total_installments,
            "Paid_Installments": paid_installments,
            "Missed_Installments": missed_installments,
            "Late_Installments": late_installments,
            "Average_Days_Late": avg_days_late,
            "Total_Late_Charges": total_late_charges,
            "Repayment_Status": repayment_status,
            "Dataset_Type": "Synthetic_Historical_Data",
        })

    df = pd.DataFrame(records)
    out = OUT_DIR / "historical_loans_2000.csv"
    df.to_csv(out, index=False)

    print(f"\n=== Historical Loans Validation ===")
    print(f"Records:         {len(df)}")
    print(f"Loan statuses:   {dict(df['Loan_Status'].value_counts())}")
    print(f"Repayment dist:  {dict(df['Repayment_Status'].value_counts())}")
    print(f"Avg loan amount: ₹{df['Loan_Amount'].mean():,.0f}")
    print(f"Avg EMI:         ₹{df['EMI_Amount'].mean():,.0f}")
    print(f"Saved: {out}")
    return df


# ─── DATASET 3: Installment Payments ─────────────────────────────────────────

def generate_installment_payments(historical_df, target_records=4000):
    print(f"\nGenerating ~{target_records} installment payment records...")
    records = []
    payment_counter = 1

    # Sample loans to get enough installment records
    loans = historical_df.sample(
        n=min(len(historical_df), target_records // 4),
        random_state=RANDOM_SEED
    ).to_dict("records")

    today = datetime.now().date()

    for loan in loans:
        loan_id = loan["Historical_Loan_ID"]
        appl_id = loan["Applicant_ID"]
        product_id = loan["Product_ID"]
        emi = float(loan["EMI_Amount"])
        tenure = int(loan["Tenure_Months"])
        paid = int(loan["Paid_Installments"])
        missed = int(loan["Missed_Installments"])
        late = int(loan["Late_Installments"])
        status = loan["Loan_Status"]

        try:
            start_dt = datetime.strptime(str(loan["Start_Date"]), "%Y-%m-%d")
        except Exception:
            start_dt = datetime(2020, 1, 1)

        # How many installments to generate
        gen_count = min(tenure, paid + missed + random.randint(1, 4))

        for inst_num in range(1, gen_count + 1):
            pay_id = f"PAY{payment_counter:08d}"
            payment_counter += 1

            # Due date
            due_m = (start_dt.month + inst_num - 1) % 12 or 12
            due_y = start_dt.year + (start_dt.month + inst_num - 2) // 12
            try:
                due_dt = start_dt.replace(year=due_y, month=due_m)
            except ValueError:
                due_dt = start_dt.replace(year=due_y, month=due_m, day=28)

            due_date = due_dt.strftime("%Y-%m-%d")

            # Principal/Interest split (simplified)
            interest_comp = round(emi * 0.3 * (1 - inst_num / (tenure * 2)), 2)
            principal_comp = round(emi - interest_comp, 2)

            # Determine payment status
            is_paid_inst = inst_num <= paid
            is_missed_inst = not is_paid_inst and random.random() < (missed / max(tenure - paid, 1))
            is_late_inst = is_paid_inst and random.random() < (late / max(paid, 1))

            if due_dt.date() > today:
                pay_status = "Pending"
                paid_date = ""
                amount_paid = 0
                days_late = 0
                late_charge = 0
            elif is_missed_inst:
                pay_status = "Missed"
                paid_date = ""
                amount_paid = 0
                days_late = (today - due_dt.date()).days
                late_charge = 0
            elif is_late_inst:
                delay = random.randint(3, 35)
                paid_dt = due_dt + timedelta(days=delay)
                pay_status = "Late"
                paid_date = paid_dt.strftime("%Y-%m-%d")
                amount_paid = round(emi + emi * 0.02 * max(1, delay // 30), 2)
                days_late = delay
                late_charge = round(emi * 0.02 * max(1, delay // 30), 2)
            else:
                paid_dt = due_dt + timedelta(days=random.randint(0, 3))
                pay_status = "Paid"
                paid_date = paid_dt.strftime("%Y-%m-%d")
                amount_paid = emi
                days_late = 0
                late_charge = 0

            records.append({
                "Payment_ID": pay_id,
                "Historical_Loan_ID": loan_id,
                "Applicant_ID": appl_id,
                "Product_ID": product_id,
                "Installment_Number": inst_num,
                "Due_Date": due_date,
                "Due_Amount": round(emi, 2),
                "Principal_Component": principal_comp,
                "Interest_Component": interest_comp,
                "Paid_Date": paid_date,
                "Amount_Paid": round(amount_paid, 2),
                "Payment_Status": pay_status,
                "Days_Late": days_late,
                "Late_Charge": round(late_charge, 2),
                "Dataset_Type": "Synthetic_Historical_Data",
            })

    df = pd.DataFrame(records)
    out = OUT_DIR / "installment_payments.csv"
    df.to_csv(out, index=False)

    print(f"\n=== Installment Payments Validation ===")
    print(f"Records:          {len(df)}")
    print(f"Status breakdown: {dict(df['Payment_Status'].value_counts())}")
    neg_emi = (df['Due_Amount'] < 0).sum()
    print(f"Negative EMI:     {neg_emi} (should be 0)")
    print(f"Saved: {out}")
    return df


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("LoanWise AI — Synthetic Dataset Generator")
    print(f"Random Seed: {RANDOM_SEED}")
    print("=" * 60)

    borrowers = generate_borrowers(n=2000)
    historical = generate_historical_loans(borrowers, n=2000)
    installments = generate_installment_payments(historical, target_records=5000)

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print(f"  Borrowers:    {len(borrowers):,} records → data/borrowers_2000.csv")
    print(f"  Historical:   {len(historical):,} records → data/historical_loans_2000.csv")
    print(f"  Installments: {len(installments):,} records → data/installment_payments.csv")
    print("=" * 60)
    print("\nNOTE: These datasets are SYNTHETIC — generated for ML training.")
    print("They do NOT represent real borrower data or real loan records.")
    print("Loan product information is from verified official lender sources.")


if __name__ == "__main__":
    main()
