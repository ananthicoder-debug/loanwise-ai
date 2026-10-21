"""
seed/import_payments.py
-------------------------
Imports synthetic installment payment records into installment_payments collection.
Dataset: backend/data/raw/installment_payments.csv (~30,000-60,000 rows)

Run: python seed/import_payments.py
Note: Large file  -  may take a minute.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.mongodb import collections

BACKEND_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "installment_payments.csv"
ROOT_PATH = Path(__file__).resolve().parents[2] / "data" / "installment_payments.csv"
DATA_PATH = BACKEND_PATH if BACKEND_PATH.exists() else ROOT_PATH

BATCH_SIZE = 5000  # insert in batches to avoid memory issues


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


def import_payments():
    if not DATA_PATH.exists():
        print(f"ERROR: installment_payments.csv not found at {DATA_PATH}")
        return

    print(f"Reading {DATA_PATH} ...")
    df = pd.read_csv(DATA_PATH).fillna("")
    rows = df.to_dict("records")
    total_rows = len(rows)
    print(f"  Read: {total_rows} rows")

    records = []
    skipped = 0

    for i, row in enumerate(rows):
        try:
            records.append({
                "payment_id": str(row.get("Payment_ID", f"PAY{i:07d}")).strip(),
                "historical_loan_id": str(row.get("Historical_Loan_ID", "")).strip(),
                "applicant_id": str(row.get("Applicant_ID", "")).strip(),
                "product_id_ref": str(row.get("Product_ID", "")).strip(),
                "installment_number": _safe_int(row.get("Installment_Number")),
                "due_date": str(row.get("Due_Date", "")).strip(),
                "due_amount": _safe_float(row.get("Due_Amount")),
                "principal_component": _safe_float(row.get("Principal_Component")),
                "interest_component": _safe_float(row.get("Interest_Component")),
                "paid_date": str(row.get("Paid_Date", "")).strip() or None,
                "amount_paid": _safe_float(row.get("Amount_Paid")),
                "payment_status": str(row.get("Payment_Status", "Paid")).strip(),
                "days_late": _safe_int(row.get("Days_Late")),
                "late_charge": _safe_float(row.get("Late_Charge")),
                "dataset_type": "Synthetic_Historical_Data",
                "imported_at": datetime.now(timezone.utc),
            })
        except Exception:
            skipped += 1

    if not records:
        print("No records to insert.")
        return

    collections["installment_payments"].delete_many({})

    inserted = 0
    for batch_start in range(0, len(records), BATCH_SIZE):
        batch = records[batch_start:batch_start + BATCH_SIZE]
        result = collections["installment_payments"].insert_many(batch)
        inserted += len(result.inserted_ids)
        print(f"  Inserted batch: {batch_start + len(batch)}/{total_rows}", end="\r")

    print(f"\nInstallment Payments: {total_rows} read | {inserted} inserted | {skipped} skipped")


if __name__ == "__main__":
    import_payments()
