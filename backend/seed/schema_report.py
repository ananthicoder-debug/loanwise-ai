"""Inspect all 7 CSV files and print exact schemas."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd
import numpy as np

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
FILES = [
    "eligibility_dataset.csv",
    "affordability_dataset.csv",
    "borrowers.csv",
    "historical_loans.csv",
    "installment_payments.csv",
    "lenders.csv",
    "loan_products.csv",
]

for fname in FILES:
    path = os.path.join(RAW, fname)
    df = pd.read_csv(path)
    print(f"\n{'='*60}")
    print(f"FILE: {fname}  |  rows={len(df)}  cols={len(df.columns)}")
    print(f"{'='*60}")
    print("COLUMNS:", list(df.columns))
    targets = [c for c in df.columns if any(t in c.lower() for t in ["status","target","label","eligible","manage","approv"])]
    print("TARGETS:", targets)
    print("DTYPES:")
    for col in df.columns:
        nu = df[col].nunique()
        miss = df[col].isna().sum()
        if df[col].dtype == object:
            vals = str(df[col].value_counts().head(5).to_dict())
            print(f"  {col:<45} object   nuniq={nu}  miss={miss}  vals={vals[:80]}")
        else:
            print(f"  {col:<45} {str(df[col].dtype):<10} min={df[col].min():.3g} max={df[col].max():.3g} mean={df[col].mean():.3g} miss={miss}")
    print("SAMPLE ROW 0:", dict(df.iloc[0]))
