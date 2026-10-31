"""Time-ordered holdout evaluation for forecast baselines."""
from __future__ import annotations
import numpy as np
import pandas as pd


def evaluate_forecast(values, test_size: int | None = None) -> dict:
    series = pd.to_numeric(pd.Series(values), errors="coerce").dropna().astype(float).to_numpy()
    n = len(series)
    if n < 5:
        raise ValueError("Validation requires at least 5 numeric observations.")
    size = test_size or max(1, min(n // 5, 10))
    if size < 1 or size >= n:
        raise ValueError("test_size must be at least 1 and smaller than the series length.")
    train, actual = series[:-size], series[-size:]
    naive = np.repeat(train[-1], size)
    x = np.arange(len(train), dtype=float)
    slope, intercept = np.polyfit(x, train, 1)
    trend = intercept + slope * np.arange(len(train), len(train) + size, dtype=float)
    def metrics(pred):
        err = actual - pred
        return {"mae": float(np.mean(np.abs(err))), "rmse": float(np.sqrt(np.mean(err ** 2)))}
    return {"train_observations": len(train), "test_observations": size, "naive_baseline": metrics(naive), "linear_trend": metrics(trend), "note": "The final observations were held out in time order. Prefer the method with lower holdout error; this small test does not guarantee future accuracy."}
