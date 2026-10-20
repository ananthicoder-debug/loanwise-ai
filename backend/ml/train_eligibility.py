"""
ml/train_eligibility.py
------------------------
Trains Model 1 using data/raw/eligibility_dataset.csv (5000 records).
Target: loan_status (0=Not Eligible, 1=Eligible).
Saves model + saves real metrics to MongoDB system_metadata.
"""
import os, sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent))

from preprocessing import ELIGIBILITY_FEATURES, EDUCATION_MAP, EMPLOYMENT_MAP

# ─── Paths ────────────────────────────────────────────────────────────────────
DATA_PATH  = BASE_DIR.parent / "data" / "raw" / "eligibility_dataset.csv"
MODEL_OUT  = BASE_DIR / "models" / "eligibility_model.joblib"
SCALER_OUT = BASE_DIR / "models" / "eligibility_preprocessor.joblib"
PROCESSED  = BASE_DIR.parent / "data" / "processed"
PROCESSED.mkdir(exist_ok=True)
RANDOM_SEED = 42


def build_features(df: pd.DataFrame):
    df = df.copy()
    # Exact column names from eligibility_dataset.csv
    df["education_enc"]  = df["education"].map(EDUCATION_MAP).fillna(0)
    df["employment_enc"] = df["employment_type"].map(EMPLOYMENT_MAP).fillna(0)

    for col in ELIGIBILITY_FEATURES:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    X = df[ELIGIBILITY_FEATURES].values
    y = df["loan_status"].astype(int).values   # 0=Not Eligible, 1=Eligible
    return X, y


