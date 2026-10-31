"""Descriptive pattern discovery for tabular data."""
from __future__ import annotations
import pandas as pd


def discover_patterns(dataframe: pd.DataFrame, top_n: int = 10) -> dict:
    if not isinstance(dataframe, pd.DataFrame) or dataframe.empty:
        raise ValueError("Provide a non-empty pandas DataFrame.")
    numeric = dataframe.select_dtypes(include="number")
    correlations = []
    if numeric.shape[1] >= 2:
        corr = numeric.corr(numeric_only=True)
        for i, col_a in enumerate(corr.columns):
            for col_b in corr.columns[i + 1:]:
                value = corr.loc[col_a, col_b]
                if pd.notna(value):
                    correlations.append({"column_a": str(col_a), "column_b": str(col_b), "correlation": float(value)})
    correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    outliers = []
    for col in numeric.columns:
        s = numeric[col].dropna()
        if len(s) >= 4:
            q1, q3 = s.quantile([.25, .75]); iqr = q3 - q1
            if iqr > 0:
                count = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
                if count:
                    outliers.append({"column": str(col), "iqr_outlier_count": count})
    return {"rows": len(dataframe), "columns": len(dataframe.columns), "missing_by_column": {str(k): int(v) for k, v in dataframe.isna().sum().items()}, "strongest_numeric_correlations": correlations[:max(1, int(top_n))], "potential_outliers": outliers, "caution": "Correlation and IQR flags are exploratory signals, not proof of causation or errors."}
