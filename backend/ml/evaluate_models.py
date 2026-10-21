"""
ml/evaluate_models.py
----------------------
Model evaluation utilities.

Loads trained models and reports their saved metrics.
Also runs a set of evaluation scenarios to sanity-check predictions.

Usage:
    python ml/evaluate_models.py
"""

import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent))


def load_saved_metrics():
    """Read saved analysis JSON files produced during training."""
    reports_dir = BASE_DIR.parent / "data" / "reports"
    results = {}
    for fname in ["eligibility_analysis.json", "affordability_analysis.json"]:
        path = reports_dir / fname
        if path.exists():
            with open(path) as f:
                results[fname] = json.load(f)
        else:
            results[fname] = {"error": f"{fname} not found  -  run training first."}
    return results


def run_scenario_predictions():
    """
    Run 10 documented test scenarios to verify model behaviour.
    Returns a list of results.
    """
    from predict_eligibility  import predict_eligibility
    from predict_affordability import predict_affordability
    from services.calculation_service import calculate_emi_with_trace

    scenarios = [
        {
            "label": "S1  -  Low EMI, sufficient income",
            "credit": {"monthly_income": 80000, "annual_income": 960000, "cibil_score": 750,
                       "existing_loans": 0, "existing_emi": 2000, "outstanding_debt": 50000,
                       "dependents": 1, "employment_type": "Salaried", "education": "Graduate",
                       "missed_payments": 0, "late_payments": 0, "previous_loans": 1},
            "app":    {"loan_amount": 300000, "loan_tenure": 36, "loan_category": "Personal Loan"},
        },
        {
            "label": "S2  -  High existing EMI",
            "credit": {"monthly_income": 40000, "annual_income": 480000, "cibil_score": 700,
                       "existing_loans": 3, "existing_emi": 25000, "outstanding_debt": 300000,
                       "dependents": 2, "employment_type": "Salaried", "education": "Graduate",
                       "missed_payments": 0, "late_payments": 0, "previous_loans": 3},
            "app":    {"loan_amount": 200000, "loan_tenure": 24, "loan_category": "Personal Loan"},
        },
        {
            "label": "S3  -  High outstanding debt",
            "credit": {"monthly_income": 50000, "annual_income": 600000, "cibil_score": 680,
                       "existing_loans": 2, "existing_emi": 10000, "outstanding_debt": 1500000,
                       "dependents": 2, "employment_type": "Self-Employed", "education": "Graduate",
                       "missed_payments": 1, "late_payments": 2, "previous_loans": 2},
            "app":    {"loan_amount": 500000, "loan_tenure": 60, "loan_category": "Personal Loan"},
        },
        {
            "label": "S4  -  Very large requested loan",
            "credit": {"monthly_income": 60000, "annual_income": 720000, "cibil_score": 720,
                       "existing_loans": 1, "existing_emi": 5000, "outstanding_debt": 200000,
                       "dependents": 0, "employment_type": "Salaried", "education": "Graduate",
                       "missed_payments": 0, "late_payments": 0, "previous_loans": 1},
            "app":    {"loan_amount": 5000000, "loan_tenure": 240, "loan_category": "Home Loan"},
        },
        {
            "label": "S5  -  Historical late payments",
            "credit": {"monthly_income": 55000, "annual_income": 660000, "cibil_score": 650,
                       "existing_loans": 1, "existing_emi": 8000, "outstanding_debt": 150000,
                       "dependents": 2, "employment_type": "Salaried", "education": "Graduate",
                       "missed_payments": 0, "late_payments": 5, "previous_loans": 2},
            "app":    {"loan_amount": 300000, "loan_tenure": 36, "loan_category": "Personal Loan"},
        },
        {
            "label": "S6  -  Missed payments",
            "credit": {"monthly_income": 45000, "annual_income": 540000, "cibil_score": 620,
                       "existing_loans": 2, "existing_emi": 12000, "outstanding_debt": 200000,
                       "dependents": 3, "employment_type": "Self-Employed", "education": "Not Graduate",
                       "missed_payments": 3, "late_payments": 4, "previous_loans": 3},
            "app":    {"loan_amount": 250000, "loan_tenure": 24, "loan_category": "Personal Loan"},
        },
        {
            "label": "S7  -  No historical data",
            "credit": {"monthly_income": 35000, "annual_income": 420000, "cibil_score": 700,
                       "existing_loans": 0, "existing_emi": 0, "outstanding_debt": 0,
                       "dependents": 0, "employment_type": "Salaried", "education": "Graduate",
                       "missed_payments": 0, "late_payments": 0, "previous_loans": 0},
            "app":    {"loan_amount": 100000, "loan_tenure": 12, "loan_category": "Personal Loan"},
        },
        {
            "label": "S8  -  Missing income (zero income edge case)",
            "credit": {"monthly_income": 0, "annual_income": 0, "cibil_score": 650,
                       "existing_loans": 0, "existing_emi": 0, "outstanding_debt": 0,
                       "dependents": 0, "employment_type": "Salaried", "education": "Graduate",
                       "missed_payments": 0, "late_payments": 0, "previous_loans": 0},
            "app":    {"loan_amount": 100000, "loan_tenure": 12, "loan_category": "Personal Loan"},
        },
        {
            "label": "S9  -  Eligible but Not Manageable (high EMI ratio)",
            "credit": {"monthly_income": 30000, "annual_income": 360000, "cibil_score": 750,
                       "existing_loans": 3, "existing_emi": 20000, "outstanding_debt": 500000,
                       "dependents": 2, "employment_type": "Salaried", "education": "Graduate",
                       "missed_payments": 0, "late_payments": 0, "previous_loans": 3},
            "app":    {"loan_amount": 400000, "loan_tenure": 24, "loan_category": "Personal Loan"},
        },
        {
            "label": "S10  -  Eligible and Manageable (ideal profile)",
            "credit": {"monthly_income": 100000, "annual_income": 1200000, "cibil_score": 800,
                       "existing_loans": 0, "existing_emi": 0, "outstanding_debt": 0,
                       "dependents": 0, "employment_type": "Salaried", "education": "Graduate",
                       "missed_payments": 0, "late_payments": 0, "previous_loans": 2},
            "app":    {"loan_amount": 500000, "loan_tenure": 36, "loan_category": "Personal Loan"},
        },
    ]

    results = []
    print("\n" + "=" * 70)
    print("  SCENARIO PREDICTION TESTS")
    print("=" * 70)

    for sc in scenarios:
        cp  = sc["credit"]
        app = sc["app"]
        r1, p1 = predict_eligibility(cp, app)
        emi_calc = calculate_emi_with_trace(app["loan_amount"], 12.0, app["loan_tenure"])
        proposed_emi = emi_calc.get("result") or 0
        r2, p2 = predict_affordability(cp, app, proposed_emi)
        results.append({
            "label":           sc["label"],
            "m1_result":       r1, "m1_prob": round(p1, 3),
            "m2_result":       r2, "m2_prob": round(p2, 3),
            "proposed_emi":    proposed_emi,
            "monthly_income":  cp["monthly_income"],
            "cibil_score":     cp["cibil_score"],
        })
        print(f"\n  {sc['label']}")
        print(f"    Model 1: {r1:<15} ({p1:.1%})  Model 2: {r2:<18} ({p2:.1%})")
        print(f"    EMI: Rs.{proposed_emi:,.0f}  Income: Rs.{cp['monthly_income']:,}  CIBIL: {cp['cibil_score']}")

    print("\n" + "=" * 70)
    return results


def main():
    print("\n" + "=" * 60)
    print("  LoanWise AI  -  Model Evaluation Report")
    print("=" * 60)

    metrics = load_saved_metrics()
    for fname, data in metrics.items():
        if "error" not in data:
            mp = data.get("model_performance", {})
            print(f"\n  {data.get('dataset', fname)}")
            print(f"    Algorithm:  {mp.get('algorithm', ' - ')}")
            print(f"    Records:    {data.get('total_records', ' - ')} total ({data.get('training_records', ' - ')} train / {data.get('testing_records', ' - ')} test)")
            print(f"    Target:     {data.get('target_column', ' - ')}")
            print(f"    Accuracy:   {mp.get('accuracy', ' - ')}")
            print(f"    F1 Score:   {mp.get('f1_score', ' - ')}")
            print(f"    ROC-AUC:    {mp.get('roc_auc', ' - ')}")
            print(f"    Disclaimer: {data.get('disclaimer', '')}")
        else:
            print(f"\n  ??  {data['error']}")

    run_scenario_predictions()
    print("\n  Evaluation complete.\n")


if __name__ == "__main__":
    main()
