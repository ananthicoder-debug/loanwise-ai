"""
seed/seed_products.py
----------------------
Imports verified Indian loan products from backend/data/raw/loan_products.csv.
Every product references a real Indian lender from the lenders collection.
No demo/sample/fake products are inserted.

Run standalone: python seed/seed_products.py  (after seed_lenders.py)
"""

import sys
import os
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.mongodb import collections

BACKEND_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "loan_products.csv"
ROOT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "loan_products.csv"

DATA_PATH = BACKEND_DATA_PATH if BACKEND_DATA_PATH.exists() else ROOT_DATA_PATH


def _safe_float(val, default=0.0):
    try:
        return float(val) if str(val).strip() not in ("", "Not publicly specified") else default
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    try:
        return int(float(val)) if str(val).strip() not in ("", "Not publicly specified") else default
    except (ValueError, TypeError):
        return default


def build_products(lenders_by_code: dict) -> tuple[list, int]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"loan_products.csv not found. Expected at: {BACKEND_DATA_PATH}"
        )

    source_rows = pd.read_csv(DATA_PATH).fillna("").to_dict("records")
    products = []
    skipped = 0

    for row in source_rows:
        lender_code = str(row.get("Lender_ID", "")).strip()
        lender_oid = lenders_by_code.get(lender_code)

        if not lender_oid:
            print(f"  SKIP: No lender found for Lender_ID={lender_code} (Product: {row.get('Product_Name','')})")
            skipped += 1
            continue

        product_name = str(row.get("Product_Name", "")).strip()
        if not product_name:
            skipped += 1
            continue

        # Parse documents_required
        docs_raw = str(row.get("Documents_Required", "Identity, Address, Income proof")).strip()
        documents = [d.strip() for d in docs_raw.split(",") if d.strip()] if docs_raw else []

        # Benefits and eligibility as lists
        benefits_raw = str(row.get("Product_Benefits", "")).strip()
        benefits = [benefits_raw] if benefits_raw and benefits_raw != "Not publicly specified" else []

        elig_raw = str(row.get("Primary_Eligibility_Conditions", "")).strip()
        elig_conds = [elig_raw] if elig_raw and elig_raw != "Not publicly specified" else []

        min_cibil_raw = str(row.get("Minimum_CIBIL_If_Publicly_Stated", "")).strip()
        min_cibil = _safe_int(min_cibil_raw) if min_cibil_raw not in ("", "Not publicly specified") else 0

        products.append({
            "product_code": str(row.get("Product_ID", "")).strip(),
            "lender_id": lender_oid,
            "product_name": product_name,
            "lender_name_cached": str(row.get("Lender_Name", "")).strip(),
            "loan_category": str(row.get("Loan_Category", "Personal Loan")).strip(),
            "min_amount": _safe_float(row.get("Minimum_Loan_Amount"), 10000),
            "max_amount": _safe_float(row.get("Maximum_Loan_Amount"), 1000000),
            "interest_rate_min": _safe_float(row.get("Interest_Rate_Min"), 10.0),
            "interest_rate_max": _safe_float(row.get("Interest_Rate_Max"), 20.0),
            "min_tenure": _safe_int(row.get("Minimum_Tenure_Months"), 12),
            "max_tenure": _safe_int(row.get("Maximum_Tenure_Months"), 60),
            "processing_fee": str(row.get("Processing_Fee", "Not publicly specified")).strip() or "Not publicly specified",
            "minimum_income": _safe_float(row.get("Minimum_Income"), 0),
            "minimum_cibil": min_cibil,
            "minimum_age": _safe_int(row.get("Minimum_Age"), 18),
            "maximum_age": _safe_int(row.get("Maximum_Age"), 70),
            "employment_required": str(row.get("Employment_Type_Requirement", "Not publicly specified")).strip(),
            "collateral_required": str(row.get("Collateral_Required", "No")).strip(),
            "coapplicant_allowed": str(row.get("Coapplicant_Allowed", "Depends")).strip(),
            "benefits": benefits,
            "eligibility_conditions": elig_conds,
            "documents_required": documents,
            "purpose": str(row.get("Purpose", "")).strip(),
            "official_product_url": str(row.get("Official_Product_URL", "")).strip(),
            "source_date": str(row.get("Source_Date", "")).strip(),
            "verification_status": str(row.get("Verification_Status", "Verified")).strip(),
            "dataset_type": str(row.get("Dataset_Type", "Verified_Product_Catalogue")).strip(),
            "is_active": str(row.get("Product_Status", "Active")).strip() == "Active",
            "is_demo": False,
            "late_charge_rule": "Not publicly specified",
        })

    return products, skipped


def seed_products():
    lenders_by_code = {l["lender_code"]: l["_id"] for l in collections["lenders"].find()}
    if not lenders_by_code:
        raise RuntimeError("No lenders found. Run seed_lenders.py first.")

    products, skipped = build_products(lenders_by_code)
    collections["loan_products"].delete_many({})

    if not products:
        print("No products to insert.")
        return

    result = collections["loan_products"].insert_many(products)
    print(f"Loan Products: {len(products) + skipped} read | {len(result.inserted_ids)} inserted | {skipped} skipped")
    return products


if __name__ == "__main__":
    seed_products()
