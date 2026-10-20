"""
main.py
--------
LoanWise AI — FastAPI Application Entry Point.
Run: uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "ml"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.mongodb import check_connection, create_indexes, DATABASE_NAME
from routes import (
    auth, users, applications, loans, predictions,
    recommendations, active_loans, payments, admin, dashboard,
    notifications, documents, feedback, credit, datasets, reports
)
from routes import assessment

app = FastAPI(
    title="LoanWise AI",
    description="Intelligent Indian Loan Eligibility, Recommendation and Repayment Management System.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Allow all — required for Netlify + Render free tier
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(credit.router)
app.include_router(applications.router)
app.include_router(loans.router)
app.include_router(predictions.router)
app.include_router(recommendations.router)
app.include_router(active_loans.router)
app.include_router(payments.router)
app.include_router(notifications.router)
app.include_router(documents.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(dashboard.router)
app.include_router(datasets.router)
app.include_router(reports.router)
app.include_router(assessment.router)


@app.on_event("startup")
def on_startup():
    from database.mongodb import _conn_label
    if check_connection():
        create_indexes()
        print(f"[LoanWise AI] Connected to {_conn_label} — database: {DATABASE_NAME}")
        # Sync any model metrics that were saved to JSON during build phase
        # (Atlas is unreachable during Render build, so metrics are saved to files first)
        _sync_model_metrics_to_db()
    else:
        print(f"[LoanWise AI] WARNING: {_conn_label} not reachable. Check your connection and restart.")


def _sync_model_metrics_to_db():
    """
    At app startup (not build), push any JSON-saved model metrics to MongoDB.
    This handles the case where Atlas was unreachable during Render build phase.
    """
    import json
    from pathlib import Path
    from database.mongodb import collections

    reports_dir = Path(__file__).parent / "data" / "reports"
    synced = 0
    for json_file in reports_dir.glob("metrics_*.json"):
        try:
            with open(json_file) as f:
                doc = json.load(f)
            if "key" in doc and "model_name" in doc:
                # Remove non-serialisable fields then upsert
                doc.pop("updated_at", None)
                from datetime import datetime, timezone
                doc["updated_at"] = datetime.now(timezone.utc)
                collections["system_metadata"].replace_one(
                    {"key": doc["key"]}, doc, upsert=True
                )
                synced += 1
        except Exception:
            pass
    if synced:
        print(f"[LoanWise AI] Synced {synced} model metric record(s) from JSON to MongoDB.")


@app.get("/api/health")
def health_check():
    from database.mongodb import _conn_label, IS_ATLAS
    connected = check_connection()
    return {
        "status": "ok" if connected else "degraded",
        "database": DATABASE_NAME,
        "connection_type": "atlas" if IS_ATLAS else "local",
        "mongodb": "connected" if connected else "disconnected",
    }


@app.get("/")
def root():
    return {
        "application": "LoanWise AI",
        "version": "2.0.0",
        "description": "Intelligent Indian Loan Eligibility, Recommendation and Repayment Management System",
        "docs": "/docs",
    }
