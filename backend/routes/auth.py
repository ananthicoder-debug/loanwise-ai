"""
routes/auth.py
---------------
Endpoints:
    POST /api/auth/register  -> create account, hash password, return JWT
    POST /api/auth/login     -> verify password, return JWT
    GET  /api/auth/me        -> return the logged-in user's basic info

Errors handled:
    - duplicate email -> 400
    - wrong password / unknown email -> 401 (deliberately vague message
      so we don't reveal which part was wrong - basic security hygiene)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from database.mongodb import collections
from models.user import RegisterRequest, LoginRequest, TokenResponse
from utils.security import hash_password, verify_password, create_access_token
from utils.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest):
    if collections["users"].find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user_doc = {
        "full_name": payload.full_name,
        "email": payload.email,
        "phone": payload.phone,
        "password_hash": hash_password(payload.password),
        "role": "user",
        "date_of_birth": None,
        "gender": None,
        "address": {"street": "", "city": "", "state": "", "pincode": ""},
        "created_at": datetime.now(timezone.utc),
    }
    result = collections["users"].insert_one(user_doc)

    # Every new user gets an empty credit profile shell so the profile
    # page has something to update rather than crashing on "not found".
    collections["credit_profiles"].insert_one({
        "user_id": result.inserted_id,
        "monthly_income": 0, "annual_income": 0, "employment_type": "Salaried",
        "dependents": 0, "cibil_score": 650, "existing_loans": 0,
        "outstanding_debt": 0, "current_emi": 0, "credit_history": "Good",
        "missed_payments": 0, "late_payments": 0, "previous_loans": 0,
        "education": "Graduate", "age": 25,
    })

    token = create_access_token({"sub": str(result.inserted_id), "role": "user"})
    return TokenResponse(access_token=token, role="user", full_name=payload.full_name)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = collections["users"].find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return TokenResponse(access_token=token, role=user["role"], full_name=user["full_name"])


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
    }
