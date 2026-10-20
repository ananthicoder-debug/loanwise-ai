"""
routes/notifications.py
-------------------------
GET  /api/notifications           -> list notifications for the logged-in user
PUT  /api/notifications/{id}/read -> mark one notification as read
PUT  /api/notifications/read-all  -> mark all as read
"""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException

from database.mongodb import collections
from utils.deps import get_current_user
from services.notification_service import get_notifications_for_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(user: dict = Depends(get_current_user)):
    notifications = get_notifications_for_user(str(user["_id"]))
    # Also fetch persisted notifications from the notifications collection
    persisted = list(
        collections["notifications"]
        .find({"user_id": user["_id"]})
        .sort("created_at", -1)
        .limit(50)
    )
    for n in persisted:
        n["_id"] = str(n["_id"])
        n["user_id"] = str(n["user_id"])
    return {"emi_notifications": notifications, "system_notifications": persisted}


@router.put("/{notification_id}/read")
def mark_read(notification_id: str, user: dict = Depends(get_current_user)):
    try:
        result = collections["notifications"].update_one(
            {"_id": ObjectId(notification_id), "user_id": user["_id"]},
            {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Notification not found.")
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"message": "Marked as read."}


@router.put("/read-all")
def mark_all_read(user: dict = Depends(get_current_user)):
    collections["notifications"].update_many(
        {"user_id": user["_id"], "is_read": False},
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc)}}
    )
    return {"message": "All notifications marked as read."}
