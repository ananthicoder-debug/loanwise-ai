"""
routes/payments.py
--------------------
Endpoints:
    GET  /api/active-loans/{id}/payments        -> full EMI schedule (spec #12)
    POST /api/payments/{payment_id}/mark-paid   -> mark one EMI PAID (spec #13)

Ownership check: mark-paid looks up the payment's parent active_loan and
confirms it belongs to the calling user before allowing the update -
otherwise any logged-in user could mark ANY EMI as paid by guessing IDs.
"""

from datetime import datetime, timezone, date
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from database.mongodb import collections
from models.payment import MarkPaidRequest
from utils.deps import get_current_user
from services.notification_service import refresh_overdue_status

router = APIRouter(tags=["payments"])


@router.get("/api/active-loans/{active_loan_id}/payments")
def get_payment_schedule(active_loan_id: str, user: dict = Depends(get_current_user)):
    try:
        loan = collections["active_loans"].find_one({"_id": ObjectId(active_loan_id), "user_id": user["_id"]})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Active loan not found.")
    if not loan:
        raise HTTPException(status_code=404, detail="Active loan not found.")

    refresh_overdue_status(active_loan_id)  # make sure OVERDUE/DUE statuses are current

    payments = list(
        collections["payments"].find({"active_loan_id": ObjectId(active_loan_id)}).sort("emi_number", 1)
    )
    for p in payments:
        p["_id"] = str(p["_id"])
        p["active_loan_id"] = str(p["active_loan_id"])
    return payments


@router.post("/api/payments/{payment_id}/mark-paid")
def mark_paid(payment_id: str, payload: MarkPaidRequest, user: dict = Depends(get_current_user)):
    try:
        payment = collections["payments"].find_one({"_id": ObjectId(payment_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Payment not found.")
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found.")

    loan = collections["active_loans"].find_one({"_id": payment["active_loan_id"], "user_id": user["_id"]})
    if not loan:
        raise HTTPException(status_code=403, detail="This EMI does not belong to your account.")

    if payment["payment_status"] == "PAID":
        raise HTTPException(status_code=400, detail="This EMI is already marked as paid.")

    amount_paid = payload.amount_paid if payload.amount_paid is not None else payment["amount_due"]

    collections["payments"].update_one(
        {"_id": payment["_id"]},
        {"$set": {
            "payment_status": "PAID",
            "amount_paid": amount_paid,
            "payment_date": date.today().strftime("%Y-%m-%d"),
        }},
    )

    # If every EMI for this loan is now PAID, close the loan out.
    remaining = collections["payments"].count_documents({
        "active_loan_id": payment["active_loan_id"], "payment_status": {"$ne": "PAID"}
    })
    if remaining == 0:
        collections["active_loans"].update_one({"_id": payment["active_loan_id"]}, {"$set": {"status": "closed"}})

    updated = collections["payments"].find_one({"_id": payment["_id"]})
    updated["_id"] = str(updated["_id"])
    updated["active_loan_id"] = str(updated["active_loan_id"])
    return updated
