"""
services/assessment_service.py
--------------------------------
Full two-model assessment pipeline with calculation traces,
feature explainability, eligible + recommended product separation,
and observation generation.

Entry points:
  run_full_assessment(user_id, application_id, what_if=None)
  get_assessment_history(user_id)
  get_assessment(assessment_id, user_id)
"""

import sys, os
from datetime import datetime, timezone
from bson import ObjectId
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "ml"))

from database.mongodb import collections
from services.calculation_service import build_full_calculation_worksheet
from services.explainability_service import (
    explain_eligibility, explain_affordability, analyse_repayment_history
)
from services.emi_service import calculate_emi
from services.product_service import get_active_products

# ML model predictors (loaded once at import time in predict_* modules)
from predict_eligibility  import predict_eligibility
from predict_affordability import predict_affordability
from preprocessing import (
    build_eligibility_vector, build_affordability_vector,
    ELIGIBILITY_FEATURES, AFFORDABILITY_FEATURES,
    EDUCATION_MAP, EMPLOYMENT_MAP,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v, default=0.0):
    try:
        return float(v or default)
    except (TypeError, ValueError):
        return default


def _safe_int(v, default=0):
    try:
        return int(v or default)
    except (TypeError, ValueError):
        return default


def _interpret_eti(ratio_pct):
    if ratio_pct is None:
        return "Cannot assess — income data missing."
    if ratio_pct <= 30:
        return f"Comfortable — {ratio_pct:.1f}% of income committed to EMI."
    if ratio_pct <= 45:
        return f"Moderate — {ratio_pct:.1f}% of income committed to EMI. Manageable but worth reviewing."
    if ratio_pct <= 60:
        return f"Elevated — {ratio_pct:.1f}% of income committed to EMI. Repayment burden is significant."
    return f"High — {ratio_pct:.1f}% of income committed to EMI. Consider lower amount or longer tenure."


def _generate_eligibility_observations(credit_profile, application, m1_result, m1_prob, calc_ws) -> list:
    obs = []
    cibil   = _safe_int(credit_profile.get("cibil_score"))
    income  = _safe_float(credit_profile.get("monthly_income"))
    loans   = _safe_int(credit_profile.get("existing_loans"))
    missed  = _safe_int(credit_profile.get("missed_payments"))
    amount  = _safe_float(application.get("loan_amount"))
    ann_inc = calc_ws["summary"].get("annual_income") or (income * 12)
    conf_pct = round(m1_prob * 100)

    if m1_result == "Eligible":
        obs.append({"type": "positive",
            "text": f"The eligibility model estimates a {conf_pct}% probability of matching the eligibility profile in the training data."})
    else:
        obs.append({"type": "warning",
            "text": f"The model estimates a {conf_pct}% probability for the positive class. The submitted profile does not strongly match the eligible pattern in the training data."})

    if cibil >= 750:
        obs.append({"type": "positive", "text": f"CIBIL score of {cibil} is excellent and supports a favourable eligibility estimate."})
    elif cibil >= 700:
        obs.append({"type": "positive", "text": f"CIBIL score of {cibil} is good and meets basic thresholds for most products."})
    elif cibil >= 650:
        obs.append({"type": "neutral",  "text": f"CIBIL score of {cibil} is fair. Some lenders specify higher minimum scores."})
    else:
        obs.append({"type": "warning",  "text": f"CIBIL score of {cibil} is below the 700 threshold commonly required by many lenders."})

    if ann_inc and amount:
        inc_to_loan = ann_inc / max(amount, 1)
        if inc_to_loan >= 0.5:
            obs.append({"type": "positive", "text": "Annual income appears proportionate to the requested loan amount."})
        elif inc_to_loan >= 0.2:
            obs.append({"type": "neutral",  "text": "Requested amount is significant relative to declared annual income."})
        else:
            obs.append({"type": "warning",  "text": "Requested amount is very high relative to declared annual income — lenders typically apply income multiples."})

    if loans == 0:
        obs.append({"type": "positive", "text": "No existing loans — clean credit profile from an obligation standpoint."})
    elif loans <= 2:
        obs.append({"type": "neutral",  "text": f"{loans} existing loan(s) noted. Within a typical manageable range."})
    else:
        obs.append({"type": "warning",  "text": f"{loans} existing loans may signal elevated credit obligation to lenders."})

    if missed > 0:
        obs.append({"type": "warning",  "text": f"{missed} missed payment(s) on the credit profile may negatively influence lender assessment."})

    obs.append({"type": "info",
        "text": "This is a model-based estimate only. Final eligibility is determined by the lender based on their own criteria and documentation review."})
    return obs


