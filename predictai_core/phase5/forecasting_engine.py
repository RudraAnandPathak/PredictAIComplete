"""Simple, explicit baseline forecasting for regularly ordered numeric series."""
from __future__ import annotations
import numpy as np
import pandas as pd


def forecast_series(values, periods: int = 5, method: str = "linear_trend") -> dict:
    series = pd.to_numeric(pd.Series(values), errors="coerce").dropna().astype(float)
    periods = max(1, min(int(periods), 100))
    if len(series) < 3:
        raise ValueError("Forecasting requires at least 3 numeric observations.")
    if not np.isfinite(series.to_numpy()).all():
        raise ValueError("The series contains non-finite values.")
    y = series.to_numpy()
    if method == "naive":
        preds = np.repeat(y[-1], periods)
        description = "Naive baseline: repeats the latest observed value."
    elif method == "moving_average":
        window = min(3, len(y))
        preds = np.repeat(float(np.mean(y[-window:])), periods)
        description = f"Moving-average baseline using the last {window} observations."
    else:
        x = np.arange(len(y), dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        preds = intercept + slope * np.arange(len(y), len(y) + periods, dtype=float)
        description = "Linear trend extrapolation; it assumes the historical linear trend continues."
    return {"method": method, "observations": len(y), "forecast": [float(round(x, 6)) for x in preds], "description": description, "warning": "Forecasts are uncertain and can fail when seasonality, structural changes, or external factors matter. Compare with a time-ordered holdout baseline before relying on them."}
