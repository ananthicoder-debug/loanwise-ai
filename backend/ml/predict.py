"""
ml/predict.py
--------------
Unified prediction interface — convenience wrapper used by tests and
external callers that want both models in one import.

Usage:
    from ml.predict import predict_both

    result = predict_both(credit_profile, application)
    # result["eligibility"]   -> {"result": "Eligible", "probability": 0.91}
    # result["affordability"] -> {"result": "Manageable", "probability": 0.83}
    # result["proposed_emi"]  -> 10036.09
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1]))

from predict_eligibility  import predict_eligibility
from predict_affordability import predict_affordability
from services.emi_service import calculate_emi


def predict_both(credit_profile: dict, application: dict, proposed_rate: float = 12.0) -> dict:
    """
    Run both models for a given credit profile and application.
    Calculates EMI from application parameters and proposed_rate.

    Returns:
        {
            "eligibility":   {"result": str, "probability": float},
            "affordability": {"result": str, "probability": float},
            "proposed_emi":  float,
            "model_version": "2.0",
        }
    """
    loan_amount = float(application.get("loan_amount") or 0)
    tenure      = int(application.get("loan_tenure") or 12)
    rate        = float(
        application.get("proposed_rate") or
        application.get("interest_rate") or
        proposed_rate
    )

    try:
        emi = calculate_emi(loan_amount, rate, tenure)
    except Exception:
        emi = 0.0

    r1, p1 = predict_eligibility(credit_profile, application)
    r2, p2 = predict_affordability(credit_profile, {**application, "proposed_rate": rate}, emi)

    return {
        "eligibility":   {"result": r1, "probability": round(p1, 4)},
        "affordability": {"result": r2, "probability": round(p2, 4)},
        "proposed_emi":  emi,
        "model_version": "2.0",
        "disclaimer": (
            "AI-based estimates. "
            "Not a lender decision or financial guarantee."
        ),
    }
