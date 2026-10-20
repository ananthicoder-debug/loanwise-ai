"""
services/report_service.py
---------------------------
Generates the personalized 'My Loan Eligibility and Financial Affordability Report'
after a user runs eligibility + affordability checks.

This service extends the existing report with:
 - Full calculation traces from calculation_service
 - Feature importance from explainability_service
 - Historical repayment analysis

Stored in MongoDB collection: financial_analysis_reports
"""

from datetime import datetime, timezone
from bson import ObjectId
from database.mongodb import collections
from services.calculation_service import build_full_calculation_worksheet
from services.explainability_service import analyse_repayment_history


# ─── Main report generator ─────────────────────────────────────────────────

def generate_report(user_id: str, application_id: str) -> dict:
    """
    Generate and save a full personalized financial analysis report.
    Returns the complete report dict.
    """
    uid = ObjectId(user_id)
    aid = ObjectId(application_id)

    # Load all required data
    user = collections["users"].find_one({"_id": uid})
    credit = collections["credit_profiles"].find_one({"user_id": uid})
    application = collections["loan_applications"].find_one({"_id": aid, "user_id": uid})
    prediction = collections["predictions"].find_one({"application_id": aid})
    recs = list(collections["recommendations"].find({"application_id": aid}).sort("match_score", -1).limit(3))

    if not user or not credit or not application:
        raise ValueError("User profile or application not found. Please complete your profile first.")

    if not prediction:
        raise ValueError("No prediction found for this application. Run eligibility check first.")

    # ── Section A: Applicant Summary ────────────────────────────────────────
    monthly_income = float(credit.get("monthly_income") or credit.get("Monthly_Income") or 0)
    existing_emi   = float(credit.get("existing_emi") or credit.get("current_emi") or credit.get("Existing_Emi_Amount") or 0)
    outstanding    = float(credit.get("outstanding_debt") or credit.get("Outstanding_Debt") or 0)
    cibil          = int(credit.get("cibil_score") or credit.get("CIBIL_Score") or 0)
    dependents     = int(credit.get("dependents") or credit.get("Number_of_Dependents") or 0)
    age            = int(credit.get("age") or credit.get("Age") or 0)
    existing_loans = int(credit.get("existing_loans") or credit.get("Existing_Loan_Count") or 0)
    missed         = int(credit.get("missed_payments") or credit.get("Missed_Payment_Count") or 0)
    late           = int(credit.get("late_payments") or credit.get("Late_Payment_Count") or 0)
    employment     = credit.get("employment_type") or credit.get("Employment_Type") or "Not specified"

    loan_amount    = float(application.get("loan_amount") or 0)
    loan_tenure    = int(application.get("loan_tenure") or 0)
    loan_category  = application.get("loan_category") or ""

    section_a = {
        "applicant_name":     user.get("full_name", ""),
        "age":                age,
        "employment_type":    employment,
        "monthly_income":     monthly_income,
        "annual_income":      monthly_income * 12,
        "dependents":         dependents,
        "cibil_score":        cibil,
        "existing_loan_count":existing_loans,
        "existing_emi":       existing_emi,
        "outstanding_debt":   outstanding,
        "requested_category": loan_category,
        "requested_amount":   loan_amount,
        "requested_tenure":   loan_tenure,
        "requested_tenure_months": loan_tenure,
        "assessment_date":    datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }

    # ── Section B: Eligibility Analysis ─────────────────────────────────────
    m1 = prediction.get("model_1", {})
    eligible_count = prediction.get("eligible_count", 0)

    eligibility_factors = []
    if cibil >= 700: eligibility_factors.append("CIBIL score is in a favourable range")
    elif cibil >= 600: eligibility_factors.append("CIBIL score is moderate")
    else: eligibility_factors.append("CIBIL score may require improvement")

    if monthly_income > 0:
        income_to_loan = monthly_income * 12 / max(loan_amount, 1)
        if income_to_loan >= 0.3: eligibility_factors.append("Annual income appears sufficient relative to requested amount")
        else: eligibility_factors.append("Requested amount is significant relative to declared income")

    if existing_loans == 0: eligibility_factors.append("No existing loans — cleaner credit profile")
    elif existing_loans <= 2: eligibility_factors.append(f"{existing_loans} existing loan(s) noted")
    else: eligibility_factors.append(f"{existing_loans} existing loans may affect eligibility")

    conditions_to_verify = [
        "Minimum income requirement varies by lender — verify directly",
        "Age eligibility (typically 21–65) — check with specific lender",
        "Employment type requirements — some products specify salaried/self-employed",
        "Final approval and terms are determined by the lender, not this system",
    ]

    section_b = {
        "eligibility_result":       m1.get("result", "Unknown"),
        "model_confidence_pct":     round(m1.get("probability", 0) * 100),
        "eligible_product_count":   eligible_count,
        "requested_loan_category":  loan_category,
        "requested_amount":         loan_amount,
        "requested_tenure_months":  loan_tenure,
        "eligibility_factors":      eligibility_factors,
        "conditions_to_verify":     conditions_to_verify,
        "disclaimer": "AI-based eligibility estimate — not a lender approval. Final decision rests with the lender.",
    }

    # ── Section C: Affordability Analysis ───────────────────────────────────
    m2 = prediction.get("model_2", {})

    # Calculate EMI for requested loan at average market rate (12%)
    avg_rate = 12.0
    if loan_tenure > 0 and loan_amount > 0:
        r = (avg_rate / 12) / 100
        factor = (1 + r) ** loan_tenure
        proposed_emi = round(loan_amount * r * factor / (factor - 1), 2)
    else:
        proposed_emi = 0.0

    total_emi = existing_emi + proposed_emi
    monthly_surplus = monthly_income - total_emi if monthly_income > 0 else 0
    eti_ratio = round((total_emi / monthly_income) * 100, 1) if monthly_income > 0 else 0
    dti_ratio = round((outstanding / (monthly_income * 12)) * 100, 1) if monthly_income > 0 else 0

    section_c = {
        "monthly_income":          monthly_income,
        "existing_emi":            existing_emi,
        "proposed_emi_estimate":   proposed_emi,
        "total_emi":               total_emi,
        "monthly_surplus_estimate":monthly_surplus,
        "emi_to_income_ratio_pct": eti_ratio,
        "debt_to_income_ratio_pct":dti_ratio,
        "outstanding_debt":        outstanding,
        "missed_payment_count":    missed,
        "late_payment_count":      late,
        "affordability_result":    m2.get("result", "Unknown"),
        "model_confidence_pct":    round(m2.get("probability", 0) * 100),
        "proposed_emi_note": "Estimated at 12% p.a. representative rate. Actual EMI depends on lender rate.",
        "surplus_note": "Monthly surplus is an estimate. Actual disposable income depends on living expenses not captured here.",
    }

    # ── Section D: Financial Observations ───────────────────────────────────
    observations = _generate_observations(section_a, section_c, m1, m2)

    # ── Section D2: Calculation Worksheet ───────────────────────────────────
    try:
        calc_ws = build_full_calculation_worksheet(
            credit, application, proposed_emi=proposed_emi
        )
    except Exception:
        calc_ws = None

    # ── Section D3: Repayment History ───────────────────────────────────────
    try:
        repayment_analysis = analyse_repayment_history(credit)
    except Exception:
        repayment_analysis = None

    # ── Section E: Eligible Products (all) ──────────────────────────────────
    eligible_products = _get_eligible_products(application_id)

    # ── Section F: Recommended Loans (top 3) ────────────────────────────────
    recommended = []
    for rec in recs:
        prod_id = rec.get("product_id")
        product = collections["loan_products"].find_one({"_id": prod_id}) if prod_id else None
        lender  = collections["lenders"].find_one({"_id": product["lender_id"]}) if product else None
        recommended.append({
            "product_name":   rec.get("product_name") or (product["product_name"] if product else ""),
            "lender_name":    rec.get("lender_name") or (lender["lender_name"] if lender else ""),
            "lender_website": rec.get("lender_website") or (lender.get("official_website","") if lender else ""),
            "loan_category":  rec.get("loan_category") or (product["loan_category"] if product else ""),
            "interest_rate_min": product["interest_rate_min"] if product else None,
            "interest_rate_max": product["interest_rate_max"] if product else None,
            "min_amount":     product["min_amount"] if product else None,
            "max_amount":     product["max_amount"] if product else None,
            "min_tenure":     product["min_tenure"] if product else None,
            "max_tenure":     product["max_tenure"] if product else None,
            "processing_fee": product.get("processing_fee","Not specified") if product else "Not specified",
            "official_url":   product.get("official_product_url","") if product else "",
            "verification_status": product.get("verification_status","") if product else "",
            "source_date":    product.get("source_date","") if product else "",
            "estimated_emi":  rec.get("recommended_emi"),
            "match_score":    rec.get("match_score"),
            "reason":         rec.get("reason",""),
            "recommendation_id": str(rec["_id"]),
        })

    # ── Section G: Next Steps ────────────────────────────────────────────────
    next_steps = _generate_next_steps(section_a, section_c, m1, m2, len(recommended))

    # ── Assemble full report ─────────────────────────────────────────────────
    report = {
        "report_title": "My Loan Eligibility and Financial Affordability Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_id":          str(uid),
        "application_id":   str(aid),
        "prediction_id":    str(prediction["_id"]) if prediction.get("_id") else None,
        "model_versions": {"eligibility": "2.0", "affordability": "2.0"},
        "section_a_applicant":      section_a,
        "section_b_eligibility":    section_b,
        "section_c_affordability":  section_c,
        "section_d_observations":   observations,
        "section_d2_calculations":  calc_ws,
        "section_d3_repayment":     repayment_analysis,
        "section_e_eligible_loans": eligible_products,
        "section_f_recommended":    recommended,
        "section_g_next_steps":     next_steps,
        "disclaimer": (
            "This report is generated by LoanWise AI based on the information you provided. "
            "It is not a financial advice document and does not guarantee loan approval. "
            "All model outputs are estimates. Verify all information directly with the lender."
        ),
    }

    # Save to MongoDB
    collections["financial_analysis_reports"].replace_one(
        {"user_id": uid, "application_id": aid},
        {**report, "user_id": uid, "application_id": aid, "prediction_id": prediction.get("_id")},
        upsert=True
    )

    return report


