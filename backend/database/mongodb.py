"""
database/mongodb.py
--------------------
Purpose:
    Shared MongoDB connection for LoanWise AI — all routes/services import
    `collections` and `db` from here. One client per process, never per request.

    Supports both:
      - MongoDB Atlas (production):  mongodb+srv://...
      - Local MongoDB (development): mongodb://localhost:27017

Database: loan_ai_system
"""

import os
import ssl
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING

load_dotenv()

MONGODB_URI   = os.getenv("MONGODB_URI",   "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "loan_ai_system")

# Detect connection type for logging
IS_ATLAS    = "mongodb+srv" in MONGODB_URI
_conn_label = "MongoDB Atlas" if IS_ATLAS else "Local MongoDB"

# Atlas connections need a longer timeout; local can stay short
_timeout_ms = 20000 if IS_ATLAS else 5000

# Build client kwargs — add TLS settings for Atlas to avoid SSL handshake issues
# on certain Linux environments (e.g. Render free tier)
_client_kwargs: dict = {"serverSelectionTimeoutMS": _timeout_ms}

if IS_ATLAS:
    _client_kwargs.update({
        "tls":                         True,
        "tlsAllowInvalidCertificates": True,   # Required for Render free tier OpenSSL
        "tlsAllowInvalidHostnames":    False,
        "retryWrites":                 True,
        "w":                           "majority",
    })

client = MongoClient(MONGODB_URI, **_client_kwargs)
db     = client[DATABASE_NAME]

collections = {
    "users":                    db["users"],
    "credit_profiles":          db["credit_profiles"],
    "lenders":                  db["lenders"],
    "loan_products":            db["loan_products"],
    "loan_applications":        db["loan_applications"],
    "eligibility_predictions":  db["eligibility_predictions"],
    "affordability_predictions":db["affordability_predictions"],
    "predictions":              db["predictions"],
    "recommendations":          db["recommendations"],
    "active_loans":             db["active_loans"],
    "payment_schedules":        db["payment_schedules"],
    "payments":                 db["payments"],
    "historical_loans":         db["historical_loans"],
    "installment_payments":     db["installment_payments"],
    "notifications":            db["notifications"],
    "documents":                db["documents"],
    "feedback":                 db["feedback"],
    "admin_logs":               db["admin_logs"],
    "system_metadata":          db["system_metadata"],
    "financial_analysis_reports": db["financial_analysis_reports"],
}


def check_connection() -> bool:
    """Ping MongoDB. Returns True if connected, False otherwise."""
    try:
        client.admin.command("ping")
        return True
    except Exception as exc:
        print(f"[{_conn_label}] Connection failed: {exc}")
        return False


def create_indexes():
    """
    Create indexes for performance and uniqueness enforcement.
    Called once at startup from main.py.
    """
    collections["users"].create_index("email", unique=True)
    collections["credit_profiles"].create_index("user_id", unique=True)
    collections["loan_products"].create_index("lender_id")
    collections["loan_products"].create_index("loan_category")
    collections["loan_products"].create_index("product_code", unique=True, sparse=True)
    collections["loan_applications"].create_index("user_id")
    collections["loan_applications"].create_index([("application_date", DESCENDING)])
    collections["predictions"].create_index("application_id")
    collections["eligibility_predictions"].create_index("application_id")
    collections["affordability_predictions"].create_index("application_id")
    collections["recommendations"].create_index("application_id")
    collections["active_loans"].create_index("user_id")
    collections["active_loans"].create_index([("created_at", DESCENDING)])
    collections["payments"].create_index("active_loan_id")
    collections["payment_schedules"].create_index("active_loan_id")
    collections["historical_loans"].create_index("applicant_id")
    collections["installment_payments"].create_index("historical_loan_id")
    collections["notifications"].create_index("user_id")
    collections["notifications"].create_index([("created_at", DESCENDING)])
    collections["documents"].create_index("user_id")
    collections["feedback"].create_index("user_id")
    collections["admin_logs"].create_index([("created_at", DESCENDING)])
    collections["financial_analysis_reports"].create_index("user_id")
    collections["financial_analysis_reports"].create_index("application_id")
    print("[MongoDB] All indexes ensured.")
