"""A cautious, transparent baseline AutoML engine for tabular datasets.

This module compares simple baseline models with a small set of standard models.
It uses a held-out test set and sklearn Pipelines so preprocessing is fit only on
training data. It is intended as a first version, not a replacement for expert
model validation in high-stakes settings.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import math
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score, mean_absolute_error,
    mean_squared_error, precision_score, r2_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder


@dataclass
class ModelResult:
    name: str
    task: str
    metrics: dict[str, float | None]
    is_baseline: bool = False
    notes: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _json_number(value: Any) -> float | None:
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _infer_task(target: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(target) or pd.api.types.is_object_dtype(target) or pd.api.types.is_categorical_dtype(target) or pd.api.types.is_string_dtype(target):
        return "classification"
    unique = target.nunique(dropna=True)
    # Integer-coded targets with few distinct values are often classes.
    if pd.api.types.is_integer_dtype(target) and unique <= min(20, max(2, int(len(target) * 0.05))):
        return "classification"
    return "regression"


def _preprocessor(X: pd.DataFrame, scale_numeric: bool = False) -> ColumnTransformer:
    numeric = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    from sklearn.pipeline import Pipeline as SkPipeline
    transformers: list[tuple[str, Any, list[str]]] = []
    if numeric:
        transformers.append(("numeric", SkPipeline(numeric_steps), numeric))
    if categorical:
        transformers.append(("categorical", SkPipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), categorical))
    if not transformers:
        raise ValueError("No usable feature columns remain after excluding the target.")
    return ColumnTransformer(transformers=transformers, remainder="drop", verbose_feature_names_out=False)


def _model_candidates(task: str, X_train: pd.DataFrame) -> list[tuple[str, Any, bool]]:
    if task == "classification":
        return [
            ("Dummy baseline", DummyClassifier(strategy="most_frequent"), True),
            ("Logistic regression", LogisticRegression(max_iter=1500, class_weight=None), False),
            ("Random forest", RandomForestClassifier(n_estimators=250, min_samples_leaf=2, random_state=42, n_jobs=-1, class_weight="balanced"), False),
        ]
    return [
        ("Dummy baseline", DummyRegressor(strategy="median"), True),
        ("Linear regression", LinearRegression(), False),
        ("Random forest", RandomForestRegressor(n_estimators=250, min_samples_leaf=2, random_state=42, n_jobs=-1), False),
    ]


def _classification_metrics(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float | None]:
    pred = model.predict(X_test)
    metrics: dict[str, float | None] = {
        "accuracy": _json_number(accuracy_score(y_test, pred)),
        "balanced_accuracy": _json_number(balanced_accuracy_score(y_test, pred)),
        "precision_macro": _json_number(precision_score(y_test, pred, average="macro", zero_division=0)),
        "recall_macro": _json_number(recall_score(y_test, pred, average="macro", zero_division=0)),
        "f1_macro": _json_number(f1_score(y_test, pred, average="macro", zero_division=0)),
        "roc_auc": None,
    }
    try:
        if hasattr(model, "predict_proba") and len(pd.unique(y_test)) == 2:
            probs = model.predict_proba(X_test)[:, 1]
            metrics["roc_auc"] = _json_number(roc_auc_score(y_test, probs))
    except (ValueError, IndexError):
        pass
    return metrics


def _regression_metrics(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float | None]:
    pred = model.predict(X_test)
    return {
        "mae": _json_number(mean_absolute_error(y_test, pred)),
        "rmse": _json_number(np.sqrt(mean_squared_error(y_test, pred))),
        "r2": _json_number(r2_score(y_test, pred)) if len(y_test) >= 2 else None,
    }


def run_automl(
    dataframe: pd.DataFrame,
    target_column: str,
    task: str = "auto",
    test_size: float = 0.2,
    random_state: int = 42,
    max_rows: int = 100_000,
) -> dict[str, Any]:
    """Compare baseline and candidate models for a selected target column.

    Returns serializable metrics, best model name, test predictions, and cautions.
    The fitted model objects are deliberately not returned or persisted.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("dataframe must be a pandas DataFrame")
    if target_column not in dataframe.columns:
        raise ValueError(f"Target column {target_column!r} was not found.")
    if not 0.1 <= float(test_size) <= 0.4:
        raise ValueError("test_size must be between 0.10 and 0.40")
    if len(dataframe) > max_rows:
        raise ValueError(f"Dataset has {len(dataframe):,} rows; this first version is limited to {max_rows:,} rows.")

    df = dataframe.copy()
    original_rows = len(df)
    df = df.replace([np.inf, -np.inf], np.nan)
    missing_target = int(df[target_column].isna().sum())
    df = df.loc[df[target_column].notna()].copy()
    if len(df) < 20:
        raise ValueError("At least 20 rows with a non-missing target are required for this initial AutoML workflow.")
    if df[target_column].nunique() < 2:
        raise ValueError("The target must contain at least two distinct values.")

    y = df[target_column]
    X = df.drop(columns=[target_column])
    # Remove constant and entirely empty features.
    all_missing = [c for c in X.columns if X[c].isna().all()]
    constant = [c for c in X.columns if X[c].nunique(dropna=True) <= 1]
    drop_features = sorted(set(all_missing + constant))
    if drop_features:
        X = X.drop(columns=drop_features)
    if X.shape[1] == 0:
        raise ValueError("No useful feature columns remain after removing the target and constant/empty columns.")

    chosen_task = _infer_task(y) if task == "auto" else task
    if chosen_task not in {"classification", "regression"}:
        raise ValueError("task must be 'auto', 'classification', or 'regression'.")
    if chosen_task == "classification":
        y = y.astype(str)
        class_counts = y.value_counts()
        if len(class_counts) < 2 or int(class_counts.min()) < 2:
            raise ValueError("Each classification class needs at least two rows. Combine rare classes or choose another target.")
        stratify = y if int(class_counts.min()) >= 2 and int(round(len(y) * test_size)) >= len(class_counts) else None
    else:
        if not pd.api.types.is_numeric_dtype(y):
            raise ValueError("Regression requires a numeric target. Choose classification for category labels.")
        y = pd.to_numeric(y, errors="coerce")
        valid = y.notna()
        X, y = X.loc[valid], y.loc[valid]
        if len(y) < 20:
            raise ValueError("Fewer than 20 usable rows remain after removing missing/non-numeric target values.")
        stratify = None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )
    candidates = _model_candidates(chosen_task, X_train)
    results: list[ModelResult] = []
    fitted: dict[str, Pipeline] = {}
    failure_notes: list[str] = []

    for name, estimator, is_baseline in candidates:
        scale = name == "Logistic regression"
        pipeline = Pipeline([("preprocess", _preprocessor(X_train, scale_numeric=scale)), ("model", estimator)])
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                pipeline.fit(X_train, y_train)
                metrics = _classification_metrics(pipeline, X_test, y_test) if chosen_task == "classification" else _regression_metrics(pipeline, X_test, y_test)
            results.append(ModelResult(name=name, task=chosen_task, metrics=metrics, is_baseline=is_baseline))
            fitted[name] = pipeline
        except Exception as exc:
            failure_notes.append(f"{name} could not be fitted: {type(exc).__name__}: {exc}")

    if not results:
        raise RuntimeError("No models could be fitted. Check the feature types and missing values. " + "; ".join(failure_notes))

    # Select by F1 macro for classification and lowest RMSE for regression.
    if chosen_task == "classification":
        score_key = "f1_macro"
        best = max(results, key=lambda r: r.metrics.get(score_key) if r.metrics.get(score_key) is not None else -1)
        leaderboard = sorted(results, key=lambda r: r.metrics.get(score_key) if r.metrics.get(score_key) is not None else -1, reverse=True)
    else:
        score_key = "rmse"
        best = min(results, key=lambda r: r.metrics.get(score_key) if r.metrics.get(score_key) is not None else float("inf"))
        leaderboard = sorted(results, key=lambda r: r.metrics.get(score_key) if r.metrics.get(score_key) is not None else float("inf"))

    best_pipeline = fitted[best.name]
    predictions = best_pipeline.predict(X_test)
    prediction_rows = []
    for idx, actual, predicted in zip(X_test.index.tolist(), y_test.tolist(), predictions.tolist()):
        prediction_rows.append({"row_index": str(idx), "actual": str(actual) if chosen_task == "classification" else _json_number(actual), "predicted": str(predicted) if chosen_task == "classification" else _json_number(predicted)})

    cautions = [
        "This is a first-pass model comparison using one held-out split, not cross-validation; scores may vary with a different split.",
        "Predictive associations do not establish causation. Validate the model with domain knowledge before using predictions for decisions.",
        "No model or uploaded data is saved by this function; persistence and model deployment are not implemented in this phase.",
    ]
    if missing_target:
        cautions.append(f"Excluded {missing_target} rows with missing target values (from {original_rows} original rows).")
    if drop_features:
        cautions.append("Removed constant or entirely empty features: " + ", ".join(map(str, drop_features)) + ".")
    if failure_notes:
        cautions.extend(failure_notes)

    return {
        "target_column": target_column,
        "task": chosen_task,
        "selection_metric": score_key,
        "best_model": best.name,
        "best_metrics": best.metrics,
        "leaderboard": [r.to_dict() for r in leaderboard],
        "test_rows": len(X_test),
        "train_rows": len(X_train),
        "features_used": X.columns.tolist(),
        "dropped_features": drop_features,
        "missing_target_rows_excluded": missing_target,
        "predictions": prediction_rows,
        "cautions": cautions,
    }
