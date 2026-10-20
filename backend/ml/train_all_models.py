"""
ml/train_all_models.py
-----------------------
Master training orchestration script.

Trains both models in sequence:
  1. Validates all required CSV files exist
  2. Runs data-quality checks
  3. Trains Model 1 (Loan Eligibility)
  4. Trains Model 2 (Loan Affordability)
  5. Saves both models and preprocessing pipelines
  6. Generates performance reports
  7. Prints final training summary

Usage (from backend/ directory):
    python ml/train_all_models.py
Or as a module:
    python -m ml.train_all_models
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR.parent / "data" / "raw"
REPORTS_DIR = BASE_DIR.parent / "data" / "reports"
MODELS_DIR  = BASE_DIR / "models"


# ─── Validation ───────────────────────────────────────────────────────────────

REQUIRED_CSV_FILES = [
    "eligibility_dataset.csv",
    "affordability_dataset.csv",
    "borrowers.csv",
    "historical_loans.csv",
    "installment_payments.csv",
    "lenders.csv",
    "loan_products.csv",
]

REQUIRED_SCHEMAS = {
    "eligibility_dataset.csv": [
        "age", "education", "employment_type", "annual_income", "dependents",
        "cibil_score", "existing_loans", "outstanding_debt",
        "loan_amount", "loan_tenure", "loan_status",
    ],
    "affordability_dataset.csv": [
        "monthly_income", "dependents", "existing_loans", "current_emi",
        "outstanding_debt", "previous_loans", "missed_payments", "late_payments",
        "proposed_amount", "proposed_rate", "proposed_tenure", "proposed_emi",
        "emi_income_ratio", "manageable",
    ],
}


def validate_files():
    print("\n[1] Validating required CSV files...")
    missing = []
    for fname in REQUIRED_CSV_FILES:
        path = DATA_DIR / fname
        if not path.exists():
            missing.append(str(path))
        else:
            print(f"    ✅ {fname}")
    if missing:
        print("\n❌ FATAL: Missing required files:")
        for m in missing:
            print(f"   {m}")
        sys.exit(1)
    print(f"    All {len(REQUIRED_CSV_FILES)} required files found.")


def validate_schemas():
    import pandas as pd
    print("\n[2] Validating dataset schemas...")
    errors = []
    for fname, required_cols in REQUIRED_SCHEMAS.items():
        df = pd.read_csv(DATA_DIR / fname, nrows=3)
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            errors.append(f"{fname} is missing columns: {missing_cols}")
        else:
            print(f"    ✅ {fname}: schema OK ({len(df.columns)} columns)")
    if errors:
        print("\n❌ Schema errors:")
        for e in errors:
            print(f"   {e}")
        sys.exit(1)


def data_quality_check():
    import pandas as pd
    print("\n[3] Data quality checks...")
    for fname in ["eligibility_dataset.csv", "affordability_dataset.csv"]:
        df = pd.read_csv(DATA_DIR / fname)
        rows    = len(df)
        missing = int(df.isnull().sum().sum())
        dupes   = int(df.duplicated().sum())
        print(f"    {fname}: {rows} rows | {missing} missing values | {dupes} duplicates")
        if rows < 100:
            print(f"    ⚠️  WARNING: {fname} has only {rows} records — model may underfit.")
        if missing > rows * 0.1:
            print(f"    ⚠️  WARNING: {fname} has high missing rate ({missing/rows*100:.1f}%).")
    print("    Data quality check complete.")


# ─── Training ─────────────────────────────────────────────────────────────────

def train_model_1():
    print("\n" + "=" * 60)
    print("[4] Training Model 1 — Loan Eligibility Prediction")
    print("=" * 60)
    sys.path.insert(0, str(BASE_DIR))
    sys.path.insert(0, str(BASE_DIR.parent))
    from train_eligibility import train as train_elig
    try:
        acc, f1, roc = train_elig()
        print(f"\n    ✅ Model 1 trained: Acc={acc:.4f}  F1={f1:.4f}  ROC-AUC={roc:.4f}")
        return {"status": "success", "accuracy": acc, "f1": f1, "roc_auc": roc}
    except Exception as e:
        print(f"\n    ❌ Model 1 training FAILED: {e}")
        return {"status": "failed", "error": str(e)}


def train_model_2():
    print("\n" + "=" * 60)
    print("[5] Training Model 2 — Loan Affordability & Repayment Feasibility")
    print("=" * 60)
    from train_affordability import train as train_aff
    try:
        acc, f1, roc = train_aff()
        print(f"\n    ✅ Model 2 trained: Acc={acc:.4f}  F1={f1:.4f}  ROC-AUC={roc:.4f}")
        return {"status": "success", "accuracy": acc, "f1": f1, "roc_auc": roc}
    except Exception as e:
        print(f"\n    ❌ Model 2 training FAILED: {e}")
        return {"status": "failed", "error": str(e)}


# ─── Summary ──────────────────────────────────────────────────────────────────

def print_summary(m1_result, m2_result):
    print("\n" + "=" * 60)
    print("  TRAINING SUMMARY")
    print("=" * 60)
    for label, res, fname in [
        ("Model 1 — Eligibility",    m1_result, "eligibility_model.joblib"),
        ("Model 2 — Affordability",  m2_result, "affordability_model.joblib"),
    ]:
        status = res.get("status", "unknown")
        if status == "success":
            print(f"  {label}")
            print(f"    Status:   ✅ Trained successfully")
            print(f"    Accuracy: {res.get('accuracy', 0):.4f}")
            print(f"    F1 Score: {res.get('f1', 0):.4f}")
            print(f"    ROC-AUC:  {res.get('roc_auc', 0):.4f}")
            print(f"    Saved:    ml/models/{fname}")
        else:
            print(f"  {label}")
            print(f"    Status: ❌ FAILED — {res.get('error', 'unknown error')}")
    print("=" * 60)
    print("\n  COMMANDS TO RETRAIN:")
    print("    python ml/train_eligibility.py")
    print("    python ml/train_affordability.py")
    print("    python ml/train_all_models.py")
    print("\n  NOTICE:")
    print("    AI model outputs are estimates — not guaranteed lender decisions.")
    print("    Always verify eligibility directly with the lender.")
    print("=" * 60)

    # Save combined summary to JSON
    REPORTS_DIR.mkdir(exist_ok=True)
    summary = {
        "training_run_at": datetime.now().isoformat(),
        "model_1": m1_result,
        "model_2": m2_result,
        "datasets_used": {
            "model_1": "data/raw/eligibility_dataset.csv",
            "model_2": "data/raw/affordability_dataset.csv",
        },
        "note": "AI model outputs are estimates — not guaranteed lender approvals.",
    }
    with open(REPORTS_DIR / "training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary saved -> data/reports/training_summary.json")


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  LoanWise AI — ML Training Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    validate_files()
    validate_schemas()
    data_quality_check()

    m1 = train_model_1()
    m2 = train_model_2()

    print_summary(m1, m2)

    if m1.get("status") != "success" or m2.get("status") != "success":
        print("\n⚠️  One or more models failed. Check errors above.")
        sys.exit(1)
    print("\n✅ Both models trained successfully.\n")


if __name__ == "__main__":
    main()
