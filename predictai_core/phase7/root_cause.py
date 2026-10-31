"""Exploratory contribution analysis; not a causal inference engine."""
from __future__ import annotations
from typing import Any
import pandas as pd
import numpy as np


def investigate_metric(df: pd.DataFrame, metric: str, group_by: str | None = None) -> dict[str, Any]:
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError('Upload a non-empty dataset first.')
    if metric not in df.columns:
        raise ValueError(f'Metric column {metric!r} was not found.')
    values = pd.to_numeric(df[metric], errors='coerce')
    valid = values.notna()
    if not valid.any():
        raise ValueError('Choose a numeric metric column.')
    out: dict[str, Any] = {'metric': metric, 'valid_rows': int(valid.sum()), 'missing_or_non_numeric': int((~valid).sum()), 'overall_mean': float(values[valid].mean()), 'overall_median': float(values[valid].median()), 'overall_std': float(values[valid].std()) if int(valid.sum()) > 1 else None, 'interpretation': 'Descriptive diagnostics show patterns and associations; they do not establish causes.'}
    if group_by and group_by in df.columns and group_by != metric:
        tmp = pd.DataFrame({'group': df[group_by].astype('string').fillna('(missing)'), 'value': values}).dropna(subset=['value'])
        grouped = tmp.groupby('group', dropna=False)['value'].agg(['count','mean','median','std']).reset_index()
        overall = float(tmp['value'].mean())
        grouped['difference_from_overall_mean'] = grouped['mean'] - overall
        out['group_by'] = group_by
        out['groups'] = grouped.sort_values('difference_from_overall_mean', key=lambda s: s.abs(), ascending=False).head(30).replace({np.nan: None}).to_dict(orient='records')
    numeric = df.select_dtypes(include='number')
    corr = {}
    if metric in numeric.columns and numeric.shape[1] > 1:
        c = numeric.corr(numeric_only=True)[metric].drop(labels=[metric], errors='ignore').dropna()
        corr = {str(k): float(v) for k,v in c.reindex(c.abs().sort_values(ascending=False).index).head(10).items()}
    out['numeric_associations'] = corr
    out['caution'] = 'These are exploratory associations. Confounding, measurement error, selection effects, and reverse causality may explain observed patterns.'
    return out
