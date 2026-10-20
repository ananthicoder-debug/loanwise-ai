"""
services/calculation_service.py
---------------------------------
Single source of truth for all financial calculations used by the
assessment report, API responses, and calculation trace.

Rules:
  - Every function returns both the result AND the trace dict so the
    API response and printed report always use the same numbers.
  - Division-by-zero is handled explicitly; result is None with a note.
  - Do not invent values for missing inputs.
"""

from datetime import datetime, timezone
from typing import Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── EMI formula (reducing balance) ─────────────────────────────────────────

def calculate_emi_with_trace(
    principal: float,
    annual_rate_pct: float,
    tenure_months: int,
) -> dict:
    """
    EMI = P × r × (1 + r)^n / ((1 + r)^n − 1)
    Returns { result, trace, steps }.
    """
    if principal <= 0 or tenure_months <= 0:
        return {
            "result": None,
            "note": "Cannot calculate: principal or tenure is zero/negative.",
            "trace": None,
        }

    r = (annual_rate_pct / 12.0) / 100.0

    if r == 0:
        emi = round(principal / tenure_months, 2)
        factor = 1.0
        steps = [
            f"Monthly rate r = {annual_rate_pct}% / 12 / 100 = 0 (zero-interest case)",
            f"EMI = P / n = {principal:,.2f} / {tenure_months} = {emi:,.2f}",
        ]
    else:
        factor = (1 + r) ** tenure_months
        emi = round(principal * r * factor / (factor - 1), 2)
        steps = [
            f"r = {annual_rate_pct}% ÷ 12 ÷ 100 = {r:.6f}",
            f"(1 + r)^n = (1 + {r:.6f})^{tenure_months} = {factor:.6f}",
            f"EMI = {principal:,.2f} × {r:.6f} × {factor:.6f} / ({factor:.6f} - 1)",
            f"EMI = {emi:,.2f}",
        ]

    total_payment = round(emi * tenure_months, 2)
    total_interest = round(total_payment - principal, 2)

    trace = {
        "calculation_name": "proposed_emi",
        "formula": "P × r × (1 + r)^n / ((1 + r)^n − 1)",
        "formula_note": "Monthly reducing-balance EMI formula",
        "inputs": {
            "principal": principal,
            "annual_rate_pct": annual_rate_pct,
            "tenure_months": tenure_months,
        },
        "derived_values": {
            "monthly_rate_r": round(r, 8),
            "compound_factor": round(factor, 6),
            "total_payment": total_payment,
            "total_interest": total_interest,
        },
        "result": emi,
        "unit": "INR / month",
        "steps": steps,
        "rounding": "2 decimal places",
        "calculated_at": _now(),
    }
    return {"result": emi, "trace": trace,
            "total_payment": total_payment, "total_interest": total_interest}


# ─── Ratio calculations ───────────────────────────────────────────────────────

def emi_burden_with_trace(existing_emi: float, monthly_income: float) -> dict:
    """Existing EMI Burden = (Existing EMI / Monthly Income) × 100"""
    name = "existing_emi_burden"
    if monthly_income <= 0:
        return {"result": None, "trace": None,
                "note": "Cannot calculate: monthly income is zero."}
    result = round((existing_emi / monthly_income) * 100, 2)
    trace = {
        "calculation_name": name,
        "formula": "(existing_emi / monthly_income) × 100",
        "inputs": {"existing_emi": existing_emi, "monthly_income": monthly_income},
        "derived_values": {},
        "result": result,
        "unit": "percent",
        "steps": [
            f"({existing_emi:,.2f} / {monthly_income:,.2f}) × 100 = {result:.2f}%"
        ],
        "rounding": "2 decimal places",
        "calculated_at": _now(),
    }
    return {"result": result, "trace": trace}


