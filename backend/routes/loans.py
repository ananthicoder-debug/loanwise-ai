"""
routes/loans.py
-----------------
GET /api/loans                    -> browse full catalogue grouped by category -> lender
GET /api/loans/categories         -> category list with product + lender counts
GET /api/loans/lenders            -> lender list with product counts
GET /api/loans/lenders/{id}       -> single lender detail + their products
GET /api/loans/search?q=          -> search across product/lender/category
GET /api/loans/compare?ids=       -> compare 2-4 products side by side
GET /api/loans/{id}               -> single product full detail

All counts come from MongoDB aggregation  -  never hardcoded.
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List

from database.mongodb import collections
from utils.deps import get_current_user
from services.recommendation_service import group_by_category_and_lender

router = APIRouter(prefix="/api/loans", tags=["loans"])


def _attach_lender(products: list) -> list:
    lender_ids = {p["lender_id"] for p in products if p.get("lender_id")}
    lenders_by_id = {
        l["_id"]: l for l in collections["lenders"].find({"_id": {"$in": list(lender_ids)}})
    }
    for p in products:
        lender = lenders_by_id.get(p.get("lender_id"))
        p["lender_name"] = lender["lender_name"] if lender else "Unknown Lender"
        p["lender_website"] = lender.get("official_website", "") if lender else ""
        p["_id"] = str(p["_id"])
        p["lender_id"] = str(p["lender_id"]) if p.get("lender_id") else None
    return products


@router.get("/categories")
def loan_categories(user: dict = Depends(get_current_user)):
    """Returns each category with product_count and lender_count from MongoDB."""
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": "$loan_category",
            "product_count": {"$sum": 1},
            "lender_ids": {"$addToSet": "$lender_id"}
        }},
        {"$project": {
            "category": "$_id",
            "product_count": 1,
            "lender_count": {"$size": "$lender_ids"},
            "_id": 0
        }},
        {"$sort": {"product_count": -1}}
    ]
    return list(collections["loan_products"].aggregate(pipeline))


@router.get("/lenders")
def loan_lenders(user: dict = Depends(get_current_user)):
    """Returns all lenders with their product count."""
    pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": "$lender_id",
            "product_count": {"$sum": 1},
            "categories": {"$addToSet": "$loan_category"}
        }},
        {"$lookup": {
            "from": "lenders",
            "localField": "_id",
            "foreignField": "_id",
            "as": "lender_info"
        }},
        {"$unwind": "$lender_info"},
        {"$match": {"lender_info.status": {"$ne": "inactive"}}},
        {"$project": {
            "_id": {"$toString": "$_id"},
            "lender_name": "$lender_info.lender_name",
            "lender_type": "$lender_info.lender_type",
            "official_website": "$lender_info.official_website",
            "verification_status": "$lender_info.verification_status",
            "headquarters_city": "$lender_info.headquarters_city",
            "state": "$lender_info.state",
            "product_count": 1,
            "categories": 1
        }},
        {"$sort": {"product_count": -1}}
    ]
    return list(collections["loan_products"].aggregate(pipeline))


@router.get("/lenders/{lender_id}")
def get_lender_detail(lender_id: str, user: dict = Depends(get_current_user)):
    """Returns lender info + their products."""
    try:
        lender = collections["lenders"].find_one({"_id": ObjectId(lender_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Lender not found.")
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found.")

    products = list(collections["loan_products"].find({"lender_id": ObjectId(lender_id), "is_active": True}))
    for p in products:
        p["_id"] = str(p["_id"])
        p["lender_id"] = str(p["lender_id"])

    lender["_id"] = str(lender["_id"])
    return {"lender": lender, "products": products, "product_count": len(products)}


@router.get("/compare")
def compare_loans(
    ids: str = Query(..., description="Comma-separated product IDs, 2-4 items"),
    user: dict = Depends(get_current_user)
):
    """Returns 2-4 products side by side for comparison."""
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if len(id_list) < 2 or len(id_list) > 4:
        raise HTTPException(status_code=400, detail="Provide 2 to 4 product IDs separated by commas.")

    products = []
    for pid in id_list:
        try:
            product = collections["loan_products"].find_one({"_id": ObjectId(pid)})
        except InvalidId:
            continue
        if product:
            products.append(product)

    products = _attach_lender(products)

    # Attach affordability context from user's latest prediction if available
    credit_profile = collections["credit_profiles"].find_one({"user_id": user["_id"]}) or {}
    for p in products:
        conditions_met = (
            credit_profile.get("annual_income", 0) >= p.get("minimum_income", 0)
            and credit_profile.get("cibil_score", 0) >= p.get("minimum_cibil", 0)
        )
        p["eligibility_indicator"] = "Potentially Eligible" if conditions_met else "Check Eligibility"

    return products


@router.get("/search")
def search_loans(q: str, user: dict = Depends(get_current_user)):
    if not q or len(q.strip()) < 2:
        return []

    regex = {"$regex": q.strip(), "$options": "i"}
    matched_lender_ids = [l["_id"] for l in collections["lenders"].find(
        {"$or": [{"lender_name": regex}, {"lender_code": regex}]}
    )]

    query = {
        "is_active": True,
        "$or": [
            {"product_name": regex},
            {"loan_category": regex},
            {"purpose": regex},
            {"lender_id": {"$in": matched_lender_ids}},
        ],
    }
    products = list(collections["loan_products"].find(query).limit(50))
    products = _attach_lender(products)

    credit_profile = collections["credit_profiles"].find_one({"user_id": user["_id"]}) or {}
    for p in products:
        conditions_met = (
            credit_profile.get("annual_income", 0) >= p.get("minimum_income", 0)
            and credit_profile.get("cibil_score", 0) >= p.get("minimum_cibil", 0)
        )
        p["eligibility_status"] = "Potentially Eligible" if conditions_met else "Not Eligible"
        p["matching_criteria"] = {
            "minimum_income_required": p.get("minimum_income", 0),
            "your_annual_income": credit_profile.get("annual_income", 0),
            "minimum_cibil_required": p.get("minimum_cibil", 0),
            "your_cibil_score": credit_profile.get("cibil_score", 0),
        }
    return products


@router.get("")
def browse_loans(user: dict = Depends(get_current_user)):
    products = list(collections["loan_products"].find({"is_active": True}))
    products = _attach_lender(products)
    return group_by_category_and_lender(products)


@router.get("/{product_id}")
def get_loan_detail(product_id: str, user: dict = Depends(get_current_user)):
    try:
        product = collections["loan_products"].find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Loan product not found.")
    if not product:
        raise HTTPException(status_code=404, detail="Loan product not found.")

    lender = collections["lenders"].find_one({"_id": product["lender_id"]})
    product["_id"] = str(product["_id"])
    product["lender_id"] = str(product["lender_id"])
    product["lender_name"] = lender["lender_name"] if lender else "Unknown Lender"
    product["lender_website"] = lender.get("official_website", "") if lender else ""
    product["lender_type"] = lender.get("lender_type", "") if lender else ""
    return product