def _generate_affordability_observations(credit_profile, calc_ws, m2_result, m2_prob, repayment) -> list:
    obs = []
    eti     = calc_ws["summary"].get("total_emi_ratio_pct")
    surplus = calc_ws["summary"].get("monthly_surplus")
    missed  = _safe_int(credit_profile.get("missed_payments"))
    late    = _safe_int(credit_profile.get("late_payments"))
    conf_pct = round(m2_prob * 100)

    if m2_result == "Manageable":
        obs.append({"type": "positive",
            "text": f"The affordability model estimates a {conf_pct}% probability that the proposed loan is manageable."})
    else:
        obs.append({"type": "warning",
            "text": f"The affordability model estimates a {conf_pct}% probability for the manageable class — indicating potential repayment risk."})

    if eti is not None:
        obs.append({"type": "info", "text": _interpret_eti(eti)})

    if surplus is not None:
        if surplus > 5000:
            obs.append({"type": "positive",
                "text": f"Estimated surplus of Rs.{surplus:,.0f}/month after EMI. Actual surplus depends on living expenses not captured here."})
        elif surplus >= 0:
            obs.append({"type": "neutral",
                "text": f"Estimated surplus of Rs.{surplus:,.0f}/month after EMI is thin — limited financial buffer."})
        else:
            obs.append({"type": "warning",
                "text": f"Estimated surplus is negative (Rs.{surplus:,.0f}/month) — declared EMI obligations exceed income."})

    if missed == 0 and late == 0:
        obs.append({"type": "positive", "text": "No missed or late payments in the profile — positive repayment signal."})
    elif missed > 2:
        obs.append({"type": "warning",  "text": f"{missed} missed payment(s) are a significant concern for repayment feasibility."})
    elif missed > 0 or late > 0:
        obs.append({"type": "neutral",  "text": f"{missed} missed and {late} late payment(s) noted — minor to moderate impact."})

    obs.append({"type": "info",
        "text": "This model cannot guarantee repayment success. Living expenses, unexpected events, and floating rates can affect actual repayment ability."})
    return obs


def _generate_next_steps(m1_result, m2_result, calc_ws, rec_count, cibil) -> list:
    steps = []
    eti   = calc_ws["summary"].get("total_emi_ratio_pct") or 0

    if rec_count > 0:
        steps.append("Review the recommended products — they match both the configured eligibility criteria and the affordability model.")
    steps.append("Visit each lender's official website to verify current rates, eligibility conditions, and required documents.")
    steps.append("Use the EMI Calculator to compare different amounts and tenures before applying.")
    if eti > 50:
        steps.append("Consider requesting a lower loan amount or a longer tenure to bring the EMI-to-income ratio below 50%.")
    if cibil and cibil < 700:
        steps.append("Work on improving your CIBIL score — timely payments on existing loans and reducing outstanding balances help.")
    steps.append("Ensure all submitted profile information (income, EMI, existing loans) is accurate — model estimates are only as reliable as the input data.")
    steps.append("Consult the lender directly before submitting a formal application. This report is for decision support only.")
    return steps


# ─── Main assessment function ─────────────────────────────────────────────────

