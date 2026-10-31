"""Transparent baseline forecasting and news-informed scenario utilities."""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def forecast_series(values: list[float] | pd.Series, horizon: int = 3) -> dict[str, Any]:
    """Forecast a univariate ordered series with a linear trend and naive baseline.

    Uses chronological holdout evaluation where enough observations exist. It is
    deliberately simple and reports limitations rather than promising accuracy.
    """
    s = pd.to_numeric(pd.Series(values), errors="coerce").dropna().astype(float).reset_index(drop=True)
    horizon = max(1, min(int(horizon), 36))
    if len(s) < 4:
        raise ValueError("At least 4 valid historical numeric observations are required for this baseline forecast.")
    x = np.arange(len(s)).reshape(-1, 1)
    model = LinearRegression().fit(x, s.to_numpy())
    future_x = np.arange(len(s), len(s) + horizon).reshape(-1, 1)
    trend_pred = model.predict(future_x)
    naive_pred = np.repeat(float(s.iloc[-1]), horizon)
    evaluation = None
    if len(s) >= 8:
        split = max(4, int(len(s) * 0.8))
        train = s.iloc[:split]
        test = s.iloc[split:]
        if len(test):
            hold_model = LinearRegression().fit(np.arange(len(train)).reshape(-1, 1), train.to_numpy())
            hold_pred = hold_model.predict(np.arange(len(train), len(s)).reshape(-1, 1))
            naive_hold = np.repeat(float(train.iloc[-1]), len(test))
            evaluation = {
                "holdout_observations": int(len(test)),
                "trend_mae": float(np.mean(np.abs(test.to_numpy() - hold_pred))),
                "trend_rmse": float(np.sqrt(np.mean((test.to_numpy() - hold_pred) ** 2))),
                "naive_mae": float(np.mean(np.abs(test.to_numpy() - naive_hold))),
                "naive_rmse": float(np.sqrt(np.mean((test.to_numpy() - naive_hold) ** 2))),
                "split_note": "Chronological holdout; the latest observations were not used to fit the evaluation model.",
            }
    return {
        "observations": int(len(s)),
        "last_value": float(s.iloc[-1]),
        "trend_slope_per_step": float(model.coef_[0]),
        "trend_forecast": [float(x) for x in trend_pred],
        "naive_forecast": [float(x) for x in naive_pred],
        "evaluation": evaluation,
        "limitations": ["This is a simple linear-trend baseline, not a guarantee of future outcomes.", "No seasonality or external variables are modelled unless separately supplied.", "A short series can produce unstable forecasts."],
    }


def make_news_scenario(baseline: list[float], adjustment_percent: float) -> list[float]:
    """Apply an explicitly user-selected scenario adjustment, not an inferred fact."""
    if not -100 <= float(adjustment_percent) <= 100:
        raise ValueError("Scenario adjustment must be between -100% and +100%.")
    return [float(v) * (1 + float(adjustment_percent) / 100) for v in baseline]
