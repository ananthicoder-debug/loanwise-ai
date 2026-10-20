"""
seed/import_historical_loans.py
---------------------------------
Imports synthetic historical loan records into the historical_loans collection.
Dataset: backend/data/raw/historical_loans.csv (~10,000 rows)

Run: python seed/import_historical_loans.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.mongodb import collections

BACKEND_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "historical_loans.csv"
ROOT_PATH = Path(__file__).resolve().parents[2] / "data" / "historical_loans.csv"
DATA_PATH = BACKEND_PATH if BACKEND_PATH.exists() else ROOT_PATH


def _safe_float(val, default=0.0):
    try:
        return float(val) if str(val).strip() not in ("", "nan") else default
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    try:
        return int(float(val)) if str(val).strip() not in ("", "nan") else default
    except (ValueError, TypeError):
        return default


def import_historical_loans():
    if not DATA_PATH.exists():
        print(f"ERROR: historical_loans.csv not found at {DATA_PATH}")
        return

    print(f"Reading {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH).fillna("")
    rows = df.to_dict("records")
    print(f"  Read: {len(rows)} rows")

    records = []
    skipped = 0
    errors = []

    for i, row in enumerate(rows):
        try:
            records.append({
                "historical_loan_id": str(row.get("Historical_Loan_ID", f"HL{i:06d}")).strip(),
                "applicant_id": str(row.get("Applicant_ID", "")).strip(),
                "product_id_ref": str(row.get("Product_ID", "")).strip(),
                "lender_id_ref": str(row.get("Lender_ID", "")).strip(),
                "loan_category": str(row.get("Loan_Category", "")).strip(),
                "loan_amount": _safe_float(row.get("Loan_Amount")),
                "interest_rate": _safe_float(row.get("Interest_Rate")),
                "tenure_months": _safe_int(row.get("Tenure_Months")),
                "emi_amount": _safe_float(row.get("EMI_Amount")),
                "start_date": str(row.get("Start_Date", "")).strip(),
                "loan_status": str(row.get("Loan_Status", "Closed")).strip(),
                "outstanding_amount": _safe_float(row.get("Outstanding_Amount")),
                "total_installments": _safe_int(row.get("Total_Installments")),
                "paid_installments": _safe_int(row.get("Paid_Installments")),
                "missed_installments": _safe_int(row.get("Missed_Installments")),
                "late_installments": _safe_int(row.get("Late_Installments")),
                "average_days_late": _safe_float(row.get("Average_Days_Late")),
                "total_late_charges": _safe_float(row.get("Total_Late_Charges")),
                "repayment_status": str(row.get("Repayment_Status", "Closed")).strip(),
                "dataset_type": "Synthetic_Historical_Data",
                "imported_at": datetime.now(timezone.utc),
            })
        except Exception as e:
            errors.append(f"Row {i}: {e}")
            skipped += 1

    if not records:
        print("No records to insert.")
        return

    collections["historical_loans"].delete_many({})
    result = collections["historical_loans"].insert_many(records)
    print(f"Historical Loans: {len(rows)} read | {len(result.inserted_ids)} inserted | {skipped} skipped")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors[:5]:
            print(f"    {err}")


if __name__ == "__main__":
    import_historical_loans()
