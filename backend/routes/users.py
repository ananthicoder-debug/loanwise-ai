"""
routes/users.py
-----------------
GET /api/users/profile  -> personal info
PUT /api/users/profile  -> update personal info
"""

from fastapi import APIRouter, Depends
from database.mongodb import collections
from models.user import ProfileUpdateRequest
from utils.deps import get_current_user

router = APIRouter(tags=["users"])


def _serialize_user(user: dict) -> dict:
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    return user


@router.get("/api/users/profile")
def get_profile(user: dict = Depends(get_current_user)):
    return _serialize_user(user)


@router.put("/api/users/profile")
def update_profile(payload: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    update_fields = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if update_fields.get("address"):
        update_fields["address"] = payload.address.model_dump()
    if update_fields:
        collections["users"].update_one({"_id": user["_id"]}, {"$set": update_fields})
    updated = collections["users"].find_one({"_id": user["_id"]})
    return _serialize_user(updated)
