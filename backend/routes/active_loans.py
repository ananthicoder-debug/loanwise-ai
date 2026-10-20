"""
routes/active_loans.py
------------------------
POST /api/active-loans          -> create active loan + full EMI schedule
GET  /api/active-loans          -> list user's active/closed loans
GET  /api/active-loans/{id}     -> single active loan with product info
"""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from database.mongodb import collections
from models.payment import ActiveLoanCreateRequest
from utils.deps import get_current_user
from services.emi_service import generate_amortization_schedule

router = APIRouter(prefix="/api/active-loans", tags=["active-loans"])


def _safe_str(v):
    """Convert ObjectId or datetime to string safely."""
    if v is None:
        return None
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    return v


def _enrich_loan(loan: dict) -> dict:
    """Return a fully JSON-serializable loan dict with product/lender info."""
    product, lender = None, None
    try:
        if loan.get("product_id"):
            product = collections["loan_products"].find_one({"_id": loan["product_id"]})
        if product and product.get("lender_id"):
            lender = collections["lenders"].find_one({"_id": product["lender_id"]})
    except Exception:
        pass

    return {
        "_id":              _safe_str(loan.get("_id")),
        "user_id":          _safe_str(loan.get("user_id")),
        "product_id":       _safe_str(loan.get("product_id")),
        "recommendation_id":_safe_str(loan.get("recommendation_id")),
        "application_id":   _safe_str(loan.get("application_id")),
        "actual_amount":    loan.get("actual_amount", 0),
        "interest_rate":    loan.get("interest_rate", 0),
        "tenure_months":    loan.get("tenure_months", 0),
        "emi_amount":       loan.get("emi_amount", 0),
        "start_date":       loan.get("start_date", ""),
        "first_due_date":   loan.get("first_due_date", ""),
        "status":           loan.get("status", ""),
        "product_name":     product["product_name"] if product else "Unknown Product",
        "lender_name":      lender["lender_name"] if lender else "Unknown Lender",
        "loan_category":    product["loan_category"] if product else "",
        "lender_website":   lender.get("official_website", "") if lender else "",
        "created_at":       _safe_str(loan.get("created_at")),
    }


@router.post("")
def create_active_loan(payload: ActiveLoanCreateRequest, user: dict = Depends(get_current_user)):
    try:
        product = collections["loan_products"].find_one({"_id": ObjectId(payload.product_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Loan product not found.")
    if not product:
        raise HTTPException(status_code=404, detail="Loan product not found.")

    if payload.actual_amount < product["min_amount"] or payload.actual_amount > product["max_amount"]:
        raise HTTPException(status_code=400, detail="Loan amount is outside this product's allowed range.")
    if payload.tenure_months < product["min_tenure"] or payload.tenure_months > product["max_tenure"]:
        raise HTTPException(status_code=400, detail="Tenure is outside this product's allowed range.")

    try:
        start_dt = datetime.strptime(payload.start_date, "%Y-%m-%d")
        first_due = datetime.strptime(payload.first_due_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be YYYY-MM-DD format.")

    schedule = generate_amortization_schedule(
        payload.actual_amount, payload.interest_rate, payload.tenure_months,
        start_dt, first_due,
    )

    active_loan_doc = {
        "user_id":          user["_id"],
        "product_id":       ObjectId(payload.product_id),
        "recommendation_id":ObjectId(payload.recommendation_id) if payload.recommendation_id else None,
        "application_id":   ObjectId(payload.application_id) if payload.application_id else None,
        "actual_amount":    payload.actual_amount,
        "interest_rate":    payload.interest_rate,
        "tenure_months":    payload.tenure_months,
        "emi_amount":       schedule[0]["amount_due"],
        "start_date":       payload.start_date,
        "first_due_date":   payload.first_due_date,
        "status":           "active",
        "created_at":       datetime.now(timezone.utc),
    }
    result = collections["active_loans"].insert_one(active_loan_doc)
    loan_oid = result.inserted_id

    for emi in schedule:
        emi["active_loan_id"] = loan_oid
    collections["payments"].insert_many(schedule)

    return {
        "_id":          str(loan_oid),
        "user_id":      str(user["_id"]),
        "product_id":   payload.product_id,
        "actual_amount":payload.actual_amount,
        "interest_rate":payload.interest_rate,
        "tenure_months":payload.tenure_months,
        "emi_amount":   schedule[0]["amount_due"],
        "start_date":   payload.start_date,
        "first_due_date":payload.first_due_date,
        "status":       "active",
    }


@router.get("")
def list_active_loans(user: dict = Depends(get_current_user)):
    loans = list(collections["active_loans"].find(
        {"user_id": user["_id"]}
    ).sort("created_at", -1))
    return [_enrich_loan(l) for l in loans]


@router.get("/{active_loan_id}")
def get_active_loan(active_loan_id: str, user: dict = Depends(get_current_user)):
    try:
        loan = collections["active_loans"].find_one({
            "_id": ObjectId(active_loan_id),
            "user_id": user["_id"],
        })
    except InvalidId:
        raise HTTPException(status_code=404, detail="Active loan not found.")
    if not loan:
        raise HTTPException(status_code=404, detail="Active loan not found.")
    return _enrich_loan(loan)