def total_emi_ratio_with_trace(
    existing_emi: float,
    proposed_emi: float,
    monthly_income: float,
) -> dict:
    """Total EMI-to-Income Ratio = (Existing EMI + Proposed EMI) / Monthly Income × 100"""
    name = "total_emi_to_income_ratio"
    total_emi = existing_emi + proposed_emi
    if monthly_income <= 0:
        return {"result": None, "total_emi": total_emi, "trace": None,
                "note": "Cannot calculate: monthly income is zero."}
    result = round((total_emi / monthly_income) * 100, 2)
    trace = {
        "calculation_name": name,
        "formula": "((existing_emi + proposed_emi) / monthly_income) × 100",
        "inputs": {
            "existing_emi": existing_emi,
            "proposed_emi": proposed_emi,
            "monthly_income": monthly_income,
        },
        "derived_values": {"total_emi": round(total_emi, 2)},
        "result": result,
        "unit": "percent",
        "steps": [
            f"total_emi = {existing_emi:,.2f} + {proposed_emi:,.2f} = {total_emi:,.2f}",
            f"ratio = ({total_emi:,.2f} / {monthly_income:,.2f}) × 100 = {result:.2f}%",
        ],
        "rounding": "2 decimal places",
        "calculated_at": _now(),
    }
    return {"result": result, "total_emi": round(total_emi, 2), "trace": trace}


def monthly_surplus_with_trace(
    monthly_income: float,
    existing_emi: float,
    proposed_emi: float,
    other_obligations: float = 0.0,
) -> dict:
    """Estimated Surplus = Monthly Income − Existing EMI − Proposed EMI − Other"""
    name = "estimated_monthly_surplus"
    total_deductions = existing_emi + proposed_emi + other_obligations
    surplus = round(monthly_income - total_deductions, 2)
    trace = {
        "calculation_name": name,
        "formula": "monthly_income − existing_emi − proposed_emi − other_obligations",
        "inputs": {
            "monthly_income": monthly_income,
            "existing_emi": existing_emi,
            "proposed_emi": proposed_emi,
            "other_obligations": other_obligations,
        },
        "derived_values": {"total_deductions": round(total_deductions, 2)},
        "result": surplus,
        "unit": "INR",
        "note": (
            "Estimated surplus before unreported living expenses and other obligations. "
            "Do not interpret as disposable income."
        ),
        "steps": [
            f"total_deductions = {existing_emi:,.2f} + {proposed_emi:,.2f} + {other_obligations:,.2f} = {total_deductions:,.2f}",
            f"surplus = {monthly_income:,.2f} − {total_deductions:,.2f} = {surplus:,.2f}",
        ],
        "rounding": "2 decimal places",
        "calculated_at": _now(),
    }
    return {"result": surplus, "trace": trace}


def debt_to_income_with_trace(
    total_monthly_debt_payments: float,
    monthly_income: float,
) -> dict:
    """DTI = (Total Monthly Debt Payments / Monthly Income) × 100"""
    name = "debt_to_income_ratio"
    if monthly_income <= 0:
        return {"result": None, "trace": None,
                "note": "Cannot calculate: monthly income is zero."}
    result = round((total_monthly_debt_payments / monthly_income) * 100, 2)
    trace = {
        "calculation_name": name,
        "formula": "(total_monthly_debt_payments / monthly_income) × 100",
        "inputs": {
            "total_monthly_debt_payments": total_monthly_debt_payments,
            "monthly_income": monthly_income,
        },
        "derived_values": {},
        "result": result,
        "unit": "percent",
        "note": "Uses total monthly debt payments (existing EMI), not outstanding principal balance.",
        "steps": [
            f"({total_monthly_debt_payments:,.2f} / {monthly_income:,.2f}) × 100 = {result:.2f}%"
        ],
        "rounding": "2 decimal places",
        "calculated_at": _now(),
    }
    return {"result": result, "trace": trace}


def annual_income_with_trace(monthly_income: float) -> dict:
    """Annual Income = Monthly Income × 12"""
    result = round(monthly_income * 12, 2)
    trace = {
        "calculation_name": "annual_income",
        "formula": "monthly_income × 12",
        "inputs": {"monthly_income": monthly_income},
        "derived_values": {},
        "result": result,
        "unit": "INR / year",
        "steps": [f"{monthly_income:,.2f} × 12 = {result:,.2f}"],
        "rounding": "2 decimal places",
        "calculated_at": _now(),
    }
    return {"result": result, "trace": trace}


