"""
ml/predict_affordability.py
------------------------------
Loads Model 2 artifacts once at import time.
Falls back to rule-based scoring if .joblib files are missing.
"""

import os
import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "models" / "affordability_model.joblib"
SCALER_PATH = BASE_DIR / "models" / "affordability_preprocessor.joblib"

import sys
sys.path.append(str(BASE_DIR))
from preprocessing import build_affordability_vector, AFFORDABILITY_FEATURES

_bundle = None
_scaler = None

try:
    if MODEL_PATH.exists() and SCALER_PATH.exists():
        _bundle = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
        if len(_bundle.get("features", [])) != len(AFFORDABILITY_FEATURES):
            print("[Model 2] Feature count mismatch  -  retrain recommended. Using rule-based fallback.")
            _bundle = None
except Exception as e:
    print(f"[Model 2] Failed to load: {e}. Using rule-based fallback.")
    _bundle = None


def _rule_based_fallback(credit_profile: dict, proposed_emi: float) -> tuple[str, float]:
    """Transparent rule-based fallback."""
    monthly_income = credit_profile.get("monthly_income", 1) or 1
    existing_emi = (
        credit_profile.get("existing_emi")
        or credit_profile.get("current_emi")
        or 0
    )
    missed = credit_profile.get("missed_payments", 0)
    total_emi_ratio = (existing_emi + proposed_emi) / monthly_income

    score = 0.9 - (total_emi_ratio * 1.5) - (0.05 * min(missed, 6))
    prob = max(0.01, min(0.99, score))
    return ("Manageable" if prob >= 0.5 else "Not Manageable"), round(prob, 4)


def predict_affordability(credit_profile: dict, application: dict, proposed_emi: float) -> tuple[str, float]:
    """Returns (result, probability). result is 'Manageable' or 'Not Manageable'."""
    if _bundle is None:
        return _rule_based_fallback(credit_profile, proposed_emi)

    vector = [build_affordability_vector(credit_profile, application, proposed_emi)]
    model = _bundle["model"]
    features = _bundle.get("features", AFFORDABILITY_FEATURES)

    try:
        features_df = pd.DataFrame(vector, columns=features)
        X = _scaler.transform(features_df.values) if _bundle.get("uses_scaler") else features_df.values
        proba = model.predict_proba(X)[0][1]
        result = "Manageable" if proba >= 0.5 else "Not Manageable"
        return result, round(float(proba), 4)
    except Exception as e:
        print(f"[Model 2] Prediction error: {e}. Falling back to rules.")
        return _rule_based_fallback(credit_profile, proposed_emi)
