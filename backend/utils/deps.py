"""
utils/deps.py
--------------
Purpose:
    FastAPI "dependencies" that routes plug into their function signature
    to require login (get_current_user) or require admin role
    (get_current_admin). This is what "Protect admin routes" (#45) means
    in code: any route with `Depends(get_current_admin)` returns 403 for
    non-admins automatically, before the route body even runs.
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from database.mongodb import collections
from utils.security import decode_access_token

bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Reads the "Authorization: Bearer <token>" header, verifies the JWT,
    loads the matching user document from MongoDB and returns it.
    Any route that includes `user = Depends(get_current_user)` is now
    a "logged-in users only" route.
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        user = collections["users"].find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    """Same as get_current_user, but also enforces role == 'admin'."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
