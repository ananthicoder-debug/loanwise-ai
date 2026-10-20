"""
routes/dashboard.py
---------------------
Endpoint:
    GET /api/dashboard -> everything the user dashboard needs in one call
                           (cards, category chart data, notifications,
                           recent activity) - requirement #16.
"""

from bson import ObjectId
from fastapi import APIRouter, Depends

from database.mongodb import collections
from utils.deps import get_current_user
from services.notification_service import get_notifications_for_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(user: dict = Depends(get_current_user)):
    user_id = user["_id"]

    applications = list(collections["loan_applications"].find({"user_id": user_id}))
    application_ids = [a["_id"] for a in applications]

    latest_prediction = None
    if application_ids:
        latest_prediction = collections["predictions"].find_one(
            {"application_id": {"$in": application_ids}}, sort=[("created_at", -1)]
        )

    eligible_count = 0
    if latest_prediction:
        # Use the count persisted by the evaluation pipeline. Counting all
        # catalogue products would incorrectly include products that failed
        # the model/product-criteria match.
        eligible_count = latest_prediction.get("eligible_count", 0)

    recommended_count = collections["recommendations"].count_documents({"application_id": {"$in": application_ids}})
    active_loans = list(collections["active_loans"].find({"user_id": user_id}))
    active_count = sum(1 for l in active_loans if l["status"] == "active")

    notifications = get_notifications_for_user(str(user_id))
    next_emi = min(
        (n for n in notifications if n["type"] in ("upcoming", "overdue")),
        key=lambda n: n["due_date"], default=None,
    )

    # Category breakdown chart: how many active products exist per category (catalogue-wide)
    category_counts = {}
    for p in collections["loan_products"].find({"is_active": True}):
        category_counts[p["loan_category"]] = category_counts.get(p["loan_category"], 0) + 1

    # Monthly EMI burden across all active loans
    total_monthly_emi = sum(l["emi_amount"] for l in active_loans if l["status"] == "active")

    # Payment status breakdown, for the "Payment status" chart
    active_loan_ids = [l["_id"] for l in active_loans]
    status_counts = {"PAID": 0, "UPCOMING": 0, "DUE": 0, "OVERDUE": 0}
    if active_loan_ids:
        for p in collections["payments"].find({"active_loan_id": {"$in": active_loan_ids}}):
            status_counts[p["payment_status"]] = status_counts.get(p["payment_status"], 0) + 1

    recent_activity = []
    for a in sorted(applications, key=lambda x: x["application_date"], reverse=True)[:3]:
        recent_activity.append({
            "type": "eligibility_checked",
            "message": f"Checked eligibility for a {a['loan_category']} of ₹{a['loan_amount']:,.0f}",
            "date": a["application_date"].strftime("%Y-%m-%d") if hasattr(a["application_date"], "strftime") else str(a["application_date"]),
        })
    for r in collections["recommendations"].find({"application_id": {"$in": application_ids}}).sort("created_at", -1).limit(3):
        recent_activity.append({
            "type": "recommendation_generated",
            "message": f"New recommendation generated (match score {r['match_score']}%)",
            "date": r["created_at"].strftime("%Y-%m-%d") if hasattr(r["created_at"], "strftime") else str(r["created_at"]),
        })

    return {
        "welcome_name": user["full_name"],
        "cards": {
            "eligible_loans": eligible_count,
            "recommended_loans": recommended_count,
            "active_loans": active_count,
            "next_emi": next_emi,
        },
        "charts": {
            "eligible_by_category": category_counts,
            "recommended_vs_eligible": {"recommended": recommended_count, "eligible": eligible_count},
            "monthly_emi_burden": total_monthly_emi,
            "payment_status": status_counts,
        },
        "notifications": notifications,
        "recent_activity": recent_activity,
    }
