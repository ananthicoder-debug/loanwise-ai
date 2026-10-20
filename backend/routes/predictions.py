"""
routes/predictions.py
-----------------------
Endpoints (matches spec #28 exactly):
    POST /api/predictions/eligibility     -> run Model 1 only, for a given application_id
    POST /api/predictions/affordability   -> run Model 2 only, for a given application_id

These exist mainly for API completeness / testing Model 1 and Model 2 in
isolation (e.g. from /docs or Postman). The normal user flow uses the
combined POST /api/applications endpoint instead, which runs both plus
the recommendation engine in one call.
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from database.mongodb import collections
from utils.deps import get_current_user
from services.eligibility_service import evaluate_products_for_application
from services.affordability_service import evaluate_affordability

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


class ApplicationIdBody(BaseModel):
    application_id: str


def _load_application(application_id: str, user: dict) -> dict:
    try:
        application = collections["loan_applications"].find_one({
            "_id": ObjectId(application_id), "user_id": user["_id"]
        })
    except InvalidId:
        raise HTTPException(status_code=404, detail="Application not found.")
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    return application


@router.post("/eligibility")
def run_eligibility_only(body: ApplicationIdBody, user: dict = Depends(get_current_user)):
    application = _load_application(body.application_id, user)
    credit_profile = collections["credit_profiles"].find_one({"user_id": user["_id"]})
    if not credit_profile:
        raise HTTPException(status_code=400, detail="Complete your credit profile first.")
    return evaluate_products_for_application(credit_profile, application)


@router.post("/affordability")
def run_affordability_only(body: ApplicationIdBody, user: dict = Depends(get_current_user)):
    application = _load_application(body.application_id, user)
    credit_profile = collections["credit_profiles"].find_one({"user_id": user["_id"]})
    if not credit_profile:
        raise HTTPException(status_code=400, detail="Complete your credit profile first.")
    eligibility_output = evaluate_products_for_application(credit_profile, application)
    return {
        "model_1": eligibility_output["model_1"],
        "products": evaluate_affordability(credit_profile, application, eligibility_output["products"]),
    }
