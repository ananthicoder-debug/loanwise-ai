"""
routes/assessment.py
---------------------
Full two-model assessment endpoints with explainability, calculation
traces, what-if analysis, and report retrieval.

POST /api/assessment/full/{application_id}     -  run full assessment, save to DB
POST /api/assessment/what-if/{application_id}  -  what-if scenario (not saved)
GET  /api/assessment/{assessment_id}            -  retrieve saved assessment
GET  /api/assessment/history                    -  user's assessment history
GET  /api/assessment/latest/{application_id}   -  latest for an application
"""

from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from database.mongodb import collections
from utils.deps import get_current_user
from services.assessment_service import run_full_assessment, run_what_if

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


class WhatIfRequest(BaseModel):
    loan_amount:   Optional[float] = None
    proposed_rate: Optional[float] = None
    loan_tenure:   Optional[int]   = None


def _load_application(application_id: str, user_id: ObjectId) -> dict:
    try:
        app = collections["loan_applications"].find_one(
            {"_id": ObjectId(application_id), "user_id": user_id}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Application not found.")
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")
    return app


def _serialize_assessment(doc: dict) -> dict:
    """Convert ObjectId fields to strings for JSON serialization."""
    if doc.get("_id"):
        doc["_id"] = str(doc["_id"])
    if doc.get("user_id"):
        doc["user_id"] = str(doc["user_id"])
    if doc.get("application_id"):
        doc["application_id"] = str(doc["application_id"])
    return doc


# ??? Full assessment ??????????????????????????????????????????????????????????

@router.post("/full/{application_id}")
def run_assessment(application_id: str, user: dict = Depends(get_current_user)):
    """
    Run the complete two-model assessment for an existing application.
    Saves the result to MongoDB financial_analysis_reports.
    Returns the full assessment with calculations, explainability,
    eligible products, and recommendations.
    """
    app = _load_application(application_id, user["_id"])
    try:
        result = run_full_assessment(str(user["_id"]), app)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")

    # Save to MongoDB
    save_doc = {
        **result,
        "_saved_type": "full_assessment",
        "user_id":      user["_id"],
        "application_id": app["_id"],
        "generated_at": datetime.now(timezone.utc),
    }
    collections["financial_analysis_reports"].replace_one(
        {"user_id": user["_id"], "application_id": app["_id"], "_saved_type": "full_assessment"},
        save_doc,
        upsert=True,
    )
    result["saved"] = True
    return result


# ??? What-if scenario ?????????????????????????????????????????????????????????

@router.post("/what-if/{application_id}")
def what_if_scenario(
    application_id: str,
    body: WhatIfRequest,
    user: dict = Depends(get_current_user),
):
    """
    Run a what-if scenario without modifying the saved application.
    """
    app = _load_application(application_id, user["_id"])
    what_if = body.model_dump(exclude_none=True)
    if not what_if:
        raise HTTPException(status_code=400, detail="Provide at least one what-if parameter.")
    try:
        result = run_what_if(str(user["_id"]), app, what_if)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"What-if analysis failed: {str(e)}")
    return result


# ??? Retrieve saved assessments ???????????????????????????????????????????????

@router.get("/history")
def assessment_history(user: dict = Depends(get_current_user)):
    """List all saved assessments for the authenticated user."""
    docs = list(
        collections["financial_analysis_reports"]
        .find({"user_id": user["_id"], "_saved_type": "full_assessment"})
        .sort("generated_at", -1)
        .limit(20)
    )
    results = []
    for d in docs:
        results.append({
            "_id":           str(d["_id"]),
            "application_id": str(d.get("application_id", "")),
            "generated_at":   d.get("generated_at", "").isoformat() if hasattr(d.get("generated_at"), "isoformat") else str(d.get("generated_at", "")),
            "eligibility_result": (d.get("eligibility") or {}).get("result", ""),
            "affordability_result": (d.get("affordability") or {}).get("result", ""),
            "eligible_count":   d.get("eligible_count", 0),
            "recommended_count": d.get("recommended_count", 0),
            "loan_amount":    (d.get("applicant_summary") or {}).get("loan_amount"),
            "loan_category":  (d.get("applicant_summary") or {}).get("loan_category"),
        })
    return results


@router.get("/latest/{application_id}")
def latest_assessment(application_id: str, user: dict = Depends(get_current_user)):
    """Return the latest saved assessment for an application."""
    try:
        doc = collections["financial_analysis_reports"].find_one(
            {
                "user_id": user["_id"],
                "application_id": ObjectId(application_id),
                "_saved_type": "full_assessment",
            },
            sort=[("generated_at", -1)],
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    if not doc:
        raise HTTPException(status_code=404, detail="No assessment found. Run assessment first.")
    return _serialize_assessment(doc)


@router.get("/{assessment_id}")
def get_assessment(assessment_id: str, user: dict = Depends(get_current_user)):
    """Return a specific saved assessment by its MongoDB _id."""
    try:
        doc = collections["financial_analysis_reports"].find_one(
            {"_id": ObjectId(assessment_id), "user_id": user["_id"]}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    if not doc:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return _serialize_assessment(doc)
