"""
routes/datasets.py
--------------------
Admin-only endpoints for dataset/catalogue management and data quality checks.
GET  /api/admin/datasets         -> dataset stats + catalogue status
GET  /api/admin/data-quality     -> validation summary
GET  /api/admin/lender-stats     -> products-per-lender aggregation
GET  /api/admin/category-stats   -> products-per-category aggregation
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from database.mongodb import collections, db
from utils.deps import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin-datasets"])


@router.get("/datasets")
def get_dataset_status(admin: dict = Depends(get_current_admin)):
    """Return live record counts for every major collection."""
    meta = collections["system_metadata"].find_one({"key": "dataset_version"}) or {}

    return {
        "dataset_version": meta.get("dataset_version", "2.0"),
        "product_catalogue_version": meta.get("product_catalogue_version", "2026.09"),
        "borrower_dataset_version": meta.get("borrower_dataset_version", "india_v2"),
        "historical_dataset_version": meta.get("historical_dataset_version", "repayment_v2"),
        "updated_at": meta.get("updated_at", "2026-09-23"),
        "counts": {
            "lenders": collections["lenders"].count_documents({}),
            "loan_products": collections["loan_products"].count_documents({"is_active": True}),
            "total_products": collections["loan_products"].count_documents({}),
            "users": collections["users"].count_documents({"role": "user"}),
            "loan_applications": collections["loan_applications"].count_documents({}),
            "predictions": collections["predictions"].count_documents({}),
            "recommendations": collections["recommendations"].count_documents({}),
            "active_loans": collections["active_loans"].count_documents({"status": "active"}),
            "payments": collections["payments"].count_documents({}),
            "historical_loans": collections["historical_loans"].count_documents({}),
            "installment_payments": collections["installment_payments"].count_documents({}),
            "notifications": collections["notifications"].count_documents({}),
            "documents": collections["documents"].count_documents({}),
            "feedback": collections["feedback"].count_documents({}),
        },
        "catalogue_status": {
            "real_lenders_loaded": collections["lenders"].count_documents({}) > 0,
            "real_products_loaded": collections["loan_products"].count_documents({"is_active": True}) > 0,
            "historical_data_loaded": collections["historical_loans"].count_documents({}) > 0,
        }
    }


@router.get("/data-quality")
def data_quality_check(admin: dict = Depends(get_current_admin)):
    """Run validation checks on the loan product catalogue."""
    errors = []
    warnings = []

    # Check for products missing key fields
    missing_name = collections["loan_products"].count_documents(
        {"product_name": {"$in": [None, ""]}}
    )
    if missing_name > 0:
        errors.append(f"{missing_name} product(s) have no product_name.")

    missing_lender = collections["loan_products"].count_documents(
        {"lender_id": None}
    )
    if missing_lender > 0:
        errors.append(f"{missing_lender} product(s) have no lender_id.")

    # Check for invalid interest rates
    invalid_rate = collections["loan_products"].count_documents(
        {"$or": [{"interest_rate_min": {"$lte": 0}}, {"interest_rate_max": {"$lte": 0}}]}
    )
    if invalid_rate > 0:
        warnings.append(f"{invalid_rate} product(s) have zero or negative interest rates.")

    # Check for invalid amounts
    invalid_amount = collections["loan_products"].count_documents(
        {"$or": [{"min_amount": {"$lte": 0}}, {"max_amount": {"$lte": 0}}]}
    )
    if invalid_amount > 0:
        warnings.append(f"{invalid_amount} product(s) have zero or negative loan amounts.")

    # Count unverified lenders
    unverified_lenders = collections["lenders"].count_documents(
        {"verification_status": {"$ne": "Verified"}}
    )
    if unverified_lenders > 0:
        warnings.append(f"{unverified_lenders} lender(s) do not have Verified status.")

    # Orphan products (lender_id references missing lender)
    lender_ids = [l["_id"] for l in collections["lenders"].find({}, {"_id": 1})]
    orphan_products = collections["loan_products"].count_documents(
        {"lender_id": {"$nin": lender_ids}}
    )
    if orphan_products > 0:
        errors.append(f"{orphan_products} product(s) reference non-existent lenders.")

    return {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_products": collections["loan_products"].count_documents({}),
        "active_products": collections["loan_products"].count_documents({"is_active": True}),
        "total_lenders": collections["lenders"].count_documents({}),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL",
    }


@router.get("/lender-stats")
def lender_stats(admin: dict = Depends(get_current_admin)):
    """Products per lender (aggregation)."""
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$lender_id", "product_count": {"$sum": 1}}},
        {"$lookup": {
            "from": "lenders",
            "localField": "_id",
            "foreignField": "_id",
            "as": "lender"
        }},
        {"$unwind": "$lender"},
        {"$project": {
            "_id": {"$toString": "$_id"},
            "lender_name": "$lender.lender_name",
            "product_count": 1
        }},
        {"$sort": {"product_count": -1}}
    ]
    result = list(collections["loan_products"].aggregate(pipeline))
    return result


@router.get("/model-performance")
def model_performance(admin: dict = Depends(get_current_admin)):
    """Return saved ML model performance metrics."""
    import sys, os
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ml"))
    try:
        from model_utils import get_all_model_metadata
        records = get_all_model_metadata()
    except Exception as e:
        records = []
    return records


@router.get("/category-stats")
def category_stats(admin: dict = Depends(get_current_admin)):
    """Products per category (aggregation)."""
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$loan_category", "product_count": {"$sum": 1}, "lender_count": {"$addToSet": "$lender_id"}}},
        {"$project": {
            "category": "$_id",
            "product_count": 1,
            "lender_count": {"$size": "$lender_count"},
            "_id": 0
        }},
        {"$sort": {"product_count": -1}}
    ]
    return list(collections["loan_products"].aggregate(pipeline))
