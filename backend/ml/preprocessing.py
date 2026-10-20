"""
ml/preprocessing.py
--------------------
Feature definitions derived from ACTUAL CSV schema inspection.

eligibility_dataset.csv columns (target=loan_status):
  age, education, employment_type, annual_income, dependents, cibil_score,
  existing_loans, outstanding_debt, loan_amount, loan_tenure

affordability_dataset.csv columns (target=manageable):
  monthly_income, dependents, existing_loans, current_emi, outstanding_debt,
  previous_loans, missed_payments, late_payments, proposed_amount,
  proposed_rate, proposed_tenure, proposed_emi, emi_income_ratio

borrowers.csv has 42 columns — used for applicant profile & rich feature mapping.
"""

# ─── Encoding maps (match actual CSV values exactly) ─────────────────────────

EMPLOYMENT_MAP = {
    # eligibility_dataset.csv values
    "Salaried":           0,
    "Self-Employed":      1,
    "Business":           2,
    "Student":            3,
    # borrowers.csv additional values
    "Private Employee":   0,
    "Government Employee":0,
    "PSU Employee":       0,
    "Defence Employee":   0,
    "Business Owner":     2,
    "Professional":       0,
    # credit-profile values
    "Self":               1,
}

EDUCATION_MAP = {
    # eligibility_dataset.csv values
    "Graduate":           0,
    "Not Graduate":       1,
    # borrowers.csv additional values
    "Postgraduate":       0,
    "Post Graduate":      0,
    "Diploma":            1,
    "12th":               1,
    "Professional Degree":0,
    "High School":        1,
    "10th":               1,
}

REPAYMENT_STATUS_MAP = {
    # historical_loans.csv values
    "Excellent": 0,
    "Good":      1,
    "Fair":      2,
    "Delayed":   3,
    "Poor":      4,
    # user profile values
    "Very Good": 1,
    "Average":   2,
    "Bad":       4,
}

# ─── Model 1: Eligibility features (exact match to eligibility_dataset.csv) ──

ELIGIBILITY_FEATURES = [
    "age",
    "education_enc",
    "employment_enc",
    "annual_income",
    "dependents",
    "cibil_score",
    "existing_loans",
    "outstanding_debt",
    "loan_amount",
    "loan_tenure",
]

# ─── Model 2: Affordability features (exact match to affordability_dataset.csv)

AFFORDABILITY_FEATURES = [
    "monthly_income",
    "dependents",
    "existing_loans",
    "current_emi",
    "outstanding_debt",
    "previous_loans",
    "missed_payments",
    "late_payments",
    "proposed_amount",
    "proposed_rate",
    "proposed_tenure",
    "proposed_emi",
    "emi_income_ratio",
]


def build_eligibility_vector(credit_profile: dict, application: dict) -> list:
    """
    Build Model 1 input from credit_profile + application dicts.
    Uses exact feature names matching eligibility_dataset.csv columns.
    """
    edu = credit_profile.get("education") or "Graduate"
    emp = (credit_profile.get("employment_type") or
           credit_profile.get("Employment_Type") or "Salaried")

    # annual_income — accept monthly * 12 fallback
    annual = (credit_profile.get("annual_income") or
              credit_profile.get("Annual_Income") or
              (credit_profile.get("monthly_income", 0) * 12) or 0)

    return [
        int(credit_profile.get("age") or credit_profile.get("Age") or 30),
        EDUCATION_MAP.get(edu, 0),
        EMPLOYMENT_MAP.get(emp, 0),
        float(annual),
        int(credit_profile.get("dependents") or
            credit_profile.get("Number_of_Dependents") or 0),
        int(credit_profile.get("cibil_score") or
            credit_profile.get("CIBIL_Score") or 650),
        int(credit_profile.get("existing_loans") or
            credit_profile.get("Existing_Loan_Count") or 0),
        float(credit_profile.get("outstanding_debt") or
              credit_profile.get("Outstanding_Debt") or 0),
        float(application.get("loan_amount") or
              application.get("Requested_Loan_Amount") or 0),
        int(application.get("loan_tenure") or
            application.get("Requested_Loan_Tenure") or 12),
    ]


def build_affordability_vector(credit_profile: dict,
                                application: dict,
                                proposed_emi: float) -> list:
    """
    Build Model 2 input from credit_profile + application + proposed EMI.
    Uses exact feature names matching affordability_dataset.csv columns.
    """
    monthly = float(
        credit_profile.get("monthly_income") or
        credit_profile.get("Monthly_Income") or
        (credit_profile.get("annual_income", 0) / 12) or 1
    )
    current = float(
        credit_profile.get("existing_emi") or          # new profile field
        credit_profile.get("current_emi") or           # old profile field
        credit_profile.get("Existing_Emi_Amount") or 0
    )
    rate = float(
        application.get("proposed_rate") or
        application.get("interest_rate") or 12.0
    )
    tenure = int(
        application.get("loan_tenure") or
        application.get("proposed_tenure") or
        application.get("Requested_Loan_Tenure") or 12
    )
    amount = float(
        application.get("loan_amount") or
        application.get("proposed_amount") or
        application.get("Requested_Loan_Amount") or 0
    )
    emi_ratio = round((current + proposed_emi) / monthly, 4) if monthly else 1.0

    return [
        monthly,
        int(credit_profile.get("dependents") or
            credit_profile.get("Number_of_Dependents") or 0),
        int(credit_profile.get("existing_loans") or
            credit_profile.get("Existing_Loan_Count") or 0),
        current,
        float(credit_profile.get("outstanding_debt") or
              credit_profile.get("Outstanding_Debt") or 0),
        int(credit_profile.get("previous_loans") or
            credit_profile.get("Previous_Loan_Count") or 0),
        int(credit_profile.get("missed_payments") or
            credit_profile.get("Missed_Payment_Count") or 0),
        int(credit_profile.get("late_payments") or
            credit_profile.get("Late_Payment_Count") or 0),
        amount,
        rate,
        tenure,
        float(proposed_emi),
        emi_ratio,
    ]
