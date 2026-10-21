"""
services/explainability_service.py
------------------------------------
Generates model explanations using permutation feature importance
(scipy/sklearn) and the trained model's coefficient / feature_importance_
arrays. No SHAP required  -  the LogisticRegression coefficients give us
directional importance without additional dependencies.

For each model, returns:
  - top_factors: list of { feature, value, description, direction, strength }
  - supporting_factors: features with positive/eligible contribution
  - concerning_factors: features with negative/at-risk contribution
  - explanation_method: string label
"""

import joblib
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL1_PATH  = BASE_DIR / "ml" / "models" / "eligibility_model.joblib"
MODEL2_PATH  = BASE_DIR / "ml" / "models" / "affordability_model.joblib"
SCALER1_PATH = BASE_DIR / "ml" / "models" / "eligibility_preprocessor.joblib"
SCALER2_PATH = BASE_DIR / "ml" / "models" / "affordability_preprocessor.joblib"


# ??? Descriptions for human-readable output ??????????????????????????????????

ELIGIBILITY_DESCRIPTIONS = {
    "age":             "Applicant age in years",
    "education_enc":   "Education level (Graduate = 0, Not Graduate = 1)",
    "employment_enc":  "Employment type (Salaried=0, Self-Employed=1, Business=2)",
    "annual_income":   "Declared annual income (INR)",
    "dependents":      "Number of financial dependents",
    "cibil_score":     "Credit Information Bureau (India) Limited score (300-900)",
    "existing_loans":  "Number of currently active loan obligations",
    "outstanding_debt":"Total outstanding debt principal (INR)",
    "loan_amount":     "Requested loan principal (INR)",
    "loan_tenure":     "Requested repayment tenure (months)",
}

AFFORDABILITY_DESCRIPTIONS = {
    "monthly_income":   "Declared monthly take-home income (INR)",
    "dependents":       "Number of financial dependents",
    "existing_loans":   "Number of currently active loan obligations",
    "current_emi":      "Total existing monthly EMI obligations (INR)",
    "outstanding_debt": "Total outstanding debt principal (INR)",
    "previous_loans":   "Number of historical loan records",
    "missed_payments":  "Number of missed payment incidents on record",
    "late_payments":    "Number of late payment incidents on record",
    "proposed_amount":  "Proposed new loan principal (INR)",
    "proposed_rate":    "Proposed annual interest rate (%)",
    "proposed_tenure":  "Proposed repayment tenure (months)",
    "proposed_emi":     "Calculated monthly EMI for the proposed loan (INR)",
    "emi_income_ratio": "Ratio of total EMI to monthly income (decimal)",
}

# ??? Helpers ?????????????????????????????????????????????????????????????????

def _load_bundle(path, scaler_path):
    try:
        bundle = joblib.load(path)
        scaler = joblib.load(scaler_path)
        return bundle, scaler
    except Exception as e:
        return None, None


def _logistic_direction(coef_val: float) -> str:
    """
    For LogisticRegression, positive coefficient -> increases probability
    of the positive class (Eligible / Manageable). Negative -> decreases.
    """
    if coef_val > 0.01:
        return "positive"   # pushes toward Eligible/Manageable
    elif coef_val < -0.01:
        return "negative"   # pushes toward Not Eligible/Not Manageable
    return "neutral"


def _strength_label(abs_val: float) -> str:
    if abs_val >= 0.3:  return "Strong"
    if abs_val >= 0.1:  return "Moderate"
    return "Weak"


# ??? Model 1 explainability ???????????????????????????????????????????????????

def explain_eligibility(feature_values: list, feature_names: list) -> dict:
    """
    Returns feature importance for Model 1 eligibility prediction.
    Uses LogisticRegression coefficients (normalized).
    """
    bundle, scaler = _load_bundle(MODEL1_PATH, SCALER1_PATH)
    if bundle is None:
        return {"error": "Model not loaded", "factors": []}

    model = bundle["model"]
    method = "Logistic Regression Coefficients"

    # Get coefficients (class 1 = Eligible)
    if hasattr(model, "coef_"):
        raw_coefs = model.coef_[0]
    elif hasattr(model, "feature_importances_"):
        raw_coefs = model.feature_importances_
        method = "Tree Feature Importances"
    else:
        return {"error": "Model has no explainability attributes", "factors": []}

    # Normalise absolute values for display
    abs_coefs = np.abs(raw_coefs)
    max_abs   = abs_coefs.max() if abs_coefs.max() > 0 else 1.0
    norm_strengths = abs_coefs / max_abs

    factors = []
    for i, feat in enumerate(feature_names):
        coef = raw_coefs[i]
        val  = feature_values[i] if i < len(feature_values) else None
        direction = _logistic_direction(coef) if hasattr(model, "coef_") else "info"
        strength_score = float(norm_strengths[i])
        factors.append({
            "feature":      feat,
            "display_name": feat.replace("_enc", "").replace("_", " ").title(),
            "value":        round(float(val), 4) if val is not None else None,
            "description":  ELIGIBILITY_DESCRIPTIONS.get(feat, feat),
            "direction":    direction,
            "strength":     _strength_label(strength_score),
            "strength_score": round(strength_score, 4),
            "raw_coef":     round(float(coef), 6),
        })

    factors.sort(key=lambda x: x["strength_score"], reverse=True)

    supporting  = [f for f in factors if f["direction"] == "positive"][:5]
    concerning  = [f for f in factors if f["direction"] == "negative"][:5]

    return {
        "explanation_method": method,
        "method_note": (
            "Positive coefficient -> feature increases probability of 'Eligible'. "
            "Negative -> decreases. Strength is relative (normalised). "
            "Direction indicates statistical association in the training data, "
            "not causal evidence."
        ),        "top_factors":       factors[:7],
        "supporting_factors": supporting,
        "concerning_factors": concerning,
        "all_factors":        factors,
    }


