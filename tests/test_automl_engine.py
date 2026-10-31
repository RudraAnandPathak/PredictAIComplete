import numpy as np
import pandas as pd
import pytest

from predictai_core.automl_engine import run_automl


def test_classification_compares_baseline_and_models():
    rng = np.random.default_rng(4)
    n = 120
    x = rng.normal(size=n)
    z = rng.normal(size=n)
    target = np.where(x + 0.4 * z > 0, "yes", "no")
    df = pd.DataFrame({"x": x, "z": z, "target": target})
    result = run_automl(df, "target")
    assert result["task"] == "classification"
    assert result["train_rows"] + result["test_rows"] == n
    assert len(result["leaderboard"]) >= 2
    assert result["best_model"] in {r["name"] for r in result["leaderboard"]}
    assert result["predictions"]
    assert "f1_macro" in result["best_metrics"]


def test_regression_has_mae_rmse_and_predictions():
    rng = np.random.default_rng(7)
    x = rng.normal(size=100)
    df = pd.DataFrame({"x": x, "category": np.where(x > 0, "high", "low"), "target": 3 * x + 2})
    result = run_automl(df, "target", task="regression")
    assert result["task"] == "regression"
    assert result["best_metrics"]["mae"] is not None
    assert result["best_metrics"]["rmse"] is not None
    assert len(result["predictions"]) == result["test_rows"]


def test_missing_target_rows_are_excluded_and_reported():
    df = pd.DataFrame({"x": range(30), "target": [float(i) if i != 3 else np.nan for i in range(30)]})
    result = run_automl(df, "target", task="regression")
    assert result["missing_target_rows_excluded"] == 1
    assert any("Excluded 1 rows" in note for note in result["cautions"])


def test_errors_for_unknown_target_and_tiny_data():
    df = pd.DataFrame({"x": range(10), "target": range(10)})
    with pytest.raises(ValueError, match="not found"):
        run_automl(df, "missing")
    with pytest.raises(ValueError, match="At least 20 rows"):
        run_automl(df, "target", task="regression")


def test_categorical_features_are_supported():
    df = pd.DataFrame({
        "city": ["A", "B", "C", "A", "B"] * 10,
        "age": list(range(50)),
        "target": ["yes", "no", "no", "yes", "no"] * 10,
    })
    result = run_automl(df, "target")
    assert "city" in result["features_used"]
    assert result["task"] == "classification"
