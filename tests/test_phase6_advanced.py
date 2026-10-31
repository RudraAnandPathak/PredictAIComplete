import pandas as pd
import pytest
from predictai_core.phase6 import forecast_series, make_news_scenario, compare_datasets, automatic_analysis
from predictai_core.phase6.knowledge_store import index_documents, search_knowledge, knowledge_stats, clear_knowledge


def test_forecast_series_returns_baseline_and_chronological_evaluation():
    result = forecast_series([10, 12, 14, 16, 18, 20, 22, 24, 26, 28], 2)
    assert len(result["trend_forecast"]) == 2
    assert result["evaluation"]["holdout_observations"] == 2
    assert result["trend_slope_per_step"] > 0


def test_forecast_rejects_too_little_history():
    with pytest.raises(ValueError):
        forecast_series([1, 2, 3], 2)


def test_news_scenario_is_explicit_adjustment():
    assert make_news_scenario([100, 200], -10) == [90, 180]
    with pytest.raises(ValueError):
        make_news_scenario([100], 101)


def test_dataset_compatibility_and_auto_analysis():
    result = compare_datasets([("a.csv", pd.DataFrame({"sales": [1, 2], "region": ["N", "S"]})), ("b.csv", pd.DataFrame({"sales": [3], "region": ["E"]}))])
    assert result["common_columns"] == ["region", "sales"]
    profile = automatic_analysis(pd.DataFrame({"sales": [1, 2, 3], "cost": [2, 3, 4]}))
    assert profile["numeric_summary"]
    assert profile["correlations"]


def test_persistent_knowledge_store(tmp_path):
    db = tmp_path / "knowledge.sqlite"
    result = index_documents([{"name": "report.txt", "text": "Revenue increased during the quarter.\n\nCosts also increased."}], db)
    assert result["documents_indexed"] == 1
    hits = search_knowledge("revenue increased quarter", db_path=db)
    assert hits and hits[0]["source"] == "report.txt"
    assert knowledge_stats(db)["documents"] == 1
    clear_knowledge(db)
    assert knowledge_stats(db)["chunks"] == 0
