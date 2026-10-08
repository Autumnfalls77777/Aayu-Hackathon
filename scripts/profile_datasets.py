"""
Profile both medicine datasets for SASTI DAWAI hackathon.
Outputs analysis to data/processed/
"""
import pandas as pd
import numpy as np
import json
import os
from collections import Counter

RAW_DIR = r"E:\Programming\new hackathon if orgor name\sasti-dawai\data\raw"
OUT_DIR = r"E:\Programming\new hackathon if orgor name\sasti-dawai\data\processed"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load datasets ──────────────────────────────────────────────────────────
print("=" * 80)
print("LOADING DATASETS")
print("=" * 80)

df_indian = pd.read_csv(os.path.join(RAW_DIR, "indian_medicine_data.csv"))
df_jan = pd.read_csv(os.path.join(RAW_DIR, "jan_aushadhi_products.csv"))

print(f"\nIndian Medicine Data: {df_indian.shape[0]:,} rows x {df_indian.shape[1]} cols")
print(f"Jan Aushadhi Products: {df_jan.shape[0]:,} rows x {df_jan.shape[1]} cols")

# ── Column info ─────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("COLUMN DETAILS — INDIAN MEDICINE DATA")
print("=" * 80)
for col in df_indian.columns:
    non_null = df_indian[col].notna().sum()
    null_pct = (df_indian[col].isna().sum() / len(df_indian)) * 100
    dtype = df_indian[col].dtype
    nunique = df_indian[col].nunique()
    print(f"  {col:25s} | dtype={str(dtype):10s} | non-null={non_null:>7,} | null={null_pct:5.1f}% | unique={nunique:>6,}")

print("\n" + "=" * 80)
print("COLUMN DETAILS — JAN AUSHADHI PRODUCTS")
print("=" * 80)
for col in df_jan.columns:
    non_null = df_jan[col].notna().sum()
    null_pct = (df_jan[col].isna().sum() / len(df_jan)) * 100
    dtype = df_jan[col].dtype
    nunique = df_jan[col].nunique()
    print(f"  {col:25s} | dtype={str(dtype):10s} | non-null={non_null:>7,} | null={null_pct:5.1f}% | unique={nunique:>6,}")

# ── Sample values ───────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("SAMPLE VALUES — INDIAN MEDICINE DATA (first 10)")
print("=" * 80)
for col in df_indian.columns:
    print(f"\n  {col}:")
    for v in df_indian[col].dropna().head(5):
        print(f"    {repr(v)}")

print("\n" + "=" * 80)
print("SAMPLE VALUES — JAN AUSHADHI PRODUCTS (first 10)")
print("=" * 80)
for col in df_jan.columns:
    print(f"\n  {col}:")
    for v in df_jan[col].dropna().head(5):
        print(f"    {repr(v)}")

# ── Price analysis ──────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("PRICE ANALYSIS")
print("=" * 80)

# Indian medicine prices
price_indian = pd.to_numeric(df_indian['price(₹)'], errors='coerce')
print(f"\nIndian Medicine Price (₹):")
print(f"  Non-numeric/missing: {price_indian.isna().sum():,}")
print(f"  Min: {price_indian.min()}")
print(f"  Max: {price_indian.max()}")
print(f"  Mean: {price_indian.mean():.2f}")
print(f"  Median: {price_indian.median():.2f}")
print(f"  Zero prices: {(price_indian == 0).sum():,}")
print(f"  Negative prices: {(price_indian < 0).sum():,}")

# Jan Aushadhi MRP
mrp_jan = pd.to_numeric(df_jan['MRP'], errors='coerce')
print(f"\nJan Aushadhi MRP (₹):")
print(f"  Non-numeric/missing: {mrp_jan.isna().sum():,}")
print(f"  Min: {mrp_jan.min()}")
print(f"  Max: {mrp_jan.max()}")
print(f"  Mean: {mrp_jan.mean():.2f}")
print(f"  Median: {mrp_jan.median():.2f}")
print(f"  Zero MRP: {(mrp_jan == 0).sum():,}")

