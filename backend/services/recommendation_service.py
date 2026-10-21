"""
services/recommendation_service.py
-------------------------------------
Rule engine: ELIGIBLE ∩ MANAGEABLE = RECOMMENDED (Top 3 by match score)
ML models score the applicant. The verified catalogue provides actual lenders/products.
"""

from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import collections
from services.eligibility_service import evaluate_products_for_application
from services.affordability_service import evaluate_affordability

# Maximum recommendations to return to user (per requirement — top 3 most suitable)
MAX_RECOMMENDATIONS = 3


def run_full_evaluation(user_id: str, application: dict) -> dict:
    """
    Full pipeline:
      1. Load credit profile
      2. Model 1 -> eligible products (ALL returned in catalogue)
      3. Model 2 -> affordability on eligible subset
      4. Rule engine -> recommended = eligible ∩ manageable, sorted by match score
      5. Return top MAX_RECOMMENDATIONS — the ones best matching user's profile
    """
    credit_profile = collections["credit_profiles"].find_one({"user_id": ObjectId(user_id)})
    if not credit_profile:
        raise ValueError("Please complete your financial/credit profile before checking eligibility.")

    # Load lender websites for enrichment
    lender_websites = {
        l["lender_name"]: l.get("official_website", "")
        for l in collections["lenders"].find({})
    }

    eligibility_output = evaluate_products_for_application(credit_profile, application)
    model_1 = eligibility_output["model_1"]
    all_products = eligibility_output["products"]

    # Attach lender website to every product
    for p in all_products:
        p["lender_website"] = lender_websites.get(p.get("lender_name", ""), "")

    scored_products = evaluate_affordability(credit_profile, application, all_products)

    eligible_products = [p for p in scored_products if p["eligibility_status"] == "Potentially Eligible"]
    manageable_products = [p for p in eligible_products if p.get("affordability_result") == "Manageable"]

    # Model 2 summary
    model_2_probs = [p["affordability_probability"] for p in eligible_products if p.get("affordability_probability") is not None]
    model_2_summary = {
        "name": "Loan Affordability Model",
        "result": "Manageable" if manageable_products else "Not Manageable",
        "probability": round(sum(model_2_probs) / len(model_2_probs), 4) if model_2_probs else 0.0,
    }

    # Score all manageable products by combined match score
    monthly_income = max(credit_profile.get("monthly_income") or credit_profile.get("Monthly_Income") or 1, 1)
    for p in manageable_products:
        p["match_score"] = round(
            (model_1["probability"] * 0.5 + p.get("affordability_probability", 0) * 0.5) * 100
        )
        emi = p.get("estimated_emi", 0) or 0
        p["emi_income_ratio_pct"] = round((emi / monthly_income) * 100)
        p["recommendation_reason"] = _generate_reason(credit_profile, p, model_1)

    # Sort by match_score descending, take top MAX_RECOMMENDATIONS
    manageable_products.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_recommendations = manageable_products[:MAX_RECOMMENDATIONS]

    # Persist predictions
    prediction_doc = {
        "application_id": application["_id"],
        "model_1": {"name": "Loan Eligibility Model", **model_1},
        "model_2": model_2_summary,
        "eligible_count": len(eligible_products),
        "recommended_count": len(top_recommendations),
        "total_manageable_count": len(manageable_products),
        "model_version": "2.0",
        "created_at": datetime.now(timezone.utc),
    }
    collections["predictions"].replace_one(
        {"application_id": application["_id"]}, prediction_doc, upsert=True
    )

    # Persist top 3 recommendations
    collections["recommendations"].delete_many({"application_id": application["_id"]})
    for product in top_recommendations:
        rec_doc = {
            "application_id": application["_id"],
            "product_id": ObjectId(product["_id"]),
            "lender_name": product.get("lender_name", ""),
            "lender_website": product.get("lender_website", ""),
            "product_name": product.get("product_name", ""),
            "loan_category": product.get("loan_category", ""),
            "eligibility_result": "Potentially Eligible",
            "affordability_result": "Manageable",
            "match_score": product["match_score"],
            "recommended_emi": product.get("estimated_emi"),
            "emi_income_ratio_pct": product.get("emi_income_ratio_pct"),
            "reason": product["recommendation_reason"],
            "created_at": datetime.now(timezone.utc),
        }
        result = collections["recommendations"].insert_one(rec_doc)
        product["recommendation_id"] = str(result.inserted_id)

    return {
        "model_1": model_1,
        "model_2": model_2_summary,
        "eligible_count": len(eligible_products),
        "recommended_count": len(top_recommendations),
        "total_manageable": len(manageable_products),
        "eligible_products": group_by_category_and_lender(eligible_products),
        "recommended_products": top_recommendations,
    }


def _generate_reason(credit_profile: dict, product: dict, model_1: dict) -> str:
    """Generate a personalised, data-driven reason for this recommendation."""
    monthly_income = max(credit_profile.get("monthly_income") or
                        credit_profile.get("Monthly_Income") or 1, 1)
    existing_emi = (credit_profile.get("existing_emi") or
                   credit_profile.get("current_emi") or
                   credit_profile.get("Existing_Emi_Amount") or 0)
    proposed_emi = product.get("estimated_emi") or 0
    total_emi = existing_emi + proposed_emi
    emi_pct = round((total_emi / monthly_income) * 100)
    match_score = product.get("match_score", 0)
    missed = (credit_profile.get("missed_payments") or
              credit_profile.get("Missed_Payment_Count") or 0)

    parts = []
    parts.append(f"Estimated total EMI (Rs.{total_emi:,.0f}/mo) is about {emi_pct}% of monthly income")
    if emi_pct <= 40:
        parts.append("which is within a manageable range")
    elif emi_pct <= 55:
        parts.append("which is moderate — worth reviewing your budget")
    else:
        parts.append("which is on the higher side — review carefully")

    if model_1["probability"] >= 0.7:
        parts.append(f"Profile eligibility confidence is {round(model_1['probability']*100)}%")
    if missed == 0:
        parts.append("no missed payments on record")
    elif missed <= 1:
        parts.append("minimal missed payment history")

    parts.append(f"AI match score: {match_score}%")
    return ". ".join(parts) + "."


