"""PredictAI's reusable, deterministic dataset analysis engine.

All numeric results in this module are calculated with pandas/NumPy. The module
returns Python-native values where practical so results can later be sent to a
UI, API, report generator, or language model without asking the model to do math.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class AnalysisInputError(ValueError):
    """Raised when a dataset cannot be analyzed meaningfully."""


def _validate_dataframe(dataframe: pd.DataFrame) -> None:
    if not isinstance(dataframe, pd.DataFrame):
        raise AnalysisInputError("Expected a pandas DataFrame.")
    if dataframe.empty:
        raise AnalysisInputError("The dataset has no rows to analyze.")
    if len(dataframe.columns) == 0:
        raise AnalysisInputError("The dataset has no columns to analyze.")


def _safe_number(value: Any) -> int | float | None:
    """Convert NumPy scalars to JSON-friendly Python numbers; non-finite -> None."""
    if pd.isna(value):
        return None
    number = float(value)
    if not np.isfinite(number):
        return None
    if number.is_integer():
        return int(number)
    return number


def profile_dataset(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Return dataset dimensions, column types, missingness, and uniqueness."""
    _validate_dataframe(dataframe)
    columns = []
    for column in dataframe.columns:
        series = dataframe[column]
        missing_count = int(series.isna().sum())
        non_missing = int(series.notna().sum())
        columns.append({
            "name": str(column),
            "dtype": str(series.dtype),
            "missing_count": missing_count,
            "missing_percent": round(missing_count / len(dataframe) * 100, 2),
            "unique_count": int(series.nunique(dropna=True)),
            "non_missing_count": non_missing,
        })

    return {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "duplicate_row_count": int(dataframe.duplicated().sum()),
        "numeric_columns": [str(c) for c in dataframe.select_dtypes(include="number").columns],
        "categorical_columns": [
            str(c) for c in dataframe.select_dtypes(include=["object", "category", "bool"]).columns
        ],
        "columns": columns,
    }


def numeric_summary(dataframe: pd.DataFrame) -> dict[str, dict[str, int | float | None]]:
    """Calculate standard descriptive statistics for numeric columns only."""
    _validate_dataframe(dataframe)
    numeric = dataframe.select_dtypes(include="number")
    results: dict[str, dict[str, int | float | None]] = {}
    for column in numeric.columns:
        values = numeric[column].dropna()
        if values.empty:
            results[str(column)] = {
                "count": 0, "mean": None, "median": None, "std": None,
                "min": None, "q1": None, "q3": None, "max": None,
            }
            continue
        results[str(column)] = {
            "count": int(values.count()),
            "mean": _safe_number(values.mean()),
            "median": _safe_number(values.median()),
            "std": _safe_number(values.std()),
            "min": _safe_number(values.min()),
            "q1": _safe_number(values.quantile(0.25)),
            "q3": _safe_number(values.quantile(0.75)),
            "max": _safe_number(values.max()),
        }
    return results


def correlation_matrix(dataframe: pd.DataFrame, method: str = "pearson") -> dict[str, dict[str, int | float | None]]:
    """Return pairwise correlations for numeric columns; undefined values become None."""
    _validate_dataframe(dataframe)
    if method not in {"pearson", "spearman", "kendall"}:
        raise AnalysisInputError("method must be 'pearson', 'spearman', or 'kendall'.")
    numeric = dataframe.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return {}
    corr = numeric.corr(method=method)
    return {
        str(row): {str(col): _safe_number(corr.loc[row, col]) for col in corr.columns}
        for row in corr.index
    }


def detect_outliers_iqr(dataframe: pd.DataFrame, multiplier: float = 1.5) -> dict[str, dict[str, Any]]:
    """Flag numeric values outside Q1 - multiplier*IQR or Q3 + multiplier*IQR.

    This is a screening heuristic, not a claim that flagged observations are errors.
    NaN values are ignored. Columns with no spread (IQR=0) are handled by the same
    bounds rule and may have no outliers.
    """
    _validate_dataframe(dataframe)
    if not isinstance(multiplier, (int, float)) or not np.isfinite(multiplier) or multiplier < 0:
        raise AnalysisInputError("multiplier must be a finite non-negative number.")

    results: dict[str, dict[str, Any]] = {}
    numeric = dataframe.select_dtypes(include="number")
    for column in numeric.columns:
        series = numeric[column].dropna()
        if series.empty:
            results[str(column)] = {
                "lower_bound": None, "upper_bound": None,
                "outlier_count": 0, "outlier_percent": 0.0, "row_indices": [],
            }
            continue
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - float(multiplier) * iqr
        upper = q3 + float(multiplier) * iqr
        mask = numeric[column].notna() & ((numeric[column] < lower) | (numeric[column] > upper))
        indices = [int(i) if isinstance(i, (int, np.integer)) else str(i) for i in dataframe.index[mask]]
        count = int(mask.sum())
        results[str(column)] = {
            "lower_bound": _safe_number(lower),
            "upper_bound": _safe_number(upper),
            "outlier_count": count,
            "outlier_percent": round(count / max(int(series.count()), 1) * 100, 2),
            "row_indices": indices[:100],
            "row_indices_truncated": count > 100,
        }
    return results


def categorical_summary(dataframe: pd.DataFrame, top_n: int = 10) -> dict[str, dict[str, Any]]:
    """Summarize category counts, excluding missing values from frequency tables."""
    _validate_dataframe(dataframe)
    if not isinstance(top_n, int) or top_n < 1:
        raise AnalysisInputError("top_n must be a positive integer.")
    categorical = dataframe.select_dtypes(include=["object", "category", "bool"])
    results: dict[str, dict[str, Any]] = {}
    for column in categorical.columns:
        counts = categorical[column].value_counts(dropna=True).head(top_n)
        results[str(column)] = {
            "non_missing_count": int(categorical[column].notna().sum()),
            "unique_count": int(categorical[column].nunique(dropna=True)),
            "top_values": [
                {"value": str(value), "count": int(count)}
                for value, count in counts.items()
            ],
        }
    return results


def analyze_dataset(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Run the initial deterministic analysis bundle on a tabular dataset."""
    profile = profile_dataset(dataframe)
    return {
        "analysis_version": "1.0.0",
        "profile": profile,
        "numeric_summary": numeric_summary(dataframe),
        "correlations": correlation_matrix(dataframe),
        "categorical_summary": categorical_summary(dataframe),
        "outliers_iqr": detect_outliers_iqr(dataframe),
        "notes": [
            "Correlations describe association, not causation.",
            "IQR outlier flags are screening indicators, not proof of data errors.",
            "Numeric statistics are calculated only for columns pandas recognizes as numeric.",
        ],
    }