def _generate_observations(section_a, section_c, m1, m2) -> list:
    obs = []
    eti = section_c["emi_to_income_ratio_pct"]
    monthly = section_c["monthly_income"]
    existing_emi = section_c["existing_emi"]
    missed = section_c["missed_payment_count"]
    late   = section_c["late_payment_count"]
    surplus = section_c["monthly_surplus_estimate"]
    cibil  = section_a["cibil_score"]

    if eti <= 30:
        obs.append({"type": "positive", "text": f"EMI-to-income ratio of {eti}% is within a comfortable range, suggesting manageable repayment burden."})
    elif eti <= 50:
        obs.append({"type": "neutral",  "text": f"EMI-to-income ratio of {eti}% is moderate. Ensure sufficient budget remains after EMI payments."})
    else:
        obs.append({"type": "warning",  "text": f"EMI-to-income ratio of {eti}% is high. The proposed loan would create a significant repayment burden."})

    if existing_emi > 0:
        pct = round((existing_emi / max(monthly, 1)) * 100)
        obs.append({"type": "neutral", "text": f"Existing EMI obligations (Rs.{existing_emi:,.0f}/mo) account for {pct}% of declared income before the proposed loan."})

    if surplus > 0:
        obs.append({"type": "positive", "text": f"Estimated monthly surplus of Rs.{surplus:,.0f} after EMI payments. Note: actual disposable income depends on living expenses."})
    else:
        obs.append({"type": "warning",  "text": "Estimated surplus is negative or zero after EMI payments. Review the loan amount or tenure."})

    if missed == 0 and late == 0:
        obs.append({"type": "positive", "text": "No missed or late payments recorded — positive repayment history."})
    elif missed > 0:
        obs.append({"type": "warning",  "text": f"{missed} missed payment(s) on record, which may affect affordability assessment."})
    elif late > 0:
        obs.append({"type": "neutral",  "text": f"{late} late payment(s) noted — minor impact on affordability score."})

    if cibil >= 750:
        obs.append({"type": "positive", "text": f"CIBIL score of {cibil} is excellent, supporting eligibility for most products."})
    elif cibil >= 700:
        obs.append({"type": "positive", "text": f"CIBIL score of {cibil} is good, meeting basic eligibility for most products."})
    elif cibil >= 650:
        obs.append({"type": "neutral",  "text": f"CIBIL score of {cibil} is fair. Some lenders may have higher minimum requirements."})
    else:
        obs.append({"type": "warning",  "text": f"CIBIL score of {cibil} is below typical minimum thresholds for many products."})

    obs.append({"type": "info", "text": "Lender-specific eligibility conditions (minimum income, employment type, age) require direct verification with each lender."})
    return obs