# ── Type distribution (Indian) ─────────────────────────────────────────────
print("\n" + "=" * 80)
print("MEDICINE TYPE DISTRIBUTION (Indian)")
print("=" * 80)
type_counts = df_indian['type'].value_counts(dropna=False)
for t, c in type_counts.items():
    print(f"  {str(t):30s} : {c:>7,} ({c/len(df_indian)*100:.1f}%)")

# ── Is_discontinued ─────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("DISCONTINUED STATUS (Indian)")
print("=" * 80)
disc_counts = df_indian['Is_discontinued'].value_counts(dropna=False)
for t, c in disc_counts.items():
    print(f"  {str(t):10s} : {c:>7,} ({c/len(df_indian)*100:.1f}%)")

# ── Manufacturer analysis ───────────────────────────────────────────────────
print("\n" + "=" * 80)
print("TOP 20 MANUFACTURERS (Indian)")
print("=" * 80)
mfr_counts = df_indian['manufacturer_name'].value_counts().head(20)
for m, c in mfr_counts.items():
    print(f"  {str(m):40s} : {c:>7,}")

# ── Pack size analysis ──────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("PACK SIZE LABEL ANALYSIS (Indian)")
print("=" * 80)
pack_counts = df_indian['pack_size_label'].value_counts(dropna=False).head(30)
for p, c in pack_counts.items():
    print(f"  {str(p):40s} : {c:>7,}")

# ── Group Name analysis (Jan Aushadhi) ──────────────────────────────────────
print("\n" + "=" * 80)
print("GROUP NAME DISTRIBUTION (Jan Aushadhi)")
print("=" * 80)
group_counts = df_jan['Group Name'].value_counts(dropna=False)
for g, c in group_counts.items():
    print(f"  {str(g):50s} : {c:>5,}")

# ── Unit Size analysis (Jan Aushadhi) ───────────────────────────────────────
print("\n" + "=" * 80)
print("UNIT SIZE DISTRIBUTION (Jan Aushadhi)")
print("=" * 80)
unit_counts = df_jan['Unit Size'].value_counts(dropna=False).head(30)
for u, c in unit_counts.items():
    print(f"  {str(u):40s} : {c:>5,}")

# ── Composition analysis ────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("COMPOSITION FORMAT ANALYSIS")
print("=" * 80)

# Indian - short_composition1
comp1 = df_indian['short_composition1'].dropna()
print(f"\nIndian short_composition1: {len(comp1):,} non-null")
print(f"  Unique values: {comp1.nunique():,}")
print(f"  Sample values:")
for v in comp1.head(20):
    print(f"    {repr(v)}")

# Indian - short_composition2
comp2 = df_indian['short_composition2'].dropna()
print(f"\nIndian short_composition2: {len(comp2):,} non-null")
print(f"  Unique values: {comp2.nunique():,}")
print(f"  Sample values:")
for v in comp2.head(10):
    print(f"    {repr(v)}")

# Jan Aushadhi - Generic Name
generic = df_jan['Generic Name'].dropna()
print(f"\nJan Aushadhi Generic Name: {len(generic):,} non-null")
print(f"  Unique values: {generic.nunique():,}")
print(f"  Sample values:")
for v in generic.head(20):
    print(f"    {repr(v)}")

# ── Save summary to JSON ────────────────────────────────────────────────────
summary = {
    "indian_medicine_data": {
        "rows": int(df_indian.shape[0]),
        "cols": int(df_indian.shape[1]),
        "columns": list(df_indian.columns),
        "missing": {col: int(df_indian[col].isna().sum()) for col in df_indian.columns},
        "unique": {col: int(df_indian[col].nunique()) for col in df_indian.columns},
    },
    "jan_aushadhi_products": {
        "rows": int(df_jan.shape[0]),
        "cols": int(df_jan.shape[1]),
        "columns": list(df_jan.columns),
        "missing": {col: int(df_jan[col].isna().sum()) for col in df_jan.columns},
        "unique": {col: int(df_jan[col].nunique()) for col in df_jan.columns},
    }
}

with open(os.path.join(OUT_DIR, "profile_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n\nSummary saved to {os.path.join(OUT_DIR, 'profile_summary.json')}")
print("PROFILING COMPLETE")
