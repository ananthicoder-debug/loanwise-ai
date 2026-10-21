"""
ml/predict_eligibility.py
---------------------------
Loads Model 1 artifacts once at import time.
Falls back to a transparent rule-based score if .joblib files are missing.
"""

import os
import joblib
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "models" / "eligibility_model.joblib"
SCALER_PATH = BASE_DIR / "models" / "eligibility_preprocessor.joblib"

# Import preprocessing from same directory
import sys
sys.path.append(str(BASE_DIR))
from preprocessing import build_eligibility_vector, ELIGIBILITY_FEATURES

_bundle = None
_scaler = None

try:
    if MODEL_PATH.exists() and SCALER_PATH.exists():
        _bundle = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)
        # Check if the loaded model has the updated feature set
        if len(_bundle.get("features", [])) != len(ELIGIBILITY_FEATURES):
            print("[Model 1] Feature count mismatch  -  retrain recommended. Using rule-based fallback.")
            _bundle = None
except Exception as e:
    print(f"[Model 1] Failed to load: {e}. Using rule-based fallback.")
    _bundle = None


def _rule_based_fallback(credit_profile: dict, application: dict) -> tuple[str, float]:
    """Transparent rule-based fallback used when model is not trained."""
    score = 0.5
    cibil = credit_profile.get("cibil_score", 650)
    annual_income = credit_profile.get("annual_income", 0)
    loan_amount = application.get("loan_amount", 0)
    existing_loans = credit_profile.get("existing_loans", 0)
    missed = credit_profile.get("missed_payments", 0)

    score += 0.20 if cibil >= 750 else (0.10 if cibil >= 700 else (-0.20 if cibil < 600 else -0.05))
    score += 0.10 if annual_income >= loan_amount * 0.3 else -0.10
    score -= 0.05 * min(existing_loans, 4)
    score -= 0.05 * min(missed, 4)

    prob = max(0.01, min(0.99, score))
    return ("Eligible" if prob >= 0.5 else "Not Eligible"), round(prob, 4)


def predict_eligibility(credit_profile: dict, application: dict) -> tuple[str, float]:
    """Returns (result, probability). result is 'Eligible' or 'Not Eligible'."""
    if _bundle is None:
        return _rule_based_fallback(credit_profile, application)

    vector = [build_eligibility_vector(credit_profile, application)]
    model = _bundle["model"]
    features = _bundle.get("features", ELIGIBILITY_FEATURES)

    try:
        features_df = pd.DataFrame(vector, columns=features)
        X = _scaler.transform(features_df.values) if _bundle.get("uses_scaler") else features_df.values
        proba = model.predict_proba(X)[0][1]
        result = "Eligible" if proba >= 0.5 else "Not Eligible"
        return result, round(float(proba), 4)
    except Exception as e:
        print(f"[Model 1] Prediction error: {e}. Falling back to rules.")
        return _rule_based_fallback(credit_profile, application)
