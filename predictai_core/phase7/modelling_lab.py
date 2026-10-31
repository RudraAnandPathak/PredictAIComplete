"""Phase 7 AutoML facade and prediction simulation helpers."""
from __future__ import annotations
from typing import Any
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score
import numpy as np
from predictai_core.automl_engine import run_automl


def compare_models(df: pd.DataFrame, target: str, task: str = 'auto') -> dict[str, Any]:
    """Use the existing tested AutoML engine; keep target selection explicit."""
    return run_automl(df, target_column=target, task=task)


def fit_simulator(df: pd.DataFrame, target: str, task: str = 'auto') -> dict[str, Any]:
    if target not in df.columns:
        raise ValueError(f'Target {target!r} was not found.')
    work = df.replace([np.inf, -np.inf], np.nan).dropna(subset=[target]).copy()
    if len(work) < 20 or work[target].nunique() < 2:
        raise ValueError('At least 20 usable rows and two target values are required.')
    y = work[target]
    inferred = task
    if inferred == 'auto':
        inferred = 'classification' if (not pd.api.types.is_numeric_dtype(y) or (pd.api.types.is_integer_dtype(y) and y.nunique() <= 20)) else 'regression'
    X = work.drop(columns=[target])
    keep = [c for c in X.columns if X[c].nunique(dropna=True) > 1 and not X[c].isna().all()]
    X = X[keep]
    if X.empty:
        raise ValueError('No useful feature columns remain.')
    numeric = X.select_dtypes(include='number').columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]
    transformers = []
    if numeric: transformers.append(('num', SimpleImputer(strategy='median'), numeric))
    if categorical: transformers.append(('cat', Pipeline([('imputer', SimpleImputer(strategy='most_frequent')), ('onehot', OneHotEncoder(handle_unknown='ignore'))]), categorical))
    pre = ColumnTransformer(transformers, remainder='drop')
    if inferred == 'classification':
        estimator = RandomForestClassifier(n_estimators=160, min_samples_leaf=2, class_weight='balanced', random_state=42, n_jobs=-1)
        y = y.astype(str)
    else:
        if not pd.api.types.is_numeric_dtype(y): raise ValueError('Regression requires a numeric target.')
        estimator = RandomForestRegressor(n_estimators=160, min_samples_leaf=2, random_state=42, n_jobs=-1)
        y = pd.to_numeric(y, errors='coerce')
        ok = y.notna(); X, y = X.loc[ok], y.loc[ok]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=42, stratify=y if inferred == 'classification' and y.value_counts().min() >= 2 else None)
    model = Pipeline([('preprocess', pre), ('model', estimator)])
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    metrics = ({'accuracy': float(accuracy_score(y_test, pred)), 'f1_macro': float(f1_score(y_test, pred, average='macro', zero_division=0))} if inferred == 'classification' else {'mae': float(mean_absolute_error(y_test, pred)), 'rmse': float(np.sqrt(mean_squared_error(y_test, pred))), 'r2': float(r2_score(y_test, pred)) if len(y_test)>1 else None})
    return {'model': model, 'feature_columns': list(X.columns), 'target': target, 'task': inferred, 'metrics': metrics, 'test_rows': len(y_test), 'note': 'This simulator is a predictive scenario tool, not a causal intervention model.'}


def simulate(simulator: dict[str, Any], baseline: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    cols = simulator['feature_columns']
    row = {c: baseline.get(c, np.nan) for c in cols}
    row.update({k: v for k,v in changes.items() if k in cols})
    X = pd.DataFrame([row], columns=cols)
    pred = simulator['model'].predict(X)[0]
    out = {'prediction': str(pred) if simulator['task']=='classification' else float(pred), 'task': simulator['task'], 'changed_features': {k: row[k] for k in changes if k in cols}, 'caution': simulator['note']}
    if simulator['task']=='classification' and hasattr(simulator['model'], 'predict_proba'):
        try: out['class_probabilities'] = {str(c): float(p) for c,p in zip(simulator['model'].named_steps['model'].classes_, simulator['model'].predict_proba(X)[0])}
        except Exception: pass
    return out
