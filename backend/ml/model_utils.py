"""
ml/model_utils.py
------------------
Saves and retrieves ML model performance metadata to/from MongoDB.
Used by train_eligibility.py and train_affordability.py after training
so the Admin Model Performance page can display real metrics.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from database.mongodb import collections


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
    """Upsert model performance record into system_metadata collection."""
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
        "updated_at": datetime.now(timezone.utc),
        "data_type": "ML_Training_Data",
        "disclaimer": (
            "Metrics calculated on held-out test data. "
            "AI model outputs are estimates — not guaranteed lender approvals."
        ),
    }
    collections["system_metadata"].replace_one(
        {"key": doc["key"]}, doc, upsert=True
    )
    print(f"[model_utils] Saved performance for '{model_name}' -> system_metadata")


def get_all_model_metadata() -> list:
    """Retrieve all model performance records."""
    records = list(collections["system_metadata"].find(
        {"key": {"$regex": "^model_performance_"}}
    ))
    for r in records:
        r["_id"] = str(r["_id"])
    return records
