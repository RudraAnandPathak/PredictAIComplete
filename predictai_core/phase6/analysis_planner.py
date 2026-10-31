"""Rule-based first-pass planner for mapping plain-language questions to analyses.

This planner recommends methods; it does not silently run tests or claim causation.
"""
from __future__ import annotations
import re
from typing import Any
import pandas as pd


def plan_analysis(question: str, dataframe: pd.DataFrame | None = None) -> dict[str, Any]:
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Please provide a question in everyday language.")
    q = question.lower()
    methods: list[dict[str, str]] = []
    def add(name: str, why: str, checks: str) -> None:
        if not any(m["method"] == name for m in methods):
            methods.append({"method": name, "reason": why, "checks": checks})

    if any(k in q for k in ("forecast", "predict next", "future", "next month", "next year", "over time")):
        add("Time-series forecasting", "The question asks about future values or change over time.", "Confirm observations are chronologically ordered, periods are regular, and enough history exists; compare against a simple baseline.")
    if any(k in q for k in ("relationship", "correlat", "associated", "related", "move together")):
        add("Correlation analysis", "The question asks whether numerical variables vary together.", "Check numeric types, sample size, outliers and whether Pearson or rank correlation is more appropriate; association is not causation.")
    if any(k in q for k in ("compare", "difference between", "higher than", "lower than", "different groups", "significant difference")):
        add("Group comparison", "The question asks whether groups differ.", "Identify outcome and groups first; check independence, distribution, sample size and variance before selecting a test.")
    if any(k in q for k in ("why", "factors", "influence", "important variables", "what drives", "explain the prediction")):
        add("Feature and explanatory analysis", "The question asks which variables may help explain an outcome.", "Separate predictive contribution from causal evidence; use domain context and validation, and inspect confounding and leakage.")
    if any(k in q for k in ("classify", "classification", "yes or no", "will they", "which category", "predict whether")):
        add("Classification", "The outcome appears categorical.", "Identify the target label, inspect class balance and leakage, and use held-out evaluation with suitable precision/recall metrics.")
    if any(k in q for k in ("group customers", "segments", "cluster", "similar groups", "group similar")):
        add("Clustering", "The question asks for groups without a known target label.", "Scale numeric features when appropriate, inspect mixed data types, and evaluate whether clusters are stable and interpretable.")
    if any(k in q for k in ("outlier", "unusual", "anomal", "strange value")):
        add("Outlier screening", "The question asks to identify unusual observations.", "Treat flags as candidates for review, not proof of errors; account for skew and legitimate rare events.")
    if any(k in q for k in ("summar", "overview", "describe", "what is in", "profile this data", "explore")) or not methods:
        add("Descriptive analysis and data-quality profile", "A summary establishes the dataset's structure before deeper analysis.", "Review missingness, duplicates, data types, distributions and possible data-entry issues.")

    profile = None
    warnings = []
    if dataframe is not None:
        numeric = list(dataframe.select_dtypes(include="number").columns)
        categorical = list(dataframe.select_dtypes(include=["object", "category", "bool"]).columns)
        profile = {"rows": int(len(dataframe)), "columns": int(len(dataframe.columns)), "numeric_columns": [str(c) for c in numeric], "categorical_columns": [str(c) for c in categorical], "missing_cells": int(dataframe.isna().sum().sum())}
        if len(dataframe) < 30:
            warnings.append("Small datasets can produce unstable estimates; treat inferential results cautiously.")
        if profile["missing_cells"]:
            warnings.append("Missing values were detected; handling them may change results.")
        if not numeric:
            warnings.append("No numeric columns were detected; numerical correlation/regression may not be suitable without transformation or another target.")
    return {"question": question.strip(), "recommended_analyses": methods, "data_profile": profile, "warnings": warnings, "limitations": ["Recommendations are a starting point, not an automatic guarantee that assumptions are met.", "Statistical association and model feature importance do not establish causation."]}
