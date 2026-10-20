"""
routes/reports.py
------------------
POST /api/reports/generate/{application_id}  -> generate + save personalized report
GET  /api/reports                             -> list user's reports
GET  /api/reports/{report_id}                 -> get one full report
GET  /api/reports/latest/{application_id}     -> get latest report for an application
GET  /api/admin/dataset-analysis              -> dataset analysis for admin
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from database.mongodb import collections
from utils.deps import get_current_user, get_current_admin
from services.report_service import generate_report, get_user_reports

router = APIRouter(tags=["reports"])


@router.post("/api/reports/generate/{application_id}")
def generate_user_report(application_id: str, user: dict = Depends(get_current_user)):
    """Generate (or regenerate) a personalized financial analysis report."""
    try:
        report = generate_report(str(user["_id"]), application_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    return report


@router.get("/api/reports")
def list_my_reports(user: dict = Depends(get_current_user)):
    """Return all saved reports for the logged-in user."""
    return get_user_reports(str(user["_id"]))


@router.get("/api/reports/latest/{application_id}")
def get_latest_report(application_id: str, user: dict = Depends(get_current_user)):
    """Return the latest report for a specific application."""
    try:
        report = collections["financial_analysis_reports"].find_one(
            {"user_id": user["_id"], "application_id": ObjectId(application_id)},
            sort=[("generated_at", -1)]
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Report not found.")
    if not report:
        raise HTTPException(status_code=404, detail="No report found. Generate one first.")
    report["_id"]            = str(report["_id"])
    report["user_id"]        = str(report["user_id"])
    report["application_id"] = str(report["application_id"])
    if report.get("prediction_id"):
        report["prediction_id"] = str(report["prediction_id"])
    return report


@router.get("/api/reports/{report_id}")
def get_report(report_id: str, user: dict = Depends(get_current_user)):
    """Return a specific report by ID."""
    try:
        report = collections["financial_analysis_reports"].find_one(
            {"_id": ObjectId(report_id), "user_id": user["_id"]}
        )
    except InvalidId:
        raise HTTPException(status_code=404, detail="Report not found.")
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    report["_id"]            = str(report["_id"])
    report["user_id"]        = str(report["user_id"])
    report["application_id"] = str(report["application_id"])
    return report


@router.get("/api/admin/dataset-analysis")
def get_dataset_analysis(admin: dict = Depends(get_current_admin)):
    """Return the full dataset analysis saved by analyse_datasets.py."""
    record = collections["system_metadata"].find_one({"key": "full_dataset_analysis"})
    if not record:
        raise HTTPException(status_code=404, detail="Dataset analysis not yet generated. Run: python ml/analyse_datasets.py")
    record["_id"] = str(record["_id"])
    return record


@router.get("/api/admin/data-quality-full")
def get_data_quality_full(admin: dict = Depends(get_current_admin)):
    """Return the data quality report saved by analyse_datasets.py."""
    record = collections["system_metadata"].find_one({"key": "data_quality_report"})
    if not record:
        raise HTTPException(status_code=404, detail="Data quality report not yet generated.")
    record["_id"] = str(record["_id"])
    return record


@router.get("/api/admin/model-analysis")
def get_model_analysis(admin: dict = Depends(get_current_admin)):
    """Return both eligibility and affordability dataset analyses."""
    elig = collections["system_metadata"].find_one({"key": "dataset_analysis_eligibility"})
    aff  = collections["system_metadata"].find_one({"key": "dataset_analysis_affordability"})
    result = {}
    if elig:
        elig["_id"] = str(elig["_id"])
        result["eligibility"] = elig
    if aff:
        aff["_id"] = str(aff["_id"])
        result["affordability"] = aff
    if not result:
        raise HTTPException(status_code=404, detail="Model analysis not found. Run training scripts first.")
    return result
