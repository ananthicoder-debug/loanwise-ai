"""
services/emi_service.py
------------------------
Purpose:
    Pure-math EMI (Equated Monthly Installment) calculations, used by:
      - recommendation_service.py (to show an ESTIMATED EMI on eligible
        products, before the user commits to anything)
      - routes/payments.py (to generate the real EMI schedule once an
        ACTIVE_LOAN is created)

Formula (requirement #11):
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    where P = principal, r = monthly interest rate (annual/12/100),
    n = number of months.
"""

from datetime import datetime, timedelta


def calculate_emi(principal: float, annual_rate_percent: float, tenure_months: int) -> float:
    """Return the monthly EMI amount, rounded to 2 decimals."""
    if tenure_months <= 0:
        raise ValueError("tenure_months must be > 0")
    monthly_rate = (annual_rate_percent / 12) / 100

    if monthly_rate == 0:
        # 0% interest edge case: EMI is simply principal / months
        return round(principal / tenure_months, 2)

    factor = (1 + monthly_rate) ** tenure_months
    emi = principal * monthly_rate * factor / (factor - 1)
    return round(emi, 2)


def generate_amortization_schedule(
    principal: float,
    annual_rate_percent: float,
    tenure_months: int,
    start_date: datetime,
    first_due_date: datetime,
) -> list[dict]:
    """
    Builds the full EMI-by-EMI schedule (requirement #12), splitting each
    installment into principal vs interest portions the way a real bank
    statement does. Returns a list of dicts ready to insert into the
    `payments` collection (active_loan_id is added by the caller).
    """
    monthly_rate = (annual_rate_percent / 12) / 100
    emi_amount = calculate_emi(principal, annual_rate_percent, tenure_months)

    schedule = []
    outstanding_principal = principal
    due_date = first_due_date

    for emi_number in range(1, tenure_months + 1):
        interest_component = round(outstanding_principal * monthly_rate, 2)
        principal_component = round(emi_amount - interest_component, 2)

        # Last EMI absorbs any rounding drift so the loan fully closes to 0.
        if emi_number == tenure_months:
            principal_component = round(outstanding_principal, 2)
            emi_amount_final = round(principal_component + interest_component, 2)
        else:
            emi_amount_final = emi_amount

        outstanding_principal = round(outstanding_principal - principal_component, 2)

        schedule.append({
            "emi_number": emi_number,
            "due_date": due_date.strftime("%Y-%m-%d"),
            "amount_due": emi_amount_final,
            "principal_component": principal_component,
            "interest_component": interest_component,
            "amount_paid": 0,
            "payment_date": None,
            "payment_status": "UPCOMING",  # UPCOMING | DUE | PAID | OVERDUE
            "days_overdue": 0,
            "late_charge": 0,
        })

        # Next EMI due date = same day, next month.
        month = due_date.month + 1
        year = due_date.year + (1 if month > 12 else 0)
        month = 1 if month > 12 else month
        try:
            due_date = due_date.replace(year=year, month=month)
        except ValueError:
            # e.g. due date was the 31st and next month has 30 days
            due_date = due_date.replace(year=year, month=month, day=28)

    return schedule
