"""
routes/admin.py
-----------------
Admin-only routes. All require Depends(get_current_admin)  -  403 for regular users.

Covers: dashboard, users, applications, predictions, recommendations,
lenders CRUD, products CRUD, active loans, payments, feedback.
"""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from database.mongodb import collections
from models.loan import LenderCreateRequest, LoanProductCreateRequest, LoanProductUpdateRequest
from utils.deps import get_current_admin


def _s(v):
    """Safe serializer  -  converts ObjectId -> str, datetime -> ISO string."""
    if v is None:
        return None
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, datetime):
        return v.isoformat()
    return v

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ??? Dashboard ????????????????????????????????????????????????????????????????

@router.get("/dashboard")
def admin_dashboard(admin: dict = Depends(get_current_admin)):
    overdue_count = collections["payments"].count_documents({"payment_status": "OVERDUE"})
    predictions_count = collections["predictions"].count_documents({})
    recommendations_count = collections["recommendations"].count_documents({})

    # Applications by category
    cat_pipeline = [
        {"$group": {"_id": "$loan_category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    apps_by_category = {r["_id"]: r["count"] for r in collections["loan_applications"].aggregate(cat_pipeline)}

    # Products by lender - explicitly convert _id to string to avoid ObjectId serialization issues
    prod_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$lender_id", "count": {"$sum": 1}}},
        {"$lookup": {"from": "lenders", "localField": "_id", "foreignField": "_id", "as": "lender"}},
        {"$unwind": "$lender"},
        {"$project": {"lender_name": "$lender.lender_name", "count": 1, "_id": 0}},
        {"$sort": {"count": -1}}
    ]
    products_by_lender = [
        {"lender_name": r["lender_name"], "count": r["count"]}
        for r in collections["loan_products"].aggregate(prod_pipeline)
    ]

    # Payment status counts
    pay_pipeline = [
        {"$group": {"_id": "$payment_status", "count": {"$sum": 1}}}
    ]
    payment_status = {r["_id"]: r["count"] for r in collections["payments"].aggregate(pay_pipeline)}

    return {
        "total_users": collections["users"].count_documents({"role": "user"}),
        "total_applications": collections["loan_applications"].count_documents({}),
        "total_lenders": collections["lenders"].count_documents({}),
        "active_loan_products": collections["loan_products"].count_documents({"is_active": True}),
        "total_predictions": predictions_count,
        "total_recommendations": recommendations_count,
        "active_loans": collections["active_loans"].count_documents({"status": "active"}),
        "total_payments": collections["payments"].count_documents({}),
        "overdue_payments": overdue_count,
        "charts": {
            "apps_by_category": apps_by_category,
            "products_by_lender": products_by_lender,
            "payment_status": payment_status,
        },
    }


# ??? Users ???????????????????????????????????????????????????????????????????

@router.get("/users")
def list_users(admin: dict = Depends(get_current_admin)):
    users = list(collections["users"].find({"role": "user"}).sort("created_at", -1))
    for u in users:
        u["_id"] = str(u["_id"])
        u.pop("password_hash", None)
        # Count their applications
        u["application_count"] = collections["loan_applications"].count_documents({"user_id": ObjectId(u["_id"])})
    return users


@router.put("/users/{user_id}/status")
def toggle_user_status(user_id: str, admin: dict = Depends(get_current_admin)):
    try:
        user = collections["users"].find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="User not found.")
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    new_status = "inactive" if user.get("status", "active") == "active" else "active"
    collections["users"].update_one({"_id": ObjectId(user_id)}, {"$set": {"status": new_status}})
    return {"message": f"User status set to {new_status}.", "status": new_status}


# ??? Applications ?????????????????????????????????????????????????????????????

@router.get("/applications")
def list_all_applications(admin: dict = Depends(get_current_admin)):
    apps = list(collections["loan_applications"].find().sort("application_date", -1).limit(200))
    users_by_id = {u["_id"]: u["full_name"] for u in collections["users"].find({}, {"full_name": 1})}
    for a in apps:
        a["_id"] = str(a["_id"])
        a["applicant_name"] = users_by_id.get(a["user_id"], "Unknown")
        a["user_id"] = str(a["user_id"])
    return apps


# ??? Predictions ??????????????????????????????????????????????????????????????

@router.get("/predictions")
def list_all_predictions(admin: dict = Depends(get_current_admin)):
    preds = list(collections["predictions"].find().sort("created_at", -1).limit(200))
    for p in preds:
        p["_id"] = str(p["_id"])
        p["application_id"] = str(p["application_id"])
    return preds


# ??? Recommendations ??????????????????????????????????????????????????????????

@router.get("/recommendations")
def list_all_recommendations(admin: dict = Depends(get_current_admin)):
    recs = list(collections["recommendations"].find().sort("created_at", -1).limit(200))
    for r in recs:
        r["_id"] = str(r["_id"])
        r["application_id"] = str(r["application_id"])
        r["product_id"] = str(r["product_id"])
    return recs


# ??? Active Loans ?????????????????????????????????????????????????????????????

@router.get("/active-loans")
def list_all_active_loans(admin: dict = Depends(get_current_admin)):
    loans = list(collections["active_loans"].find().sort("created_at", -1).limit(200))
    users_by_id = {u["_id"]: u["full_name"] for u in collections["users"].find({}, {"full_name": 1})}
    products_by_id = {p["_id"]: p for p in collections["loan_products"].find({}, {"product_name": 1, "lender_id": 1})}
    lenders_by_id = {l["_id"]: l["lender_name"] for l in collections["lenders"].find({}, {"lender_name": 1})}
    result = []
    for l in loans:
        product = products_by_id.get(l.get("product_id"))
        lender_name = lenders_by_id.get(product["lender_id"], "Unknown") if product else "Unknown"
        result.append({
            "_id":             str(l["_id"]),
            "applicant_name":  users_by_id.get(l.get("user_id"), "Unknown"),
            "user_id":         str(l.get("user_id", "")),
            "product_id":      str(l.get("product_id", "")),
            "product_name":    product["product_name"] if product else "Unknown",
            "lender_name":     lender_name,
            "actual_amount":   l.get("actual_amount", 0),
            "emi_amount":      l.get("emi_amount", 0),
            "interest_rate":   l.get("interest_rate", 0),
            "tenure_months":   l.get("tenure_months", 0),
            "start_date":      l.get("start_date", ""),
            "status":          l.get("status", ""),
            "recommendation_id": str(l["recommendation_id"]) if l.get("recommendation_id") else None,
        })
    return result


# ??? Payments ?????????????????????????????????????????????????????????????????

@router.get("/payments")
def list_all_payments(admin: dict = Depends(get_current_admin)):
    payments = list(collections["payments"].find().sort("due_date", -1).limit(300))
    for p in payments:
        p["_id"] = str(p["_id"])
        p["active_loan_id"] = str(p["active_loan_id"])
    return payments


# ??? Feedback ?????????????????????????????????????????????????????????????????

@router.get("/model-performance")
def model_performance(admin: dict = Depends(get_current_admin)):
    """Return saved ML model performance metrics from MongoDB."""
    records = list(collections["system_metadata"].find(
        {"key": {"$regex": "^model_performance_"}}
    ))
    result = []
    for r in records:
        result.append({
            "_id":              str(r["_id"]),
            "model_name":       r.get("model_name", ""),
            "algorithm":        r.get("algorithm", ""),
            "features":         r.get("features", []),
            "training_records": r.get("training_records", 0),
            "testing_records":  r.get("testing_records", 0),
            "dataset_name":     r.get("dataset_name", ""),
            "metrics":          r.get("metrics", {}),
            "model_version":    r.get("model_version", ""),
            "model_file":       r.get("model_file", ""),
            "training_date":    r.get("training_date", ""),
            "disclaimer":       r.get("disclaimer", ""),
        })
    return result


@router.get("/feedback")
def list_feedback(admin: dict = Depends(get_current_admin)):
    """Return all user feedback with resolved user names."""
    items = list(collections["feedback"].find().sort("created_at", -1).limit(500))
    users_by_id = {u["_id"]: u["full_name"] for u in collections["users"].find({}, {"full_name": 1})}
    result = []
    for item in items:
        result.append({
            "_id":            str(item["_id"]),
            "user_name":      users_by_id.get(item.get("user_id"), "Unknown"),
            "user_id":        str(item.get("user_id", "")),
            "rating":         item.get("rating", 0),
            "category":       item.get("category", "General"),
            "comments":       item.get("comments", ""),
            "product_id":     str(item["product_id"]) if item.get("product_id") else None,
            "application_id": str(item["application_id"]) if item.get("application_id") else None,
            "created_at":     item["created_at"].isoformat() if hasattr(item.get("created_at"), "isoformat") else str(item.get("created_at", "")),
        })
    return result


# ??? Lenders ?????????????????????????????????????????????????????????????????

@router.post("/lenders")
def create_lender(payload: LenderCreateRequest, admin: dict = Depends(get_current_admin)):
    doc = payload.model_dump()
    result = collections["lenders"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@router.get("/lenders")
def list_lenders_admin(admin: dict = Depends(get_current_admin)):
    lenders = list(collections["lenders"].find())
    for l in lenders:
        l["_id"] = str(l["_id"])
        l["product_count"] = collections["loan_products"].count_documents({"lender_id": ObjectId(l["_id"])})
    return lenders


@router.put("/lenders/{lender_id}")
def update_lender(lender_id: str, payload: LenderCreateRequest, admin: dict = Depends(get_current_admin)):
    try:
        result = collections["lenders"].update_one({"_id": ObjectId(lender_id)}, {"$set": payload.model_dump()})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Lender not found.")
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lender not found.")
    updated = collections["lenders"].find_one({"_id": ObjectId(lender_id)})
    updated["_id"] = str(updated["_id"])
    return updated


@router.delete("/lenders/{lender_id}")
def deactivate_lender(lender_id: str, admin: dict = Depends(get_current_admin)):
    try:
        result = collections["lenders"].update_one(
            {"_id": ObjectId(lender_id)}, {"$set": {"status": "inactive"}}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Lender not found.")
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lender not found.")
    collections["loan_products"].update_many(
        {"lender_id": ObjectId(lender_id)}, {"$set": {"is_active": False}}
    )
    return {"message": "Lender deactivated. All associated products deactivated."}


# ??? Products ?????????????????????????????????????????????????????????????????

@router.post("/products")
def create_product(payload: LoanProductCreateRequest, admin: dict = Depends(get_current_admin)):
    doc = payload.model_dump()
    try:
        doc["lender_id"] = ObjectId(doc["lender_id"])
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail="Invalid lender_id.")
    doc["created_at"] = datetime.now(timezone.utc)
    result = collections["loan_products"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["lender_id"] = str(doc["lender_id"])
    return doc


@router.get("/products")
def list_products_admin(admin: dict = Depends(get_current_admin)):
    products = list(collections["loan_products"].find())
    lenders_by_id = {l["_id"]: l["lender_name"] for l in collections["lenders"].find()}
    for p in products:
        p["_id"] = str(p["_id"])
        p["lender_name"] = lenders_by_id.get(p.get("lender_id"), "Unknown Lender")
        if p.get("lender_id"):
            p["lender_id"] = str(p["lender_id"])
    return products


@router.put("/products/{product_id}")
def update_product(product_id: str, payload: LoanProductUpdateRequest, admin: dict = Depends(get_current_admin)):
    update_fields = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    try:
        result = collections["loan_products"].update_one(
            {"_id": ObjectId(product_id)}, {"$set": update_fields}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Loan product not found.")
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Loan product not found.")
    updated = collections["loan_products"].find_one({"_id": ObjectId(product_id)})
    updated["_id"] = str(updated["_id"])
    if updated.get("lender_id"):
        updated["lender_id"] = str(updated["lender_id"])
    return updated


@router.delete("/products/{product_id}")
def deactivate_product(product_id: str, admin: dict = Depends(get_current_admin)):
    try:
        result = collections["loan_products"].update_one(
            {"_id": ObjectId(product_id)}, {"$set": {"is_active": False}}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Loan product not found.")
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Loan product not found.")
    return {"message": "Loan product deactivated."}
