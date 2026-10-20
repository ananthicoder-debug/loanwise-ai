"""
ml/model_utils.py
------------------
Saves and retrieves ML model performance metadata to/from MongoDB.
Used by train_eligibility.py and train_affordability.py after training
so the Admin Model Performance page can display real metrics.

NOTE: During Render build phase, Atlas may reject connections due to
TLS/IP restrictions. All saves are wrapped in try/except so a failed
MongoDB save never fails the overall build — metrics are always saved
to JSON files as a fallback.
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))


def save_model_metadata(
    model_name: str,
    algorithm: str,
    features: list,
    training_records: int,
    testing_records: int,
    dataset_name: str,
    accuracy: float,
    precision: float,
    recall: float,
    f1_score: float,
    roc_auc: float,
    confusion_matrix: list,
    model_version: str = "2.0",
    model_file: str = "",
):
    """
    Upsert model performance record into system_metadata collection.
    Falls back gracefully if Atlas is unreachable (e.g. during build phase).
    """
    doc = {
        "key": f"model_performance_{model_name.lower().replace(' ', '_')}",
        "model_name": model_name,
        "algorithm": algorithm,
        "features": features,
        "training_records": training_records,
        "testing_records": testing_records,
        "dataset_name": dataset_name,
        "metrics": {
            "accuracy":         round(float(accuracy), 4),
            "precision":        round(float(precision), 4),
            "recall":           round(float(recall), 4),
            "f1_score":         round(float(f1_score), 4),
            "roc_auc":          round(float(roc_auc), 4),
            "confusion_matrix": confusion_matrix,
        },
        "model_version": model_version,
        "model_file": model_file,
        "training_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "data_type": "ML_Training_Data",
        "disclaimer": (
            "Metrics calculated on held-out test data. "
            "AI model outputs are estimates — not guaranteed lender approvals."
        ),
    }

    # Always save to JSON as primary backup (works even without MongoDB)
    _save_to_json(model_name, doc)

    # Try MongoDB — gracefully skip if unreachable (build phase TLS issue)
    try:
        from database.mongodb import collections
        doc_to_save = {**doc, "updated_at": datetime.now(timezone.utc)}
        collections["system_metadata"].replace_one(
            {"key": doc["key"]}, doc_to_save, upsert=True
        )
        print(f"[model_utils] Saved performance for '{model_name}' -> system_metadata")
    except Exception as e:
        err_short = str(e)[:120].replace("\n", " ")
        print(f"[model_utils] MongoDB save skipped (will retry at app startup): {err_short}")
        print(f"[model_utils] Metrics saved to JSON fallback instead.")


def _save_to_json(model_name: str, doc: dict):
    """Save metrics to a JSON file as a fallback when MongoDB is unreachable."""
    try:
        reports_dir = Path(__file__).parent.parent / "data" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        safe_name  = model_name.lower().replace(" ", "_").replace("/", "_")
        json_path  = reports_dir / f"metrics_{safe_name}.json"
        save_doc   = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in doc.items()}
        with open(json_path, "w") as f:
            json.dump(save_doc, f, indent=2, default=str)
    except Exception:
        pass  # JSON save is best-effort


def get_all_model_metadata() -> list:
    """Retrieve all model performance records from MongoDB."""
    try:
        from database.mongodb import collections
        records = list(collections["system_metadata"].find(
            {"key": {"$regex": "^model_performance_"}}
        ))
        for r in records:
            r["_id"] = str(r["_id"])
        return records
    except Exception as e:
        print(f"[model_utils] Could not retrieve from MongoDB: {e}")
        return _load_from_json_fallback()


def _load_from_json_fallback() -> list:
    """Load metrics from JSON files when MongoDB is unavailable."""
    records = []
    try:
        reports_dir = Path(__file__).parent.parent / "data" / "reports"
        for json_file in reports_dir.glob("metrics_*.json"):
            with open(json_file) as f:
                records.append(json.load(f))
    except Exception:
        pass
    return records
