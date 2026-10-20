"""
routes/credit.py
-----------------
Separate router for credit profile endpoints.
GET /api/credit-profile
PUT /api/credit-profile
"""

from bson import ObjectId
from fastapi import APIRouter, Depends
from database.mongodb import collections
from models.user import CreditProfileUpdateRequest
from utils.deps import get_current_user

router = APIRouter(tags=["credit"])


@router.get("/api/credit-profile")
def get_credit_profile(user: dict = Depends(get_current_user)):
    profile = collections["credit_profiles"].find_one({"user_id": user["_id"]})
    if profile:
        profile["_id"] = str(profile["_id"])
        profile["user_id"] = str(profile["user_id"])
    return profile or {}


@router.put("/api/credit-profile")
def update_credit_profile(payload: CreditProfileUpdateRequest, user: dict = Depends(get_current_user)):
    update = payload.model_dump(exclude_unset=True)
    # Normalise legacy aliases so both old and new frontend work
    if "current_emi" in update and update["current_emi"] is not None:
        update.setdefault("existing_emi", update.pop("current_emi"))
    if "credit_history" in update and update["credit_history"] is not None:
        update.pop("credit_history")   # no longer a separate field

    # Derive annual_income if only monthly given
    if "monthly_income" in update and "annual_income" not in update:
        update["annual_income"] = update["monthly_income"] * 12

    collections["credit_profiles"].update_one(
        {"user_id": user["_id"]}, {"$set": update}, upsert=True
    )
    profile = collections["credit_profiles"].find_one({"user_id": user["_id"]})
    profile["_id"] = str(profile["_id"])
    profile["user_id"] = str(profile["user_id"])
    return profile
