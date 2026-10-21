"""
seed/seed_lenders.py
---------------------
Imports the verified Indian lender catalogue from backend/data/raw/lenders.csv.
These are real Indian banks/NBFCs  -  no demo/sample/fake entries.

Run standalone: python seed/seed_lenders.py
"""

import sys
import os
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.mongodb import collections

# Try both locations (backend/data/raw/ first, then root data/raw/)
BACKEND_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "lenders.csv"
ROOT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "lenders.csv"

DATA_PATH = BACKEND_DATA_PATH if BACKEND_DATA_PATH.exists() else ROOT_DATA_PATH


def seed_lenders():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"lenders.csv not found. Expected at: {BACKEND_DATA_PATH}\n"
            "Copy the file from the project data/ folder to backend/data/raw/"
        )

    source_rows = pd.read_csv(DATA_PATH).fillna("").to_dict("records")
    lenders = []
    skipped = 0
    for row in source_rows:
        lender_name = str(row.get("Lender_Name", "")).strip()
        if not lender_name:
            skipped += 1
            continue
        lenders.append({
            "lender_code": str(row.get("Lender_ID", "")).strip(),
            "lender_name": lender_name,
            "lender_type": str(row.get("Lender_Type", "Bank")).strip(),
            "headquarters_city": str(row.get("Headquarters_City", "")).strip(),
            "state": str(row.get("State", "")).strip(),
            "official_website": str(row.get("Official_Website", "")).strip(),
            "verification_status": str(row.get("Verification_Status", "Verified")).strip(),
            "dataset_type": str(row.get("Dataset_Type", "Verified_Product_Catalogue")).strip(),
            "status": "active",
        })

    collections["lenders"].delete_many({})
    if not lenders:
        print("No lender records to insert.")
        return {}

    result = collections["lenders"].insert_many(lenders)
    print(f"Lenders: {len(source_rows)} read | {len(result.inserted_ids)} inserted | {skipped} skipped")

    return {
        lender["lender_code"]: _id
        for lender, _id in zip(lenders, result.inserted_ids)
    }


if __name__ == "__main__":
    seed_lenders()
