"""
ml/train_affordability.py
--------------------------
Trains Model 2 using data/raw/affordability_dataset.csv (5000 records).
Target: manageable (0=Not Manageable, 1=Manageable).

NOTE: This script saves everything to .joblib and .json files ONLY.
      It never calls MongoDB  -  that avoids the SSL handshake error
      in Render's build container.
      FastAPI startup (main.py) syncs the JSON metrics to Atlas.
"""
import os, sys, json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)

BASE_DIR   = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent))

from preprocessing import AFFORDABILITY_FEATURES

DATA_PATH  = BASE_DIR.parent / "data" / "raw" / "affordability_dataset.csv"
MODEL_OUT  = BASE_DIR / "models" / "affordability_model.joblib"
SCALER_OUT = BASE_DIR / "models" / "affordability_preprocessor.joblib"
REPORTS    = BASE_DIR.parent / "data" / "reports"
PROCESSED  = BASE_DIR.parent / "data" / "processed"
RANDOM_SEED = 42


def build_features(df: pd.DataFrame):
    df = df.copy()
    for col in AFFORDABILITY_FEATURES:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    X = df[AFFORDABILITY_FEATURES].values
    y = df["manageable"].astype(int).values
    return X, y


def train():
    print("\n" + "="*60)
    print("  MODEL 2 -- Loan Affordability & Repayment Feasibility")
    print(f"  Data: {DATA_PATH}")
    print("="*60)

    df = pd.read_csv(DATA_PATH)
    print(f"\nLoaded {len(df)} records from affordability_dataset.csv")
    print(f"Target distribution:\n{df['manageable'].value_counts().to_dict()}")
    print(f"Class balance: {df['manageable'].mean()*100:.1f}% positive (Manageable)")
    print(f"\nNote: Dataset has {(df['manageable']==1).sum()} Manageable and {(df['manageable']==0).sum()} Not Manageable")
    print(f"Class imbalance noted -- using stratified split and class_weight=balanced where applicable.")

    X, y = build_features(df)
    print(f"\nFeatures ({len(AFFORDABILITY_FEATURES)}): {AFFORDABILITY_FEATURES}")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED / "affordability_processed.csv", index=False)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    print(f"\nTrain={len(X_train)} | Test={len(X_test)}")

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    candidates = {
        "RandomForest":       (RandomForestClassifier(n_estimators=200, max_depth=10, class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1), False),
        "GradientBoosting":   (GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=RANDOM_SEED), False),
        "LogisticRegression": (LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_SEED), True),
    }

    print("\nModel comparison:")
    best_model, best_f1, best_name, best_uses_scaler = None, -1, "", False
    for name, (model, use_sc) in candidates.items():
        model.fit(X_train_sc if use_sc else X_train, y_train)
        preds = model.predict(X_test_sc if use_sc else X_test)
        f1  = f1_score(y_test, preds, zero_division=0)
        acc = accuracy_score(y_test, preds)
        print(f"  {name:<22} F1={f1:.4f}  Acc={acc:.4f}")
        if f1 > best_f1:
            best_f1, best_model, best_name, best_uses_scaler = f1, model, name, use_sc

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
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {roc:.4f}")
    print(f"  Confusion:\n    TN={cm[0][0]}  FP={cm[0][1]}\n    FN={cm[1][0]}  TP={cm[1][1]}")
    print(classification_report(y_test, preds_f, target_names=["Not Manageable", "Manageable"]))

    fi_sorted = []
    if hasattr(best_model, "feature_importances_"):
        fi = dict(zip(AFFORDABILITY_FEATURES, best_model.feature_importances_))
        fi_sorted = sorted(fi.items(), key=lambda x: -x[1])
        print("  Feature Importance:")
        for feat, imp in fi_sorted:
            print(f"    {feat:<35} {imp:.4f}")

    # ?? Save model artifacts ??????????????????????????????????????????????????
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": best_model, "features": AFFORDABILITY_FEATURES,
        "uses_scaler": best_uses_scaler, "algorithm": best_name,
        "model_version": "2.0",
        "feature_importance": getattr(best_model, "feature_importances_", None),
    }
    joblib.dump(bundle, MODEL_OUT)
    joblib.dump(scaler, SCALER_OUT)
    print(f"\nSaved: {MODEL_OUT}")

    # ?? Save ALL metrics to JSON (no MongoDB call here) ???????????????????????
    REPORTS.mkdir(parents=True, exist_ok=True)

    analysis = {
        "dataset": "affordability_dataset.csv",
        "source": "data/raw/affordability_dataset.csv",
        "total_records": len(df),
        "training_records": len(X_train),
        "testing_records": len(X_test),
        "target_column": "manageable",
        "class_distribution": {"manageable": int(y.sum()), "not_manageable": int((y == 0).sum())},
        "class_balance_pct": {"manageable": round(float(y.mean()) * 100, 1), "not_manageable": round((1 - float(y.mean())) * 100, 1)},
        "class_imbalance_note": "Dataset is imbalanced (22.5% Manageable). class_weight=balanced used.",
        "features_used": AFFORDABILITY_FEATURES,
        "numerical_stats": {
            col: {"min": float(df[col].min()), "max": float(df[col].max()), "mean": round(float(df[col].mean()), 2)}
            for col in ["monthly_income", "current_emi", "outstanding_debt", "proposed_amount", "emi_income_ratio"]
        },
        "missing_values": int(df.isnull().sum().sum()),
        "model_performance": {
            "algorithm": best_name, "accuracy": round(acc, 4),
            "precision": round(prec, 4), "recall": round(rec, 4),
            "f1_score": round(f1, 4), "roc_auc": round(roc, 4),
            "confusion_matrix": cm,
        },
        "feature_importance": {k: round(float(v), 6) for k, v in fi_sorted[:10]},
        "disclaimer": "Trained on borrower financial profile data. AI output is an estimate  -  not a repayment guarantee.",
        "generated_at": datetime.now().isoformat(),
    }
    with open(REPORTS / "affordability_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"Analysis saved to data/reports/affordability_analysis.json")

    # model_performance record for admin dashboard (synced to Atlas at app startup)
    perf_doc = {
        "key": "model_performance_loan_affordability_and_repayment_feasibility_model",
        "model_name": "Loan Affordability and Repayment Feasibility Model",
        "algorithm": best_name,
        "features": AFFORDABILITY_FEATURES,
        "training_records": len(X_train),
        "testing_records": len(X_test),
        "dataset_name": "affordability_dataset.csv (5000 records)",
        "metrics": {
            "accuracy": round(acc, 4), "precision": round(prec, 4),
            "recall": round(rec, 4), "f1_score": round(f1, 4),
            "roc_auc": round(roc, 4), "confusion_matrix": cm,
        },
        "model_version": "2.0",
        "model_file": str(MODEL_OUT),
        "training_date": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        "data_type": "ML_Training_Data",
        "disclaimer": "Metrics calculated on held-out test data. AI model outputs are estimates.",
    }
    with open(REPORTS / "metrics_loan_affordability_and_repayment_feasibility_model.json", "w") as f:
        json.dump(perf_doc, f, indent=2)

    print("  Metrics saved to JSON. Will sync to MongoDB at app startup.")
    print("="*60)
    print("  Model 2 training complete.")
    print("="*60)
    return acc, f1, roc


if __name__ == "__main__":
    train()
