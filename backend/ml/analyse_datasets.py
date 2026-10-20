"""
ml/analyse_datasets.py
-----------------------
Generates dataset analysis reports from all 7 CSV files.
Saves results to:
  data/reports/dataset_analysis.json
  data/reports/data_quality_report.json
  MongoDB system_metadata collection
"""
import sys, os, json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np

RAW      = Path(__file__).parent.parent / "data" / "raw"
REPORTS  = Path(__file__).parent.parent / "data" / "reports"
REPORTS.mkdir(exist_ok=True)


class _NumpyEncoder(json.JSONEncoder):
    """Makes numpy int64/float64 JSON-serializable."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):  return int(obj)
        if isinstance(obj, (np.floating,)): return float(obj)
        if isinstance(obj, np.ndarray):     return obj.tolist()
        return super().default(obj)

def _clean(obj):
    """Recursively convert numpy types to Python native types."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.integer,)):  return int(obj)
    if isinstance(obj, (np.floating,)): return float(obj)
    if isinstance(obj, np.ndarray):     return obj.tolist()
    return obj

def _stats(series):
    s = series.dropna()
    if len(s) == 0:
        return {}
    return {
        "min":    round(float(s.min()), 2),
        "max":    round(float(s.max()), 2),
        "mean":   round(float(s.mean()), 2),
        "median": round(float(s.median()), 2),
        "std":    round(float(s.std()), 2),
    }


def analyse_eligibility():
    df = pd.read_csv(RAW / "eligibility_dataset.csv")
    return {
        "file": "eligibility_dataset.csv",
        "total_records": len(df),
        "columns": list(df.columns),
        "target": "loan_status",
        "class_distribution": df["loan_status"].value_counts().to_dict(),
        "class_balance_pct": {
            "eligible":     round(float(df["loan_status"].mean())*100, 1),
            "not_eligible": round((1-float(df["loan_status"].mean()))*100, 1),
        },
        "income_stats":    _stats(df["annual_income"]),
        "cibil_stats":     _stats(df["cibil_score"]),
        "loan_amount_stats":_stats(df["loan_amount"]),
        "loan_tenure_stats":_stats(df["loan_tenure"]),
        "age_stats":       _stats(df["age"]),
        "education_dist":  df["education"].value_counts().to_dict(),
        "employment_dist": df["employment_type"].value_counts().to_dict(),
        "missing_values":  int(df.isnull().sum().sum()),
        "duplicate_rows":  int(df.duplicated().sum()),
        "dataset_type":    "Synthetic Training Data — NOT real borrower data",
    }


def analyse_affordability():
    df = pd.read_csv(RAW / "affordability_dataset.csv")
    return {
        "file": "affordability_dataset.csv",
        "total_records": len(df),
        "columns": list(df.columns),
        "target": "manageable",
        "class_distribution": df["manageable"].value_counts().to_dict(),
        "class_balance_pct": {
            "manageable":     round(float(df["manageable"].mean())*100, 1),
            "not_manageable": round((1-float(df["manageable"].mean()))*100, 1),
        },
        "class_imbalance_warning": "Dataset is imbalanced — 22.5% Manageable vs 77.5% Not Manageable. Class weights applied during training.",
        "income_stats":        _stats(df["monthly_income"]),
        "current_emi_stats":   _stats(df["current_emi"]),
        "outstanding_debt_stats":_stats(df["outstanding_debt"]),
        "proposed_emi_stats":  _stats(df["proposed_emi"]),
        "emi_income_ratio_stats":_stats(df["emi_income_ratio"]),
        "proposed_amount_stats":_stats(df["proposed_amount"]),
        "missed_payments_dist": df["missed_payments"].value_counts().to_dict(),
        "late_payments_dist":  df["late_payments"].value_counts().to_dict(),
        "missing_values":  int(df.isnull().sum().sum()),
        "duplicate_rows":  int(df.duplicated().sum()),
        "dataset_type":    "Synthetic Training Data — NOT real borrower data",
    }


def analyse_borrowers():
    df = pd.read_csv(RAW / "borrowers.csv")
    return {
        "file": "borrowers.csv",
        "total_records": len(df),
        "columns": list(df.columns),
        "eligibility_dist": df["Eligibility_Target"].value_counts().to_dict(),
        "affordability_dist": df["Affordability_Target"].value_counts().to_dict(),
        "income_stats":   _stats(df["Monthly_Income"]),
        "cibil_stats":    _stats(df["CIBIL_Score"]),
        "age_stats":      _stats(df["Age"]),
        "loan_amount_stats": _stats(df["Requested_Loan_Amount"]),
        "employment_dist":df["Employment_Type"].value_counts().to_dict(),
        "state_dist":     dict(df["State"].value_counts().head(10)),
        "loan_category_dist": df["Requested_Loan_Category"].value_counts().to_dict(),
        "missing_values": int(df.isnull().sum().sum()),
        "missing_by_col": {col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().sum() > 0},
        "duplicate_rows": int(df.duplicated().sum()),
        "dataset_type":   "Synthetic Borrower Data — NOT real customer data",
    }