def train():
    print("\n" + "="*60)
    print("  MODEL 1 — Loan Eligibility Prediction")
    print(f"  Data: {DATA_PATH}")
    print("="*60)

    df = pd.read_csv(DATA_PATH)
    print(f"\nLoaded {len(df)} records from eligibility_dataset.csv")
    print(f"Target distribution:\n{df['loan_status'].value_counts().to_dict()}")
    print(f"Class balance: {df['loan_status'].mean()*100:.1f}% positive (Eligible)")

    X, y = build_features(df)
    print(f"\nFeatures ({len(ELIGIBILITY_FEATURES)}): {ELIGIBILITY_FEATURES}")
    print(f"Class distribution: Eligible={y.sum()} Not_Eligible={(y==0).sum()}")

    # Save processed file
    df_proc = df.copy()
    df_proc["education_enc"]  = df_proc["education"].map(EDUCATION_MAP).fillna(0)
    df_proc["employment_enc"] = df_proc["employment_type"].map(EMPLOYMENT_MAP).fillna(0)
    df_proc.to_csv(PROCESSED / "eligibility_processed.csv", index=False)
    print(f"Saved processed data to data/processed/eligibility_processed.csv")

    # Train/test split (80/20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    print(f"\nTrain={len(X_train)} records | Test={len(X_test)} records")

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    # Compare models
    candidates = {
        "RandomForest":      (RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=3, random_state=RANDOM_SEED, n_jobs=-1), False),
        "GradientBoosting":  (GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=RANDOM_SEED), False),
        "LogisticRegression":(LogisticRegression(max_iter=1000, random_state=RANDOM_SEED, C=1.0), True),
    }

    print("\nModel comparison:")
    best_model, best_f1, best_name, best_uses_scaler = None, -1, "", False
    for name, (model, use_sc) in candidates.items():
        X_fit  = X_train_sc if use_sc else X_train
        X_eval = X_test_sc  if use_sc else X_test
        model.fit(X_fit, y_train)
        preds = model.predict(X_eval)
        f1 = f1_score(y_test, preds, zero_division=0)
        acc = accuracy_score(y_test, preds)
        print(f"  {name:<22} F1={f1:.4f}  Acc={acc:.4f}")
        if f1 > best_f1:
            best_f1, best_model, best_name, best_uses_scaler = f1, model, name, use_sc

    # Final evaluation on test set
    X_eval_f = X_test_sc if best_uses_scaler else X_test
    preds_f  = best_model.predict(X_eval_f)
    proba_f  = best_model.predict_proba(X_eval_f)[:, 1]

    acc  = accuracy_score(y_test, preds_f)
    prec = precision_score(y_test, preds_f, zero_division=0)
    rec  = recall_score(y_test, preds_f, zero_division=0)
    f1   = f1_score(y_test, preds_f, zero_division=0)
    roc  = roc_auc_score(y_test, proba_f)
    cm   = confusion_matrix(y_test, preds_f).tolist()

    print(f"\n{'='*60}")
    print(f"  BEST MODEL: {best_name}")
    print(f"  Accuracy:  {acc:.4f}  ({acc*100:.1f}%)")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {roc:.4f}")
    print(f"  Confusion Matrix:\n    TN={cm[0][0]}  FP={cm[0][1]}\n    FN={cm[1][0]}  TP={cm[1][1]}")
    print(classification_report(y_test, preds_f, target_names=["Not Eligible","Eligible"]))

    # Feature importance
    if hasattr(best_model, "feature_importances_"):
        fi = dict(zip(ELIGIBILITY_FEATURES, best_model.feature_importances_))
        fi_sorted = sorted(fi.items(), key=lambda x: -x[1])
        print("  Feature Importance:")
        for feat, imp in fi_sorted:
            print(f"    {feat:<30} {imp:.4f}")

    # Save model
    MODEL_OUT.parent.mkdir(exist_ok=True)
    bundle = {
        "model":         best_model,
        "features":      ELIGIBILITY_FEATURES,
        "uses_scaler":   best_uses_scaler,
        "algorithm":     best_name,
        "model_version": "2.0",
        "feature_importance": getattr(best_model, "feature_importances_", None),
    }
    joblib.dump(bundle, MODEL_OUT)
    joblib.dump(scaler, SCALER_OUT)
    print(f"\nSaved: {MODEL_OUT}")

    # Save metrics to MongoDB
    try:
        from model_utils import save_model_metadata
        class_dist = df["loan_status"].value_counts().to_dict()
        save_model_metadata(
            model_name       = "Loan Eligibility Prediction Model",
            algorithm        = best_name,
            features         = ELIGIBILITY_FEATURES,
            training_records = len(X_train),
            testing_records  = len(X_test),
            dataset_name     = "eligibility_dataset.csv (5000 records)",
            accuracy         = acc,
            precision        = prec,
            recall           = rec,
            f1_score         = f1,
            roc_auc          = roc,
            confusion_matrix = cm,
            model_version    = "2.0",
            model_file       = str(MODEL_OUT),
        )
        print("Metrics saved to MongoDB system_metadata.")
    except Exception as e:
        print(f"Warning — could not save to MongoDB: {e}")

    # Save dataset analysis JSON
    import json
    from datetime import datetime
    analysis = {
        "dataset": "eligibility_dataset.csv",
        "source": "data/raw/eligibility_dataset.csv",
        "total_records": len(df),
        "training_records": len(X_train),
        "testing_records": len(X_test),
        "target_column": "loan_status",
        "class_distribution": {"eligible": int(y.sum()), "not_eligible": int((y==0).sum())},
        "class_balance_pct": {"eligible": round(float(y.mean())*100, 1), "not_eligible": round((1-float(y.mean()))*100,1)},
        "features_used": ELIGIBILITY_FEATURES,
        "feature_count": len(ELIGIBILITY_FEATURES),
        "numerical_stats": {
            col: {"min": float(df[col].min()), "max": float(df[col].max()), "mean": round(float(df[col].mean()), 2)}
            for col in ["age", "annual_income", "cibil_score", "loan_amount", "loan_tenure", "outstanding_debt"]
        },
        "categorical_distributions": {
            "education": df["education"].value_counts().to_dict(),
            "employment_type": df["employment_type"].value_counts().to_dict(),
        },
        "missing_values": int(df.isnull().sum().sum()),
        "model_performance": {
            "algorithm": best_name,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc, 4),
            "confusion_matrix": cm,
        },
        "feature_importance": {k: round(float(v), 6) for k, v in (fi_sorted[:10] if 'fi_sorted' in dir() else [])},
        "disclaimer": "Trained on borrower profile data. AI output is an estimate — not a lender decision.",
        "generated_at": datetime.now().isoformat(),
    }
    reports_dir = BASE_DIR.parent / "data" / "reports"
    reports_dir.mkdir(exist_ok=True)
    with open(reports_dir / "eligibility_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"Analysis saved to data/reports/eligibility_analysis.json")

    # Also save to MongoDB
    try:
        sys.path.insert(0, str(BASE_DIR.parent))
        from database.mongodb import collections
        from datetime import timezone
        collections["system_metadata"].replace_one(
            {"key": "dataset_analysis_eligibility"},
            {"key": "dataset_analysis_eligibility", **analysis},
            upsert=True
        )
    except Exception:
        pass

    print("="*60)
    print("  Model 1 training complete.")
    print("="*60)
    return acc, f1, roc


if __name__ == "__main__":
    train()
