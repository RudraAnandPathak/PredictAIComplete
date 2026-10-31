import pandas as pd
import pytest

from predictai_core.analysis_engine import (
    AnalysisInputError,
    analyze_dataset,
    correlation_matrix,
    detect_outliers_iqr,
    numeric_summary,
    profile_dataset,
)


def sample_df():
    return pd.DataFrame({
        "hours": [1, 2, 3, 4, 100],
        "score": [10, 20, 30, 40, 50],
        "group": ["A", "A", "B", "B", "B"],
        "incomplete": [1.0, None, 3.0, None, 5.0],
    })


def test_profile_counts_rows_columns_missing_and_duplicates():
    result = profile_dataset(sample_df())
    assert result["row_count"] == 5
    assert result["column_count"] == 4
    columns = {item["name"]: item for item in result["columns"]}
    assert columns["incomplete"]["missing_count"] == 2
    assert columns["incomplete"]["missing_percent"] == 40.0


def test_numeric_summary_is_calculated():
    result = numeric_summary(sample_df())
    assert result["score"]["mean"] == 30
    assert result["score"]["median"] == 30
    assert result["score"]["min"] == 10
    assert result["score"]["max"] == 50


def test_correlation_is_between_minus_one_and_one():
    result = correlation_matrix(sample_df())
    assert result["score"]["score"] == 1
    assert -1 <= result["hours"]["score"] <= 1


def test_iqr_detects_extreme_value():
    result = detect_outliers_iqr(sample_df())
    assert result["hours"]["outlier_count"] == 1
    assert result["hours"]["row_indices"] == [4]


def test_bundle_has_expected_sections_and_cautions():
    result = analyze_dataset(sample_df())
    assert result["analysis_version"] == "1.0.0"
    assert "numeric_summary" in result
    assert "categorical_summary" in result
    assert any("not causation" in note for note in result["notes"])


def test_empty_dataset_is_rejected():
    with pytest.raises(AnalysisInputError):
        analyze_dataset(pd.DataFrame())


def test_invalid_correlation_method_is_rejected():
    with pytest.raises(AnalysisInputError):
        correlation_matrix(sample_df(), method="invalid")