# ??? Model 2 explainability ???????????????????????????????????????????????????

def explain_affordability(feature_values: list, feature_names: list) -> dict:
    """
    Returns feature importance for Model 2 affordability prediction.
    """
    bundle, scaler = _load_bundle(MODEL2_PATH, SCALER2_PATH)
    if bundle is None:
        return {"error": "Model not loaded", "factors": []}

    model = bundle["model"]
    method = "Logistic Regression Coefficients"

    if hasattr(model, "coef_"):
        raw_coefs = model.coef_[0]
    elif hasattr(model, "feature_importances_"):
        raw_coefs = model.feature_importances_
        method = "Tree Feature Importances"
    else:
        return {"error": "Model has no explainability attributes", "factors": []}

    abs_coefs    = np.abs(raw_coefs)
    max_abs      = abs_coefs.max() if abs_coefs.max() > 0 else 1.0
    norm_strengths = abs_coefs / max_abs

    factors = []
    for i, feat in enumerate(feature_names):
        coef = raw_coefs[i]
        val  = feature_values[i] if i < len(feature_values) else None
        direction = _logistic_direction(coef) if hasattr(model, "coef_") else "info"
        strength_score = float(norm_strengths[i])
        factors.append({
            "feature":      feat,
            "display_name": feat.replace("_enc", "").replace("_", " ").title(),
            "value":        round(float(val), 4) if val is not None else None,
            "description":  AFFORDABILITY_DESCRIPTIONS.get(feat, feat),
            "direction":    direction,
            "strength":     _strength_label(strength_score),
            "strength_score": round(strength_score, 4),
            "raw_coef":     round(float(coef), 6),
        })

    factors.sort(key=lambda x: x["strength_score"], reverse=True)
    supporting = [f for f in factors if f["direction"] == "positive"][:5]
    concerning = [f for f in factors if f["direction"] == "negative"][:5]

    return {
        "explanation_method": method,
        "method_note": (
            "Positive coefficient -> feature increases probability of 'Manageable'. "
            "Negative -> decreases. Strength is relative. "
            "These are statistical associations from training data, not causal claims."
        ),
        "top_factors":       factors[:7],
        "supporting_factors": supporting,
        "concerning_factors": concerning,
        "all_factors":        factors,
    }


# ??? Historical repayment analysis ???????????????????????????????????????????

def analyse_repayment_history(credit_profile: dict) -> dict:
    """
    Uses the credit profile fields (missed_payments, late_payments, etc.)
    which are filled from the user's self-declared profile or seeded from
    historical_loans.csv. Falls back gracefully if fields are absent.
    """
    missed  = int(credit_profile.get("missed_payments") or 0)
    late    = int(credit_profile.get("late_payments") or 0)
    previous = int(credit_profile.get("previous_loans") or 0)
    avg_days_late = float(credit_profile.get("average_days_late") or 0)
    existing_loans = int(credit_profile.get("existing_loans") or 0)

    # Compute payment completion ratio from profile data where possible
    if previous > 0:
        # Assume each historical loan had at least 1 due installment
        # Late/missed count as "problematic" but not "unpaid"
        total_due = max(previous * 12, missed + late + 1)  # rough proxy
        paid_est  = total_due - missed
        comp_calc = {"paid_est": paid_est, "total_due": total_due,
                     "ratio_pct": round((paid_est / total_due) * 100, 1)}
    else:
        comp_calc = None

    # Qualitative summary
    if previous == 0:
        summary = "No historical loan records available in profile."
        quality = "neutral"
    elif missed == 0 and late == 0:
        summary = "Payment history appears clean  -  no missed or late payments on record."
        quality = "positive"
    elif missed > 0:
        summary = f"{missed} missed payment(s) and {late} late payment(s) noted."
        quality = "warning"
    else:
        summary = f"{late} late payment(s) noted; no missed payments."
        quality = "caution"

    return {
        "previous_loans":           previous,
        "existing_loans":           existing_loans,
        "missed_payments":          missed,
        "late_payments":            late,
        "average_days_late":        avg_days_late,
        "payment_completion":       comp_calc,
        "quality_label":            quality,
        "summary":                  summary,
        "note": (
            "This analysis is based on the credit profile fields. "
            "Detailed per-installment history is available if the user's "
            "historical loan IDs are linked in the installment_payments collection."
        ),
    }
