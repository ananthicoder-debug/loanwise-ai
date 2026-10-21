"""
routes/feedback.py
--------------------
POST /api/feedback        -> submit feedback
GET  /api/feedback        -> user's own feedback list
GET  /api/admin/feedback  -> admin: all feedback
"""

from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from database.mongodb import collections
from utils.deps import get_current_user, get_current_admin

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackRequest(BaseModel):
    rating: int                      # 1-5
    category: Optional[str] = "General"
    comments: Optional[str] = ""
    product_id: Optional[str] = None
    application_id: Optional[str] = None


@router.post("")
def submit_feedback(payload: FeedbackRequest, user: dict = Depends(get_current_user)):
    doc = {
        "user_id": user["_id"],
        "rating": min(5, max(1, payload.rating)),
        "category": payload.category,
        "comments": payload.comments,
        "product_id": ObjectId(payload.product_id) if payload.product_id else None,
        "application_id": ObjectId(payload.application_id) if payload.application_id else None,
        "created_at": datetime.now(timezone.utc),
    }
    result = collections["feedback"].insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    doc["user_id"] = str(user["_id"])
    return doc


@router.get("")
def my_feedback(user: dict = Depends(get_current_user)):
    items = list(collections["feedback"].find({"user_id": user["_id"]}).sort("created_at", -1))
    for item in items:
        item["_id"] = str(item["_id"])
        item["user_id"] = str(item["user_id"])
        if item.get("product_id"):
            item["product_id"] = str(item["product_id"])
        if item.get("application_id"):
            item["application_id"] = str(item["application_id"])
    return items


@router.get("/admin/all")
def admin_feedback(admin: dict = Depends(get_current_admin)):
    items = list(collections["feedback"].find().sort("created_at", -1).limit(500))
    users_by_id = {u["_id"]: u["full_name"] for u in collections["users"].find({}, {"full_name": 1})}
    for item in items:
        item["_id"] = str(item["_id"])
        item["user_name"] = users_by_id.get(item["user_id"], "Unknown")
        item["user_id"] = str(item["user_id"])
        if item.get("product_id"):
            item["product_id"] = str(item["product_id"])
        if item.get("application_id"):
            item["application_id"] = str(item["application_id"])
    return items
