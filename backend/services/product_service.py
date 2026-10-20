"""
services/product_service.py
-----------------------------
Purpose:
    Central service layer for loan product catalogue operations.
    Provides helpers for:
      - fetching and enriching products with lender information
      - filtering and searching products
      - computing estimated EMIs on product cards
      - attaching a lightweight eligibility indicator based on credit profile
        rules only (no ML model call — fast, for catalogue browsing)

This keeps product-related logic DRY across routes/loans.py,
routes/datasets.py, and the admin routes.
"""

from bson import ObjectId
from bson.errors import InvalidId
from typing import Optional

from database.mongodb import collections
from services.emi_service import calculate_emi


# ─── Lender Cache Helper ──────────────────────────────────────────────────────

def _get_lenders_by_id(lender_ids: set) -> dict:
    """
    Returns a dict of {ObjectId: lender_doc} for the given set of lender IDs.
    Used to avoid N+1 queries when hydrating a list of products.
    """
    if not lender_ids:
        return {}
    return {
        l["_id"]: l
        for l in collections["lenders"].find({"_id": {"$in": list(lender_ids)}})
    }


# ─── Product Hydration ────────────────────────────────────────────────────────

def attach_lender_info(products: list) -> list:
    """
    Mutates each product in-place to add:
      - lender_name
      - lender_website
      - lender_type
    Converts _id and lender_id to strings.
    """
    lender_ids = {p["lender_id"] for p in products if p.get("lender_id")}
    lenders_by_id = _get_lenders_by_id(lender_ids)

    for p in products:
        lender = lenders_by_id.get(p.get("lender_id"))
        p["lender_name"]    = lender["lender_name"]    if lender else "Unknown Lender"
        p["lender_website"] = lender.get("official_website", "") if lender else ""
        p["lender_type"]    = lender.get("lender_type", "")      if lender else ""
        p["_id"]       = str(p["_id"])
        p["lender_id"] = str(p["lender_id"]) if p.get("lender_id") else None

    return products


def attach_estimated_emi(products: list, loan_amount: float, tenure_months: int) -> list:
    """
    For each product computes an estimated EMI at the given loan_amount and
    tenure, using the mid-point of the product's interest rate range.
    Sets product["estimated_emi"]. Silently skips on bad inputs.
    """
    for p in products:
        try:
            mid_rate = (p["interest_rate_min"] + p["interest_rate_max"]) / 2
            p["estimated_emi"] = calculate_emi(loan_amount, mid_rate, tenure_months)
        except Exception:
            p["estimated_emi"] = None
    return products


def attach_rule_eligibility_indicator(products: list, credit_profile: dict) -> list:
    """
    Attaches a lightweight rule-based eligibility indicator to each product
    card WITHOUT calling the ML model. Used for browsing the full catalogue
    where running the model on every product would be too slow.

    Sets product["eligibility_indicator"]:
        "Potentially Eligible" — passes basic income + CIBIL rules
        "Check Eligibility"    — does not meet one or more product rules,
                                 or no credit profile available
    """
    if not credit_profile:
        for p in products:
            p["eligibility_indicator"] = "Check Eligibility"
        return products

    annual_income = credit_profile.get("annual_income", 0)
    cibil_score   = credit_profile.get("cibil_score", 0)

    for p in products:
        income_ok = annual_income >= p.get("minimum_income", 0)
        cibil_ok  = cibil_score   >= p.get("minimum_cibil",  0)
        p["eligibility_indicator"] = (
            "Potentially Eligible" if (income_ok and cibil_ok) else "Check Eligibility"
        )

    return products


# ─── Product Fetching ─────────────────────────────────────────────────────────

def get_active_products(category: Optional[str] = None) -> list:
    """
    Returns all active loan products, optionally filtered by category.
    Does not attach lender info (call attach_lender_info separately).
    """
    query: dict = {"is_active": True}
    if category:
        query["loan_category"] = category
    return list(collections["loan_products"].find(query))


def get_product_by_id(product_id: str) -> Optional[dict]:
    """
    Fetches a single product by its string _id.
    Returns None if not found or ID is invalid.
    """
    try:
        product = collections["loan_products"].find_one({"_id": ObjectId(product_id)})
    except InvalidId:
        return None
    if product:
        product = attach_lender_info([product])[0]
    return product


def get_products_for_compare(id_list: list[str]) -> list:
    """
    Fetches 2–4 products by their string IDs for the compare page.
    Attaches lender info. Returns only products that exist.
    """
    products = []
    for pid in id_list:
        try:
            p = collections["loan_products"].find_one({"_id": ObjectId(pid)})
        except InvalidId:
            continue
        if p:
            products.append(p)
    return attach_lender_info(products) if products else []


# ─── Search ───────────────────────────────────────────────────────────────────

def search_products(query_str: str, limit: int = 50) -> list:
    """
    Full-text-style search across product_name, loan_category, purpose,
    and lender_name. Returns hydrated products with lender info.
    """
    q = query_str.strip()
    if not q or len(q) < 2:
        return []

    regex = {"$regex": q, "$options": "i"}
    matched_lender_ids = [l["_id"] for l in collections["lenders"].find({"lender_name": regex})]

    mongo_query = {
        "is_active": True,
        "$or": [
            {"product_name":  regex},
            {"loan_category": regex},
            {"purpose":       regex},
            {"lender_id": {"$in": matched_lender_ids}},
        ],
    }
    products = list(collections["loan_products"].find(mongo_query).limit(limit))
    return attach_lender_info(products)


# ─── Catalogue Stats ──────────────────────────────────────────────────────────

def get_catalogue_summary() -> dict:
    """
    Returns high-level catalogue statistics without hardcoding any numbers.
    Used by the admin dashboard and dataset management page.
    """
    total_products  = collections["loan_products"].count_documents({})
    active_products = collections["loan_products"].count_documents({"is_active": True})
    total_lenders   = collections["lenders"].count_documents({})
    active_lenders  = collections["lenders"].count_documents({"status": {"$ne": "inactive"}})

    # Category breakdown
    category_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": "$loan_category",
            "product_count": {"$sum": 1},
            "lender_count":  {"$addToSet": "$lender_id"},
        }},
        {"$project": {
            "category":      "$_id",
            "product_count": 1,
            "lender_count":  {"$size": "$lender_count"},
            "_id": 0,
        }},
        {"$sort": {"product_count": -1}},
    ]
    categories = list(collections["loan_products"].aggregate(category_pipeline))

    # Products per lender
    lender_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {
            "_id":           "$lender_id",
            "product_count": {"$sum": 1},
        }},
        {"$lookup": {
            "from":         "lenders",
            "localField":   "_id",
            "foreignField": "_id",
            "as":           "lender_info",
        }},
        {"$unwind": "$lender_info"},
        {"$project": {
            "_id":          {"$toString": "$_id"},
            "lender_name":  "$lender_info.lender_name",
            "product_count": 1,
        }},
        {"$sort": {"product_count": -1}},
    ]
    products_by_lender = list(collections["loan_products"].aggregate(lender_pipeline))

    return {
        "total_products":      total_products,
        "active_products":     active_products,
        "total_lenders":       total_lenders,
        "active_lenders":      active_lenders,
        "categories":          categories,
        "products_by_lender":  products_by_lender,
    }