def payment_completion_ratio_with_trace(
    paid_installments: int,
    total_due_installments: int,
) -> dict:
    """Payment Completion Ratio = (Paid / Due) × 100"""
    name = "payment_completion_ratio"
    if total_due_installments <= 0:
        return {"result": None, "trace": None,
                "note": "No due installments to calculate from."}
    result = round((paid_installments / total_due_installments) * 100, 1)
    trace = {
        "calculation_name": name,
        "formula": "(paid_installments / total_due_installments) × 100",
        "inputs": {
            "paid_installments": paid_installments,
            "total_due_installments": total_due_installments,
        },
        "derived_values": {},
        "result": result,
        "unit": "percent",
        "note": "Denominator is the count of installments that were due (past due date), not total schedule.",
        "steps": [
            f"({paid_installments} / {total_due_installments}) × 100 = {result:.1f}%"
        ],
        "rounding": "1 decimal place",
        "calculated_at": _now(),
    }
    return {"result": result, "trace": trace}


# ─── Full calculation worksheet ───────────────────────────────────────────────

def build_full_calculation_worksheet(
    credit_profile: dict,
    application: dict,
    proposed_emi: Optional[float] = None,
    proposed_rate: Optional[float] = None,
) -> dict:
    """
    Build the complete calculation worksheet from actual applicant values.
    Returns a dict with all calculation traces and summary values.
    """
    monthly_income = float(credit_profile.get("monthly_income") or 0)
    existing_emi   = float(
        credit_profile.get("existing_emi") or
        credit_profile.get("current_emi") or 0
    )
    outstanding_debt = float(credit_profile.get("outstanding_debt") or 0)
    loan_amount      = float(application.get("loan_amount") or 0)
    loan_tenure      = int(application.get("loan_tenure") or 0)

    # Proposed rate: try application, fall back to 12% representative rate
    rate = float(
        proposed_rate or
        application.get("proposed_rate") or
        application.get("interest_rate") or
        12.0
    )

    # 1. Annual income
    ann = annual_income_with_trace(monthly_income)

    # 2. Proposed EMI
    if proposed_emi is None:
        emi_calc = calculate_emi_with_trace(loan_amount, rate, loan_tenure)
        proposed_emi_val = emi_calc.get("result") or 0.0
    else:
        proposed_emi_val = float(proposed_emi)
        emi_calc = calculate_emi_with_trace(loan_amount, rate, loan_tenure)

    # 3. Existing EMI burden
    burden = emi_burden_with_trace(existing_emi, monthly_income)

    # 4. Total EMI ratio
    total_ratio = total_emi_ratio_with_trace(existing_emi, proposed_emi_val, monthly_income)

    # 5. Monthly surplus
    surplus = monthly_surplus_with_trace(monthly_income, existing_emi, proposed_emi_val)

    # 6. DTI (using existing EMI as proxy for monthly debt payment)
    dti = debt_to_income_with_trace(existing_emi, monthly_income)

    return {
        "annual_income":            ann,
        "proposed_emi":             emi_calc,
        "existing_emi_burden":      burden,
        "total_emi_ratio":          total_ratio,
        "monthly_surplus":          surplus,
        "debt_to_income_ratio":     dti,
        # Convenience summary (all results in one flat dict)
        "summary": {
            "monthly_income":           monthly_income,
            "annual_income":            ann["result"],
            "existing_emi":             existing_emi,
            "outstanding_debt":         outstanding_debt,
            "loan_amount":              loan_amount,
            "loan_tenure_months":       loan_tenure,
            "applied_rate_pct":         rate,
            "proposed_emi":             proposed_emi_val,
            "total_emi":                total_ratio.get("total_emi"),
            "existing_emi_burden_pct":  burden.get("result"),
            "total_emi_ratio_pct":      total_ratio.get("result"),
            "monthly_surplus":          surplus.get("result"),
            "debt_to_income_pct":       dti.get("result"),
            "total_scheduled_repayment": emi_calc.get("total_payment"),
            "total_estimated_interest":  emi_calc.get("total_interest"),
        },
    }