def _get_eligible_products(application_id) -> list:
    """Return up to 10 eligible products for the report (all categories)."""
    aid = ObjectId(application_id) if isinstance(application_id, str) else application_id
    application = collections["loan_applications"].find_one({"_id": aid})
    if not application:
        return []

    category = application.get("loan_category")
    products = list(collections["loan_products"].find({"loan_category": category, "is_active": True}))
    lender_ids = {p["lender_id"] for p in products}
    lenders_by_id = {l["_id"]: l for l in collections["lenders"].find({"_id": {"$in": list(lender_ids)}})}

    result = []
    for p in products[:15]:
        lender = lenders_by_id.get(p.get("lender_id"), {})
        result.append({
            "product_name":    p.get("product_name",""),
            "lender_name":     lender.get("lender_name",""),
            "lender_website":  lender.get("official_website",""),
            "loan_category":   p.get("loan_category",""),
            "interest_rate_min": p.get("interest_rate_min"),
            "interest_rate_max": p.get("interest_rate_max"),
            "min_amount":      p.get("min_amount"),
            "max_amount":      p.get("max_amount"),
            "min_tenure":      p.get("min_tenure"),
            "max_tenure":      p.get("max_tenure"),
            "processing_fee":  p.get("processing_fee","Not publicly specified"),
            "official_url":    p.get("official_product_url",""),
            "verification_status": p.get("verification_status",""),
            "source_date":     p.get("source_date",""),
            "product_id":      str(p["_id"]),
        })
    return result


