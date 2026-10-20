"""
routes/applications.py
------------------------
Endpoints:
    POST /api/applications          -> submit a loan requirement, RUN Model 1 + Model 2
                                        + recommendation engine, return full results
    GET  /api/applications          -> list the user's past applications
    GET  /api/applications/{id}     -> re-fetch one application's full results

This is the single endpoint the "CHECK MY ELIGIBILITY" button calls
(spec #47 demo flow). It intentionally does the whole pipeline in one
request so the frontend stays simple.
"""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from database.mongodb import collections
from models.loan import LoanApplicationRequest
from utils.deps import get_current_user
from services.recommendation_service import run_full_evaluation

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("")
def create_application(payload: LoanApplicationRequest, user: dict = Depends(get_current_user)):
    application_doc = {
        "user_id": user["_id"],
        "loan_amount": payload.loan_amount,
        "loan_tenure": payload.loan_tenure,
        "loan_category": payload.loan_category,
        "purpose": payload.purpose,
        "application_date": datetime.now(timezone.utc),
        "status": "evaluated",
    }
    result = collections["loan_applications"].insert_one(application_doc)
    application_doc["_id"] = result.inserted_id

    try:
        evaluation = run_full_evaluation(str(user["_id"]), application_doc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "application_id": str(application_doc["_id"]),
        "loan_category": payload.loan_category,
        "loan_amount": payload.loan_amount,
        "loan_tenure": payload.loan_tenure,
        **evaluation,
    }


@router.get("")
def list_applications(user: dict = Depends(get_current_user)):
    apps = list(collections["loan_applications"].find({"user_id": user["_id"]}).sort("application_date", -1))
    for a in apps:
        a["_id"] = str(a["_id"])
        a["user_id"] = str(a["user_id"])
    return apps


@router.get("/{application_id}")
def get_application_results(application_id: str, user: dict = Depends(get_current_user)):
    """
    Re-runs the (deterministic) evaluation for an existing application so
    the Eligible-Loans / Recommended-Loans pages can be reloaded or
    deep-linked without resubmitting the form.
    """
    try:
        application = collections["loan_applications"].find_one({
            "_id": ObjectId(application_id), "user_id": user["_id"]
        })
    except InvalidId:
        raise HTTPException(status_code=404, detail="Application not found.")

    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    evaluation = run_full_evaluation(str(user["_id"]), application)
    return {
        "application_id": str(application["_id"]),
        "loan_category": application["loan_category"],
        "loan_amount": application["loan_amount"],
        "loan_tenure": application["loan_tenure"],
        **evaluation,
    }
