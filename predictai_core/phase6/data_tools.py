"""Dataset compatibility checks and deterministic analysis helpers."""
from __future__ import annotations
from typing import Any
import pandas as pd
import numpy as np


def compare_datasets(frames: list[tuple[str, pd.DataFrame]]) -> dict[str, Any]:
    summaries = []
    for name, df in frames:
        summaries.append({"name": name, "rows": int(len(df)), "columns": [str(c) for c in df.columns], "numeric_columns": [str(c) for c in df.select_dtypes(include="number").columns], "missing_cells": int(df.isna().sum().sum()), "duplicates": int(df.duplicated().sum())})
    common = set(summaries[0]["columns"]) if summaries else set()
    for s in summaries[1:]: common &= set(s["columns"])
    return {"datasets": summaries, "common_columns": sorted(common), "can_concat_by_columns": bool(len(frames) >= 2 and common), "note": "Shared column names do not guarantee identical meanings, units, or grain. Review compatibility before combining."}


def automatic_analysis(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        raise ValueError("Upload a non-empty dataset first.")
    numeric = df.select_dtypes(include="number")
    out: dict[str, Any] = {
        "rows": int(len(df)), "columns": int(len(df.columns)),
        "missing_by_column": {str(k): int(v) for k, v in df.isna().sum().items()},
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_summary": {}, "correlations": {}, "categorical_summary": {}, "warnings": []
    }
    if not numeric.empty:
        out["numeric_summary"] = numeric.describe().replace({np.nan: None}).to_dict()
        if numeric.shape[1] >= 2:
            out["correlations"] = numeric.corr().replace({np.nan: None}).to_dict()
        for col in numeric.columns:
            q1, q3 = numeric[col].quantile([.25,.75])
            iqr = q3-q1
            out.setdefault("outlier_screening", {})[str(col)] = int(((numeric[col] < q1-1.5*iqr) | (numeric[col] > q3+1.5*iqr)).sum())
    categorical = df.select_dtypes(include=["object", "category", "bool"])
    for col in categorical.columns:
        out["categorical_summary"][str(col)] = [{"value": str(k), "count": int(v)} for k,v in categorical[col].value_counts(dropna=True).head(10).items()]
    if len(df) < 30: out["warnings"].append("Fewer than 30 rows: estimates and relationships may be unstable.")
    if int(df.isna().sum().sum()): out["warnings"].append("Missing values exist; inspect the missingness pattern before modelling.")
    out["warnings"].append("Correlation and feature importance do not establish causation.")
    return out