def group_by_category_and_lender(products: list) -> dict:
    """Build category -> lender -> products hierarchy with counts."""
    grouped: dict = {}
    for product in products:
        category   = product.get("loan_category", "Other")
        lender_name = product.get("lender_name", "Unknown Lender")
        grouped.setdefault(category, {"count": 0, "lenders": {}})
        grouped[category]["count"] += 1
        grouped[category]["lenders"].setdefault(lender_name, {"count": 0, "products": []})
        grouped[category]["lenders"][lender_name]["count"] += 1
        grouped[category]["lenders"][lender_name]["products"].append(product)
    return grouped
    """
    Full pipeline for one loan application:
      1. Load the user's credit profile.
      2. Model 1 -> eligible products (ALL are returned, per #6).
      3. Model 2 -> affordability on the eligible subset.
      4. Rule engine -> recommended subset.
      5. Persist predictions + recommendations.
      6. Return a grouped structure ready for the frontend.
    """
    credit_profile = collections["credit_profiles"].find_one({"user_id": ObjectId(user_id)})
    if not credit_profile:
        raise ValueError("Please complete your financial/credit profile before checking eligibility.")

    eligibility_output = evaluate_products_for_application(credit_profile, application)
    model_1 = eligibility_output["model_1"]
    all_products = eligibility_output["products"]

    scored_products = evaluate_affordability(credit_profile, application, all_products)

    eligible_products = [p for p in scored_products if p["eligibility_status"] == "Potentially Eligible"]
    recommended_products = [p for p in eligible_products if p.get("affordability_result") == "Manageable"]

    # Model 2 summary probability = average of the manageable ones (for the predictions doc)
    model_2_probs = [p["affordability_probability"] for p in eligible_products if p.get("affordability_probability") is not None]
    model_2_summary = {
        "name": "Loan Affordability Model",
        "result": "Manageable" if recommended_products else "Not Manageable",
        "probability": round(sum(model_2_probs) / len(model_2_probs), 4) if model_2_probs else 0.0,
    }

    prediction_doc = {
        "application_id": application["_id"],
        "model_1": {"name": "Loan Eligibility Model", **model_1},
        "model_2": model_2_summary,
        "eligible_count": len(eligible_products),
        "recommended_count": len(recommended_products),
        "model_version": "1.0",
        "created_at": datetime.now(timezone.utc),
    }
    # Upsert (replace) so re-checking eligibility for the same application
    # (e.g. after editing a profile) updates the record instead of piling
    # up duplicates.
    collections["predictions"].replace_one(
        {"application_id": application["_id"]}, prediction_doc, upsert=True
    )
    # Clear any previous recommendations for this application before
    # re-inserting the fresh set below (same reasoning as above).
    collections["recommendations"].delete_many({"application_id": application["_id"]})

    # Persist one recommendation document per recommended product (requirement #25).
    recommendation_ids = {}
    for product in recommended_products:
        match_score = round(
            (model_1["probability"] * 0.5 + product["affordability_probability"] * 0.5) * 100
        )
        ratio_pct = round((product["estimated_emi"] / max(credit_profile.get("monthly_income", 1), 1)) * 100)
        reason = (
            f"Estimated EMI is about {ratio_pct}% of your monthly income, which is within the "
            f"configured affordability range, and your profile matches this product's eligibility criteria."
        )
        rec_doc = {
            "application_id": application["_id"],
            "product_id": ObjectId(product["_id"]),
            "eligibility_result": "Eligible",
            "affordability_result": "Manageable",
            "match_score": match_score,  # NOTE: an AI-assisted match indicator, NOT a lender approval score
            "recommended_emi": product["estimated_emi"],
            "reason": reason,
            "created_at": datetime.now(timezone.utc),
        }
        result = collections["recommendations"].insert_one(rec_doc)
        recommendation_ids[product["_id"]] = str(result.inserted_id)
        product["match_score"] = match_score
        product["recommendation_reason"] = reason
        product["recommendation_id"] = str(result.inserted_id)
        product["emi_income_ratio_pct"] = ratio_pct

    return {
        "model_1": model_1,
        "model_2": model_2_summary,
        "eligible_count": len(eligible_products),
        "recommended_count": len(recommended_products),
        "eligible_products": group_by_category_and_lender(eligible_products),
        "recommended_products": recommended_products,
    }


def group_by_category_and_lender(products: list) -> dict:
    """
    Builds the nested structure required by #6/#7:
        { category: { "count": N, "lenders": { lender_name: {"count": N, "products":[...]} } } }
    Counts are computed here, dynamically, from the actual list - never hardcoded.
    """
    grouped: dict = {}
    for product in products:
        category = product.get("loan_category", "Other")
        lender_name = product.get("lender_name", "Unknown Lender")

        grouped.setdefault(category, {"count": 0, "lenders": {}})
        grouped[category]["count"] += 1

        grouped[category]["lenders"].setdefault(lender_name, {"count": 0, "products": []})
        grouped[category]["lenders"][lender_name]["count"] += 1
        grouped[category]["lenders"][lender_name]["products"].append(product)

    return grouped