def _generate_next_steps(section_a, section_c, m1, m2, rec_count) -> list:
    steps = []
    if rec_count > 0:
        steps.append("Review the top recommended loan products in Section F — these appear both eligible and manageable based on your profile.")
    steps.append("Visit the official lender website for each product to verify current eligibility criteria and interest rates.")
    steps.append("Use the EMI Calculator to compare different loan amounts and tenures before deciding.")

    if section_c["emi_to_income_ratio_pct"] > 50:
        steps.append("Consider requesting a lower loan amount or longer tenure to reduce monthly EMI burden.")

    if section_a["cibil_score"] < 700:
        steps.append("Review and improve your CIBIL score before applying — timely payments and reducing existing debt can help.")

    if section_c["outstanding_debt"] > section_a["monthly_income"] * 6:
        steps.append("Consider reducing outstanding debt before adding a new loan obligation.")

    steps.append("Compare the total repayment cost (principal + interest) across multiple products using the Compare Loans feature.")
    steps.append("Verify all information you have submitted is accurate — incorrect data can affect model estimates.")
    steps.append("This report is for reference only. Always consult the lender directly before submitting a formal loan application.")
    return steps


def get_user_reports(user_id: str) -> list:
    """Return all reports for a user, newest first."""
    uid = ObjectId(user_id)
    reports = list(collections["financial_analysis_reports"].find(
        {"user_id": uid}
    ).sort("generated_at", -1).limit(10))
    for r in reports:
        r["_id"] = str(r["_id"])
        r["user_id"] = str(r["user_id"])
        r["application_id"] = str(r["application_id"])
        if r.get("prediction_id"):
            r["prediction_id"] = str(r["prediction_id"])
    return reports
