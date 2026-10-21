"""
services/notification_service.py
------------------------------------
Purpose:
    Implements requirements #14 (overdue detection) and #15 (reminders)
    as IN-APP notifications only (no paid SMS/email gateway - per spec).

    refresh_overdue_status() is called whenever payments are read (e.g.
    dashboard load, payment-history page) so that DUE/OVERDUE status is
    always computed fresh against "today", never stale.
"""

from datetime import datetime, date
from bson import ObjectId
from database.mongodb import collections


def _late_charge_for(active_loan: dict, product: dict | None, amount_due: float, days_overdue: int) -> float:
    """
    Reads the product's stored late_charge_rule and applies a simple,
    clearly-labelled ESTIMATE (never presented as guaranteed - spec #14).
    Default rule: 2% of the overdue EMI per month (or part-month) late.
    """
    if days_overdue <= 0:
        return 0.0
    months_late = max(1, -(-days_overdue // 30))  # ceil division
    rate = 0.02
    if product and "late_charge_rule" in product:
        # Very small parser: if the admin wrote e.g. "3% per month", use 3%.
        rule = product["late_charge_rule"]
        for token in rule.replace("%", " ").split():
            try:
                rate = float(token) / 100
                break
            except ValueError:
                continue
    return round(amount_due * rate * months_late, 2)


def refresh_overdue_status(active_loan_id: str | None = None) -> None:
    """
    Scans UPCOMING/DUE EMIs whose due_date has passed and are not PAID,
    marks them OVERDUE, and (re)computes days_overdue + estimated late
    charge. Safe to call repeatedly (idempotent).
    """
    query = {"payment_status": {"$in": ["UPCOMING", "DUE", "OVERDUE"]}}
    if active_loan_id:
        query["active_loan_id"] = ObjectId(active_loan_id)

    today = date.today()
    products_cache: dict = {}

    for payment in collections["payments"].find(query):
        due_date = datetime.strptime(payment["due_date"], "%Y-%m-%d").date()
        days_overdue = (today - due_date).days

        if days_overdue > 0:
            active_loan = collections["active_loans"].find_one({"_id": payment["active_loan_id"]})
            product = None
            if active_loan:
                pid = active_loan["product_id"]
                if pid not in products_cache:
                    products_cache[pid] = collections["loan_products"].find_one({"_id": pid})
                product = products_cache[pid]

            late_charge = _late_charge_for(active_loan, product, payment["amount_due"], days_overdue)
            collections["payments"].update_one(
                {"_id": payment["_id"]},
                {"$set": {"payment_status": "OVERDUE", "days_overdue": days_overdue, "late_charge": late_charge}},
            )
        elif days_overdue == 0 and payment["payment_status"] == "UPCOMING":
            collections["payments"].update_one({"_id": payment["_id"]}, {"$set": {"payment_status": "DUE"}})


def get_notifications_for_user(user_id: str) -> list[dict]:
    """
    Builds the dashboard's reminder feed (#15/#16): one entry per
    upcoming (next 7 days) or overdue EMI, across all of the user's
    active loans.
    """
    refresh_overdue_status()

    active_loan_ids = [
        loan["_id"] for loan in collections["active_loans"].find({"user_id": ObjectId(user_id)})
    ]
    if not active_loan_ids:
        return []

    notifications = []
    today = date.today()
    for payment in collections["payments"].find({
        "active_loan_id": {"$in": active_loan_ids},
        "payment_status": {"$in": ["DUE", "UPCOMING", "OVERDUE"]},
    }).sort("due_date", 1):
        due_date = datetime.strptime(payment["due_date"], "%Y-%m-%d").date()
        days_until = (due_date - today).days

        if payment["payment_status"] == "OVERDUE":
            notifications.append({
                "type": "overdue",
                "payment_id": str(payment["_id"]),
                "active_loan_id": str(payment["active_loan_id"]),
                "message": f"Payment overdue by {payment['days_overdue']} day(s).",
                "amount_due": payment["amount_due"],
                "estimated_late_charge": payment["late_charge"],
                "due_date": payment["due_date"],
            })
        elif days_until <= 7:
            notifications.append({
                "type": "upcoming",
                "payment_id": str(payment["_id"]),
                "active_loan_id": str(payment["active_loan_id"]),
                "message": f"Upcoming EMI of Rs.{payment['amount_due']} due on {payment['due_date']}.",
                "amount_due": payment["amount_due"],
                "due_date": payment["due_date"],
            })

    return notifications
