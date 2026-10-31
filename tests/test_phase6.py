import pandas as pd
import pytest
from predictai_core.phase6 import plan_analysis, combine_document_evidence, assess_uncertainty


def test_planner_maps_forecast_question():
    result = plan_analysis("Can you forecast sales for next year?")
    assert any(x["method"] == "Time-series forecasting" for x in result["recommended_analyses"])


def test_planner_uses_data_profile_and_flags_missing():
    df = pd.DataFrame({"sales": [1, None, 3], "region": ["A", "B", "A"]})
    result = plan_analysis("Explain the factors and relationships", df)
    assert result["data_profile"]["missing_cells"] == 1
    assert result["warnings"]
    assert len(result["recommended_analyses"]) >= 2


def test_empty_question_rejected():
    with pytest.raises(ValueError):
        plan_analysis("  ")


def test_evidence_returns_source_and_actual_snippet():
    docs = [{"name": "sales.pdf", "text": "Sales increased in January.\n\nCosts rose in February."}]
    hits = combine_document_evidence("Why did sales increase in January?", docs)
    assert hits
    assert hits[0]["source"] == "sales.pdf"
    assert "Sales increased" in hits[0]["evidence"]


def test_evidence_empty_when_no_match():
    assert combine_document_evidence("Quantum astrophysics", [{"name": "x", "text": "Sales rose."}]) == []


def test_uncertainty_does_not_invent_confidence():
    result = assess_uncertainty(sample_size=12, missing_percent=10)
    assert result["confidence_percent"] is None
    assert any("small" in n.lower() for n in result["notes"])
    assert any("missing" in n.lower() for n in result["notes"])


def test_uncertainty_validates_missing_percentage():
    with pytest.raises(ValueError):
        assess_uncertainty(missing_percent=101)