def run_full_assessment(user_id: str, application: dict, what_if: dict = None) -> dict:
    """
    Runs Model 1 + Model 2 + calculation worksheet + explainability
    + observation generation + eligible/recommended product separation.

    what_if (optional):
      { "loan_amount": ..., "proposed_rate": ..., "loan_tenure": ... }
      When provided, calculations use the what-if values but the
      saved application is NOT modified.
    """
    uid = ObjectId(user_id)
    credit_profile = collections["credit_profiles"].find_one({"user_id": uid})
    if not credit_profile:
        raise ValueError("Credit profile not found. Complete your financial profile first.")

    # Merge what-if overrides for calculation only
    effective_app = dict(application)
    is_what_if = False
    if what_if:
        effective_app.update({k: v for k, v in what_if.items() if v is not None})
        is_what_if = True

    # ── Raw values ────────────────────────────────────────────────────────────
    monthly_income = _safe_float(
        credit_profile.get("monthly_income") or credit_profile.get("Monthly_Income")
    )
    existing_emi = _safe_float(
        credit_profile.get("existing_emi") or credit_profile.get("current_emi") or
        credit_profile.get("Existing_Emi_Amount")
    )
    cibil       = _safe_int(credit_profile.get("cibil_score") or credit_profile.get("CIBIL_Score"), 650)
    dependents  = _safe_int(credit_profile.get("dependents") or credit_profile.get("Number_of_Dependents"))
    existing_loans = _safe_int(credit_profile.get("existing_loans") or credit_profile.get("Existing_Loan_Count"))
    loan_amount = _safe_float(effective_app.get("loan_amount"))
    loan_tenure = _safe_int(effective_app.get("loan_tenure"))
    proposed_rate = _safe_float(effective_app.get("proposed_rate") or effective_app.get("interest_rate"), 12.0)

    # ── Proposed EMI ──────────────────────────────────────────────────────────
    try:
        proposed_emi = calculate_emi(loan_amount, proposed_rate, loan_tenure)
    except Exception:
        proposed_emi = 0.0

    # ── Calculation worksheet ─────────────────────────────────────────────────
    calc_ws = build_full_calculation_worksheet(
        credit_profile, effective_app, proposed_emi, proposed_rate
    )

    # ── Model 1: Eligibility ──────────────────────────────────────────────────
    m1_result, m1_prob = predict_eligibility(credit_profile, effective_app)
    elig_vector = build_eligibility_vector(credit_profile, effective_app)
    elig_explain = explain_eligibility(elig_vector, ELIGIBILITY_FEATURES)
    elig_obs = _generate_eligibility_observations(
        credit_profile, effective_app, m1_result, m1_prob, calc_ws
    )

    # ── Model 2: Affordability ────────────────────────────────────────────────
    m2_result, m2_prob = predict_affordability(credit_profile, effective_app, proposed_emi)
    aff_vector = build_affordability_vector(credit_profile, effective_app, proposed_emi)
    aff_explain = explain_affordability(aff_vector, AFFORDABILITY_FEATURES)
    repayment   = analyse_repayment_history(credit_profile)
    aff_obs     = _generate_affordability_observations(
        credit_profile, calc_ws, m2_result, m2_prob, repayment
    )

    # ── Product matching ──────────────────────────────────────────────────────
    category = effective_app.get("loan_category", "")
    products = list(collections["loan_products"].find({"loan_category": category, "is_active": True}))
    lender_ids = {p.get("lender_id") for p in products if p.get("lender_id")}
    lenders_by_id = {
        l["_id"]: l
        for l in collections["lenders"].find({"_id": {"$in": list(lender_ids)}})
    }

    eligible_products   = []
    recommended_products = []

    for product in products:
        lender = lenders_by_id.get(product.get("lender_id"), {})
        product["lender_name"]    = lender.get("lender_name", "Unknown Lender")
        product["lender_website"] = lender.get("official_website", "")

        # Rule checks
        reasons = []
        rule_pass = True
        if loan_amount < (product.get("min_amount") or 0):
            rule_pass = False
            reasons.append(f"Requested amount Rs.{loan_amount:,.0f} is below minimum Rs.{product.get('min_amount'):,.0f}.")
        if loan_amount > (product.get("max_amount") or float("inf")):
            rule_pass = False
            reasons.append(f"Requested amount Rs.{loan_amount:,.0f} exceeds maximum Rs.{product.get('max_amount'):,.0f}.")
        if loan_tenure < (product.get("min_tenure") or 0):
            rule_pass = False
            reasons.append(f"Tenure {loan_tenure} months is below minimum {product.get('min_tenure')} months.")
        if loan_tenure > (product.get("max_tenure") or 999):
            rule_pass = False
            reasons.append(f"Tenure {loan_tenure} months exceeds maximum {product.get('max_tenure')} months.")
        if credit_profile.get("annual_income", 0) < (product.get("minimum_income") or 0):
            rule_pass = False
            reasons.append(f"Annual income below minimum Rs.{product.get('minimum_income'):,.0f}.")
        if cibil < (product.get("minimum_cibil") or 0):
            rule_pass = False
            reasons.append(f"CIBIL {cibil} below minimum {product.get('minimum_cibil')}.")

        model_pass = (m1_result == "Eligible")
        if not model_pass:
            reasons.append("AI eligibility model does not strongly support this profile for this loan shape.")

        elig_status = "Potentially Eligible" if (rule_pass and model_pass) else "Not Eligible"

        # Estimated EMI at product midpoint rate
        mid_rate = ((product.get("interest_rate_min") or proposed_rate) +
                    (product.get("interest_rate_max") or proposed_rate)) / 2.0
        try:
            est_emi = calculate_emi(loan_amount, mid_rate, loan_tenure)
        except Exception:
            est_emi = proposed_emi

        # Affordability for eligible products only
        afford_result = None
        afford_prob   = None
        if elig_status == "Potentially Eligible":
            app_with_rate = {**effective_app, "proposed_rate": mid_rate}
            afford_result, afford_prob = predict_affordability(
                credit_profile, app_with_rate, est_emi
            )

        p_out = {
            "_id":                  str(product["_id"]),
            "lender_id":            str(product.get("lender_id", "")),
            "lender_name":          product["lender_name"],
            "lender_website":       product["lender_website"],
            "product_name":         product.get("product_name", ""),
            "loan_category":        product.get("loan_category", ""),
            "min_amount":           product.get("min_amount"),
            "max_amount":           product.get("max_amount"),
            "interest_rate_min":    product.get("interest_rate_min"),
            "interest_rate_max":    product.get("interest_rate_max"),
            "min_tenure":           product.get("min_tenure"),
            "max_tenure":           product.get("max_tenure"),
            "processing_fee":       product.get("processing_fee", "Not publicly specified"),
            "official_product_url": product.get("official_product_url", ""),
            "source_date":          product.get("source_date", ""),
            "verification_status":  product.get("verification_status", ""),
            "eligibility_conditions": product.get("eligibility_conditions", []),
            "documents_required":   product.get("documents_required", ""),
            "eligibility_status":   elig_status,
            "rule_reasons":         reasons,
            "applied_interest_rate": round(mid_rate, 2),
            "estimated_emi":        est_emi,
            "affordability_result": afford_result,
            "affordability_probability": round(afford_prob, 4) if afford_prob is not None else None,
        }

        eligible_products.append(p_out)
        if elig_status == "Potentially Eligible" and afford_result == "Manageable":
            match_score = round((m1_prob * 0.5 + (afford_prob or 0) * 0.5) * 100)
            emi_income_pct = round((est_emi / max(monthly_income, 1)) * 100)
            p_out["match_score"] = match_score
            p_out["emi_income_ratio_pct"] = emi_income_pct
            p_out["recommendation_reason"] = (
                f"Estimated EMI Rs.{est_emi:,.0f}/mo is {emi_income_pct}% of income. "
                f"AI match score {match_score}%. Profile matches both eligibility and affordability estimates."
            )
            recommended_products.append(p_out)

    recommended_products.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_recs = recommended_products[:3]

    # ── Next steps ────────────────────────────────────────────────────────────
    next_steps = _generate_next_steps(m1_result, m2_result, calc_ws, len(top_recs), cibil)

    # ── Assemble assessment result ────────────────────────────────────────────
    assessment = {
        "assessment_id":     str(application.get("_id", "")) if not is_what_if else None,
        "is_what_if":        is_what_if,
        "generated_at":      _now_iso(),
        "application_id":    str(application.get("_id", "")),
        "what_if_params":    what_if if is_what_if else None,

        # Applicant summary
        "applicant_summary": {
            "monthly_income":   monthly_income,
            "annual_income":    calc_ws["summary"]["annual_income"],
            "existing_emi":     existing_emi,
            "outstanding_debt": _safe_float(credit_profile.get("outstanding_debt")),
            "cibil_score":      cibil,
            "dependents":       dependents,
            "existing_loans":   existing_loans,
            "employment_type":  credit_profile.get("employment_type", ""),
            "education":        credit_profile.get("education", ""),
            "loan_category":    effective_app.get("loan_category", ""),
            "loan_amount":      loan_amount,
            "loan_tenure":      loan_tenure,
            "proposed_rate":    proposed_rate,
        },

        # Model 1
        "eligibility": {
            "model_name":    "Loan Eligibility Prediction Model",
            "model_version": "2.0",
            "algorithm":     "LogisticRegression (trained on eligibility_dataset.csv)",
            "result":        m1_result,
            "probability":   round(m1_prob, 4),
            "confidence_pct": round(m1_prob * 100),
            "display_result": (
                "Potentially Eligible" if m1_result == "Eligible"
                else "Does Not Match Configured Eligibility Criteria"
            ),
            "result_note": (
                "This is an AI-based eligibility estimate. "
                "It is not an approval or rejection issued by a bank or lender."
            ),
            "explanation": elig_explain,
            "observations": elig_obs,
            "input_features": [
                {
                    "feature": ELIGIBILITY_FEATURES[i],
                    "value":   round(float(elig_vector[i]), 4),
                    "description": _feat_desc(ELIGIBILITY_FEATURES[i], "eligibility"),
                }
                for i in range(len(ELIGIBILITY_FEATURES))
            ],
            "disclaimer": (
                "AI-based eligibility estimate. "
                "Not an approval or rejection from any bank or lender."
            ),
        },

        # Model 2
        "affordability": {
            "model_name":    "Loan Affordability and Repayment Feasibility Model",
            "model_version": "2.0",
            "algorithm":     "LogisticRegression (trained on affordability_dataset.csv)",
            "result":        m2_result,
            "probability":   round(m2_prob, 4),
            "confidence_pct": round(m2_prob * 100),
            "display_result": (
                "Manageable" if m2_result == "Manageable"
                else "Not Manageable — potential repayment burden"
            ),
            "result_note": (
                "This model estimates repayment feasibility based on declared income, "
                "existing obligations, proposed EMI, and payment history. "
                "It cannot guarantee repayment success."
            ),
            "explanation": aff_explain,
            "observations": aff_obs,
            "input_features": [
                {
                    "feature": AFFORDABILITY_FEATURES[i],
                    "value":   round(float(aff_vector[i]), 4),
                    "description": _feat_desc(AFFORDABILITY_FEATURES[i], "affordability"),
                }
                for i in range(len(AFFORDABILITY_FEATURES))
            ],
            "disclaimer": (
                "AI-based affordability estimate. "
                "This model cannot guarantee repayment outcomes."
            ),
        },

        # Calculations
        "calculations": calc_ws,

        # Historical repayment
        "repayment_history": repayment,

        # Products
        "eligible_products":     eligible_products,
        "recommended_products":  top_recs,
        "eligible_count":        len([p for p in eligible_products
                                      if p["eligibility_status"] == "Potentially Eligible"]),
        "recommended_count":     len(top_recs),

        # Next steps
        "next_steps": next_steps,

        # Disclaimer
        "disclaimer": (
            "LoanWise AI — This assessment is based on AI models and the financial information you provided. "
            "It is an estimate for decision-support purposes. "
            "It is not a guarantee of loan approval, a lender's decision, or financial advice. "
            "Final eligibility, pricing, and approval are determined solely by the lender."
        ),
    }

    return assessment


def _feat_desc(feat: str, model_type: str) -> str:
    from services.explainability_service import ELIGIBILITY_DESCRIPTIONS, AFFORDABILITY_DESCRIPTIONS
    if model_type == "eligibility":
        return ELIGIBILITY_DESCRIPTIONS.get(feat, feat)
    return AFFORDABILITY_DESCRIPTIONS.get(feat, feat)


# ─── What-if analysis ────────────────────────────────────────────────────────

def run_what_if(user_id: str, application: dict, what_if: dict) -> dict:
    """
    Runs the assessment with what-if parameters.
    Clearly labeled as a scenario — does not touch saved records.
    """
    result = run_full_assessment(user_id, application, what_if=what_if)
    result["scenario_label"] = (
        f"What-If Scenario: Amount=Rs.{what_if.get('loan_amount', 'unchanged'):,}, "
        f"Rate={what_if.get('proposed_rate', 'unchanged')}%, "
        f"Tenure={what_if.get('loan_tenure', 'unchanged')} months"
    )
    result["scenario_note"] = (
        "This is a recalculated scenario using the values you adjusted. "
        "Your saved application has not been changed. "
        "Calculator outputs reflect the new parameters; "
        "model predictions use the updated values."
    )
    return result