def analyse_historical_loans():
    df = pd.read_csv(RAW / "historical_loans.csv")
    active = (df["Loan_Status"] == "Active").sum()
    closed = (df["Loan_Status"] == "Closed").sum()
    return {
        "file": "historical_loans.csv",
        "total_records": len(df),
        "loan_status_dist": df["Loan_Status"].value_counts().to_dict(),
        "repayment_status_dist": df["Repayment_Status"].value_counts().to_dict(),
        "active_loans":  int(active),
        "closed_loans":  int(closed),
        "loan_amount_stats": _stats(df["Loan_Amount"]),
        "emi_stats":     _stats(df["EMI_Amount"]),
        "interest_rate_stats": _stats(df["Interest_Rate"]),
        "tenure_stats":  _stats(df["Tenure_Months"]),
        "missed_installments_stats": _stats(df["Missed_Installments"]),
        "late_installments_stats": _stats(df["Late_Installments"]),
        "avg_days_late_stats": _stats(df["Average_Days_Late"]),
        "outstanding_amount_stats": _stats(df["Outstanding_Amount"]),
        "lender_dist":   dict(df["Lender_Name"].value_counts()),
        "loan_category_dist": df["Loan_Category"].value_counts().to_dict(),
        "early_closure_count": int((df["Early_Closure"] == "Yes").sum()),
        "missing_values":int(df.isnull().sum().sum()),
        "dataset_type":  "Synthetic Historical Loan Data — NOT real loan records",
    }


def analyse_installment_payments():
    # Only read a sample for speed
    df = pd.read_csv(RAW / "installment_payments.csv")
    return {
        "file": "installment_payments.csv",
        "total_records": len(df),
        "payment_status_dist": df["Payment_Status"].value_counts().to_dict(),
        "paid_count":   int((df["Payment_Status"] == "Paid").sum()),
        "late_count":   int((df["Payment_Status"] == "Late").sum()),
        "missed_count": int((df["Payment_Status"] == "Missed").sum()),
        "pending_count":int((df["Payment_Status"] == "Pending").sum()),
        "due_amount_stats":  _stats(df["Due_Amount"]),
        "amount_paid_stats": _stats(df["Amount_Paid"]),
        "days_late_stats":   _stats(df["Days_Late"].dropna()),
        "late_charge_stats": _stats(df["Late_Charge"]),
        "missing_values":    int(df.isnull().sum().sum()),
        "missing_paid_date": int(df["Paid_Date"].isna().sum()),
        "missing_note":      "Paid_Date and Days_Late are null for Pending/Missed rows — expected behaviour",
        "dataset_type":      "Synthetic Payment History — NOT real payment data",
    }


def analyse_lenders():
    df = pd.read_csv(RAW / "lenders.csv")
    return {
        "file": "lenders.csv",
        "total_records": len(df),
        "lender_names": list(df["Lender_Name"]),
        "lender_types": df["Lender_Type"].value_counts().to_dict(),
        "verification_status": df["Verification_Status"].value_counts().to_dict(),
        "all_verified": bool((df["Verification_Status"] == "Verified").all()),
        "dataset_type": "Verified Product Catalogue — Real Indian lenders",
    }


def analyse_loan_products():
    df = pd.read_csv(RAW / "loan_products.csv")
    return {
        "file": "loan_products.csv",
        "total_records": len(df),
        "category_dist": df["Loan_Category"].value_counts().to_dict(),
        "lender_dist":   df["Lender_Name"].value_counts().to_dict(),
        "interest_rate_stats": _stats(df["Interest_Rate_Min"]),
        "loan_amount_stats": _stats(df["Maximum_Loan_Amount"]),
        "all_active":    bool((df["Product_Status"] == "Active").all()),
        "not_publicly_specified_fields": [
            col for col in df.columns
            if df[col].dtype == object and
            df[col].value_counts().index[0] == "Not publicly specified"
        ],
        "dataset_type": "Verified Product Catalogue — Real Indian loan products",
    }


def run():
    print("Generating dataset analysis reports...")

    report = {
        "generated_at": datetime.now().isoformat(),
        "datasets": {
            "eligibility_dataset":    analyse_eligibility(),
            "affordability_dataset":  analyse_affordability(),
            "borrowers":              analyse_borrowers(),
            "historical_loans":       analyse_historical_loans(),
            "installment_payments":   analyse_installment_payments(),
            "lenders":                analyse_lenders(),
            "loan_products":          analyse_loan_products(),
        }
    }

    # Data quality report
    quality = {
        "generated_at": datetime.now().isoformat(),
        "checks": []
    }
    for name, data in report["datasets"].items():
        mv = data.get("missing_values", 0)
        dr = data.get("duplicate_rows", 0)
        status = "PASS" if mv == 0 and dr == 0 else "WARN"
        quality["checks"].append({
            "dataset": name,
            "total_records": data.get("total_records", 0),
            "missing_values": mv,
            "duplicate_rows": dr,
            "status": status,
            "notes": data.get("class_imbalance_warning", "") or data.get("missing_note", ""),
        })

    with open(REPORTS / "dataset_analysis.json", "w") as f:
        json.dump(_clean(report), f, indent=2, cls=_NumpyEncoder)
    with open(REPORTS / "data_quality_report.json", "w") as f:
        json.dump(_clean(quality), f, indent=2, cls=_NumpyEncoder)

    print(f"Saved: {REPORTS / 'dataset_analysis.json'}")
    print(f"Saved: {REPORTS / 'data_quality_report.json'}")

    # Save to MongoDB
    try:
        from database.mongodb import collections
        collections["system_metadata"].replace_one(
            {"key": "full_dataset_analysis"},
            {"key": "full_dataset_analysis", **_clean(report)}, upsert=True
        )
        collections["system_metadata"].replace_one(
            {"key": "data_quality_report"},
            {"key": "data_quality_report", **_clean(quality)}, upsert=True
        )
        print("Saved to MongoDB system_metadata.")
    except Exception as e:
        print(f"Warning: {e}")

    # Print summary
    print("\n=== DATASET SUMMARY ===")
    for name, data in report["datasets"].items():
        print(f"  {name:<30} {data.get('total_records',0):>8} records")

    return report


if __name__ == "__main__":
    run()
