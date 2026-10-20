"""
routes/recommendations.py
----------------------------
Endpoints:
    GET /api/recommendations       -> ALL of the user's saved recommendations
                                       (across every application), newest first
    GET /api/recommendations/{id}  -> one recommendation, with full product+lender detail
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from database.mongodb import collections
from utils.deps import get_current_user

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _enrich(rec: dict) -> dict:
    product = collections["loan_products"].find_one({"_id": rec["product_id"]})
    lender  = collections["lenders"].find_one({"_id": product["lender_id"]}) if product else None

    rec["_id"]            = str(rec["_id"])
    rec["application_id"] = str(rec["application_id"])
    rec["product_id"]     = str(rec["product_id"])
    if product:
        product["_id"]          = str(product["_id"])
        product["lender_id"]    = str(product["lender_id"])
        product["lender_name"]  = lender["lender_name"] if lender else "Unknown Lender"
        product["lender_website"] = lender.get("official_website", "") if lender else ""
    rec["product"] = product
    return rec


@router.get("")
def list_recommendations(user: dict = Depends(get_current_user)):
    application_ids = [
        a["_id"] for a in collections["loan_applications"].find({"user_id": user["_id"]}, {"_id": 1})
    ]
    recs = list(
        collections["recommendations"]
        .find({"application_id": {"$in": application_ids}})
        .sort("created_at", -1)
    )
    return [_enrich(r) for r in recs]


@router.get("/{recommendation_id}")
def get_recommendation(recommendation_id: str, user: dict = Depends(get_current_user)):
    try:
        rec = collections["recommendations"].find_one({"_id": ObjectId(recommendation_id)})
    except InvalidId:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    application = collections["loan_applications"].find_one({"_id": rec["application_id"], "user_id": user["_id"]})
    if not application:
        raise HTTPException(status_code=403, detail="Not your recommendation.")

    return _enrich(rec)
