"""
services/eligibility_service.py
---------------------------------
Purpose:
    Implements requirement #3's two-step eligibility logic:

        ELIGIBILITY MODEL RESULT (applicant-level, Model 1)
                        +
        PRODUCT ELIGIBILITY RULES (from loan_products, admin-managed)
                        =
        "Potentially Eligible" or "Not Eligible" PER PRODUCT

    The ML model never invents lender/product names - it only scores the
    applicant. This service is what maps that score onto the real
    MongoDB `loan_products` catalogue.
"""

from database.mongodb import collections
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml"))
from predict_eligibility import predict_eligibility  # noqa: E402


def evaluate_products_for_application(credit_profile: dict, application: dict) -> dict:
    """
    Returns:
        {
          "model_1": {"result": "Eligible", "probability": 0.91},
          "products": [ {..product.., "eligibility_status": "Potentially Eligible"/"Not Eligible",
                          "rule_reasons": [...]}, ... ]   # ALL active products in the category
        }
    Per requirement #6, we NEVER hide products - we mark each one.
    """
    model_result, model_probability = predict_eligibility(credit_profile, application)

    category = application.get("loan_category")
    candidate_products = list(collections["loan_products"].find({
        "loan_category": category,
        "is_active": True,
    }))

    # Look up lender names once (avoids N+1 queries in the loop below).
    lender_ids = {p["lender_id"] for p in candidate_products}
    lenders_by_id = {
        l["_id"]: l["lender_name"]
        for l in collections["lenders"].find({"_id": {"$in": list(lender_ids)}})
    }

    evaluated = []
    for product in candidate_products:
        product["lender_name"] = lenders_by_id.get(product["lender_id"], "Unknown Lender")
        reasons = []
        rule_pass = True

        amount = application.get("loan_amount", 0)
        tenure = application.get("loan_tenure", 0)

        if amount < product.get("min_amount", 0) or amount > product.get("max_amount", float("inf")):
            rule_pass = False
            reasons.append(
                f"Requested amount must be between {product.get('min_amount')} and {product.get('max_amount')}."
            )
        if tenure < product.get("min_tenure", 0) or tenure > product.get("max_tenure", 999):
            rule_pass = False
            reasons.append(
                f"Tenure must be between {product.get('min_tenure')} and {product.get('max_tenure')} months."
            )
        if credit_profile.get("annual_income", 0) < product.get("minimum_income", 0):
            rule_pass = False
            reasons.append(f"Minimum annual income required: {product.get('minimum_income')}.")
        if credit_profile.get("cibil_score", 0) < product.get("minimum_cibil", 0):
            rule_pass = False
            reasons.append(f"Minimum CIBIL score required: {product.get('minimum_cibil')}.")

        model_pass = model_result == "Eligible"
        if not model_pass:
            reasons.append("AI eligibility model estimates this applicant profile as high-risk for this loan shape.")

        final_status = "Potentially Eligible" if (rule_pass and model_pass) else "Not Eligible"

        product["_id"] = str(product["_id"])
        product["lender_id"] = str(product["lender_id"])
        product["eligibility_status"] = final_status
        product["rule_reasons"] = reasons
        evaluated.append(product)

    return {
        "model_1": {"result": model_result, "probability": model_probability},
        "products": evaluated,
    }
