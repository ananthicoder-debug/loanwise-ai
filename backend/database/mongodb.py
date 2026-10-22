import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING

load_dotenv()

MONGODB_URI   = os.getenv("MONGODB_URI",   "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "loan_ai_system")

IS_ATLAS    = "mongodb+srv" in MONGODB_URI
_conn_label = "MongoDB Atlas" if IS_ATLAS else "Local MongoDB"

# Client is created lazily - not at import time
_client = None
_db     = None


def _get_client():
    global _client, _db, IS_ATLAS, _conn_label
    if _client is not None:
        try:
            _client.admin.command("ping")
            return _client, _db
        except Exception:
            _client = None

    if _client is None:
        kwargs = {"serverSelectionTimeoutMS": 4000}
        if "mongodb+srv" in MONGODB_URI:
            kwargs.update({
                "tls": True,
                "tlsAllowInvalidCertificates": True,
                "retryWrites": True,
                "w": "majority",
            })
        try:
            c = MongoClient(MONGODB_URI, **kwargs)
            c.admin.command("ping")
            _client = c
            _db = _client[DATABASE_NAME]
            IS_ATLAS = "mongodb+srv" in MONGODB_URI
            _conn_label = "MongoDB Atlas" if IS_ATLAS else "Local MongoDB"
            return _client, _db
        except Exception as exc:
            # If primary connection failed (e.g. Atlas IP blocked), check local MongoDB Compass
            try:
                local_uri = "mongodb://127.0.0.1:27017"
                c_local = MongoClient(local_uri, serverSelectionTimeoutMS=2000)
                c_local.admin.command("ping")
                _client = c_local
                _db = _client[DATABASE_NAME]
                IS_ATLAS = False
                _conn_label = "Local MongoDB (Compass)"
                print("[LoanWise AI] Connected to local MongoDB Compass.")
                return _client, _db
            except Exception:
                pass
            _client = MongoClient(MONGODB_URI, **kwargs)
            _db = _client[DATABASE_NAME]
    return _client, _db


class _LazyCollections:
    """Access collections lazily - connection only made when first collection is accessed."""
    def __getitem__(self, name):
        _, db = _get_client()
        return db[name]


collections = _LazyCollections()


def check_connection():
    try:
        c, _ = _get_client()
        c.admin.command("ping")
        return True
    except Exception as exc:
        print(f"[{_conn_label}] Connection failed: {exc}")
        return False


def create_indexes():
    db = _get_client()[1]
    db["users"].create_index("email", unique=True)
    db["credit_profiles"].create_index("user_id", unique=True)
    db["loan_products"].create_index("lender_id")
    db["loan_products"].create_index("loan_category")
    db["loan_products"].create_index("product_code", unique=True, sparse=True)
    db["loan_applications"].create_index("user_id")
    db["loan_applications"].create_index([("application_date", DESCENDING)])
    db["predictions"].create_index("application_id")
    db["eligibility_predictions"].create_index("application_id")
    db["affordability_predictions"].create_index("application_id")
    db["recommendations"].create_index("application_id")
    db["active_loans"].create_index("user_id")
    db["active_loans"].create_index([("created_at", DESCENDING)])
    db["payments"].create_index("active_loan_id")
    db["payment_schedules"].create_index("active_loan_id")
    db["historical_loans"].create_index("applicant_id")
    db["installment_payments"].create_index("historical_loan_id")
    db["notifications"].create_index("user_id")
    db["notifications"].create_index([("created_at", DESCENDING)])
    db["documents"].create_index("user_id")
    db["feedback"].create_index("user_id")
    db["admin_logs"].create_index([("created_at", DESCENDING)])
    db["financial_analysis_reports"].create_index("user_id")
    db["financial_analysis_reports"].create_index("application_id")
    print("[MongoDB] All indexes ensured.")