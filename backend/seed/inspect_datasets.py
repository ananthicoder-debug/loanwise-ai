# -*- coding: utf-8 -*-
"""
Dataset Schema Inspector
Inspects all 7 CSV files in the raw data directory and produces a full schema report.
"""

import pandas as pd
import numpy as np
import os
import sys

# Force UTF-8 output on Windows so unicode chars don't crash
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = r"C:\Users\Admin\Downloads\LoanAssist-AI\LoanAssist-AI\backend\data\raw"

FILES = [
    "affordability_dataset.csv",
    "borrowers.csv",
    "eligibility_dataset.csv",
    "historical_loans.csv",
    "installment_payments.csv",
    "lenders.csv",
    "loan_products.csv",
]

SEPARATOR = "=" * 80


def infer_target_column(df, filename):
    """Heuristically identify likely target/label columns."""
    candidates = []
    target_keywords = [
        "label", "target", "approved", "approval", "default", "status",
        "outcome", "result", "eligible", "eligibility", "affordable",
        "affordability", "risk", "class", "fraud", "churn"
    ]
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in target_keywords):
            candidates.append(col)
    return candidates


def analyze_file(filepath, filename):
    print(SEPARATOR)
    print(f"FILE: {filename}")
    print(SEPARATOR)

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"  ERROR reading file: {e}")
        return

    # ?? 1. Record count ??????????????????????????????????????????????????????
    print(f"\n1. RECORD COUNT (rows excl. header): {len(df)}")

    # ?? 2. Column names ??????????????????????????????????????????????????????
    print(f"\n2. COLUMN NAMES ({len(df.columns)} columns):")
    for i, col in enumerate(df.columns, 1):
        print(f"   {i:>3}. {col}")

    # ?? 3. Data types ?????????????????????????????????????????????????????????
    print("\n3. DATA TYPES:")
    for col in df.columns:
        print(f"   {col:<45} {str(df[col].dtype)}")

    # ?? 4. Sample values (first 2 rows) ??????????????????????????????????????
    print("\n4. SAMPLE VALUES (first 2 rows):")
    sample = df.head(2)
    for _, row in sample.iterrows():
        print("   ---")
        for col in df.columns:
            print(f"   {col:<45} {repr(row[col])}")

    # ?? 5. Missing value counts ???????????????????????????????????????????????
    print("\n5. MISSING VALUE COUNTS:")
    missing = df.isnull().sum()
    has_missing = False
    for col in df.columns:
        count = missing[col]
        pct = (count / len(df) * 100) if len(df) > 0 else 0
        flag = " *** " if count > 0 else ""
        print(f"   {col:<45} {count:>6}  ({pct:.1f}%){flag}")
        if count > 0:
            has_missing = True
    if not has_missing:
        print("   (no missing values)")

    # ?? 6. Numeric column stats ???????????????????????????????????????????????
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        print("\n6. NUMERIC COLUMN STATS (min / max / mean):")
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) == 0:
                print(f"   {col:<45} all NaN")
                continue
            mn  = series.min()
            mx  = series.max()
            avg = series.mean()
            print(f"   {col:<45} min={mn:.4g}  max={mx:.4g}  mean={avg:.4g}")
    else:
        print("\n6. NUMERIC COLUMN STATS: (none)")

    # ?? 7. Categorical column unique values ???????????????????????????????????
    categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    # Also treat low-cardinality integer columns as categorical
    for col in numeric_cols:
        if df[col].nunique() <= 20:
            if col not in categorical_cols:
                categorical_cols.append(col)

    if categorical_cols:
        print("\n7. CATEGORICAL COLUMN UNIQUE VALUES (<=20 unique shown):")
        for col in categorical_cols:
            n_unique = df[col].nunique()
            print(f"\n   [{col}]  - {n_unique} unique value(s)")
            if n_unique <= 20:
                counts = df[col].value_counts(dropna=False)
                for val, cnt in counts.items():
                    pct = cnt / len(df) * 100
                    print(f"      {repr(val):<40} {cnt:>6} ({pct:.1f}%)")
            else:
                print(f"      (>20 unique values - skipping detail)")
    else:
        print("\n7. CATEGORICAL COLUMN UNIQUE VALUES: (none)")

    # ?? 8. Likely target / label columns ?????????????????????????????????????
    targets = infer_target_column(df, filename)
    print("\n8. LIKELY TARGET / LABEL COLUMNS:")
    if targets:
        for t in targets:
            print(f"   {t}")
    else:
        print("   (none detected by keyword heuristic)")

    print()


def main():
    print("\n" + SEPARATOR)
    print("  LOANASSIST-AI -- FULL DATASET SCHEMA REPORT")
    print(SEPARATOR + "\n")

    for filename in FILES:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(SEPARATOR)
            print(f"FILE: {filename}")
            print("  *** FILE NOT FOUND ***")
            print()
            continue
        analyze_file(filepath, filename)

    print(SEPARATOR)
    print("  END OF REPORT")
    print(SEPARATOR + "\n")


if __name__ == "__main__":
    main()
