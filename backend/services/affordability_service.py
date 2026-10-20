"""
services/affordability_service.py
------------------------------------
Purpose:
    Implements Model 2 (requirement #4). For every product marked
    "Potentially Eligible" by eligibility_service, this computes an
    estimated EMI (using the product's mid-point interest rate) and
    asks Model 2 whether that EMI, layered on top of the user's existing
    obligations and repayment history, looks financially manageable.
"""

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml"))
from predict_affordability import predict_affordability  # noqa: E402
from services.emi_service import calculate_emi


def evaluate_affordability(credit_profile: dict, application: dict, eligible_products: list) -> list:
    """
    Mutates/returns a list of products (only the "Potentially Eligible" ones
    need affordability results, but we still ATTACH info for the others so
    the frontend can render one unified list without extra lookups).
    """
    results = []
    for product in eligible_products:
        if product["eligibility_status"] != "Potentially Eligible":
            product["affordability_result"] = None
            product["affordability_probability"] = None
            product["estimated_emi"] = None
            results.append(product)
            continue

        mid_rate = (product["interest_rate_min"] + product["interest_rate_max"]) / 2
        amount = application.get("loan_amount", product.get("min_amount"))
        tenure = application.get("loan_tenure", product.get("min_tenure"))
        estimated_emi = calculate_emi(amount, mid_rate, tenure)

        app_with_rate = {**application, "proposed_rate": mid_rate}
        afford_result, afford_probability = predict_affordability(credit_profile, app_with_rate, estimated_emi)

        product["affordability_result"] = afford_result
        product["affordability_probability"] = afford_probability
        product["estimated_emi"] = estimated_emi
        product["applied_interest_rate"] = mid_rate
        results.append(product)

    return results
