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
    description="Intelligent Indian Loan Eligibility and Recommendation System.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        print("[LoanWise AI] Connected to " + _conn_label + " | database: " + DATABASE_NAME)
        _sync_metrics()
        _seed_if_empty()
    else:
        print("[LoanWise AI] WARNING: " + _conn_label + " not reachable.")


def _sync_metrics():
    import json
    from pathlib import Path
    from datetime import datetime, timezone
    from database.mongodb import collections as cols
    reports_dir = Path(__file__).parent / "data" / "reports"
    synced = 0
    for jf in reports_dir.glob("metrics_*.json"):
        try:
            doc = json.load(open(jf))
            if "key" in doc and "model_name" in doc:
                doc.pop("updated_at", None)
                doc["updated_at"] = datetime.now(timezone.utc)
                cols["system_metadata"].replace_one({"key": doc["key"]}, doc, upsert=True)
                synced += 1
        except Exception:
            pass
    if synced:
        print("[LoanWise AI] Synced " + str(synced) + " model metric(s) to MongoDB.")


def _seed_if_empty():
    try:
        from database.mongodb import collections as cols
        if cols["lenders"].count_documents({}) >= 12:
            return
        print("[LoanWise AI] Database empty - seeding...")
        import subprocess
        r = subprocess.run([sys.executable, "seed/run_all_seeds.py"],
                          capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            print("[LoanWise AI] Seeding complete.")
        else:
            print("[LoanWise AI] Seed output: " + r.stderr[-300:])
    except Exception as e:
        print("[LoanWise AI] Seed skipped: " + str(e))


@app.get("/api/health")
def health_check():
    from database.mongodb import IS_ATLAS
    connected = check_connection()
    return {
        "status": "ok" if connected else "degraded",
        "database": DATABASE_NAME,
        "connection_type": "atlas" if IS_ATLAS else "local",
        "mongodb": "connected" if connected else "disconnected",
    }


from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Locate frontend folder
_BASE_DIR = Path(__file__).resolve().parent
_FRONTEND_CANDIDATES = [
    _BASE_DIR / "frontend",
    _BASE_DIR.parent / "frontend",
]
FRONTEND_DIR = next((d for d in _FRONTEND_CANDIDATES if d.exists() and (d / "index.html").exists()), None)

if FRONTEND_DIR:
    css_path = FRONTEND_DIR / "css"
    js_path = FRONTEND_DIR / "js"
    if css_path.exists():
        app.mount("/css", StaticFiles(directory=str(css_path)), name="css")
    if js_path.exists():
        app.mount("/js", StaticFiles(directory=str(js_path)), name="js")


@app.get("/api")
def api_root():
    return {
        "application": "LoanWise AI",
        "version": "2.0.0",
        "description": "Intelligent Indian Loan Eligibility and Recommendation System",
        "docs": "/docs",
    }


@app.get("/", include_in_schema=False)
def root():
    if FRONTEND_DIR and (FRONTEND_DIR / "index.html").exists():
        return FileResponse(FRONTEND_DIR / "index.html")
    return api_root()


@app.get("/{path_name:path}", include_in_schema=False)
def serve_frontend_pages(path_name: str):
    if not FRONTEND_DIR:
        return JSONResponse({"detail": "Not found"}, status_code=404)
    # Never intercept api or swagger docs
    if path_name.startswith("api") or path_name in ("docs", "redoc", "openapi.json"):
        return JSONResponse({"detail": "Not found"}, status_code=404)

    target = FRONTEND_DIR / path_name
    if target.is_file():
        return FileResponse(target)

    html_target = FRONTEND_DIR / f"{path_name}.html"
    if html_target.is_file():
        return FileResponse(html_target)

    return FileResponse(FRONTEND_DIR / "index.html")
