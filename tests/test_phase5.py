import pandas as pd
import pytest
from predictai_core.phase5.document_collection import collect_document_text
from predictai_core.phase5.exam_intelligence import analyze_exam_collection, extract_questions, generate_practice_paper
from predictai_core.phase5.forecasting_engine import forecast_series
from predictai_core.phase5.pattern_discovery import discover_patterns
from predictai_core.phase5.evidence_engine import search_evidence
from predictai_core.phase5.validation import evaluate_forecast


def test_collect_document_text_normalizes_and_skips_empty():
    got = collect_document_text([{"name": "a", "text": "hello   world"}, {"name": "b", "text": "  "}])
    assert len(got) == 1 and got[0]["text"] == "hello world"


def test_exam_analysis_and_practice_set():
    paper = {"name": "paper1.txt", "text": "Q1. Define force. [2 marks]\n\nQ2. Calculate speed from distance and time. (3 marks)"}
    result = analyze_exam_collection([paper])
    assert result["paper_count"] == 1
    assert result["question_count"] >= 1
    practice = generate_practice_paper(result, 2)
    assert practice and "question" in practice[0]


def test_forecast_methods_return_requested_horizon():
    result = forecast_series([1, 2, 3, 4, 5], 3, "linear_trend")
    assert len(result["forecast"]) == 3
    assert result["forecast"][0] > 5


def test_forecast_requires_enough_observations():
    with pytest.raises(ValueError): forecast_series([1, 2], 2)


def test_pattern_discovery_finds_correlation_and_missing():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [2, 4, 6, 8, 10], "c": [1, None, 1, 1, 1]})
    result = discover_patterns(df)
    assert result["missing_by_column"]["c"] == 1
    assert result["strongest_numeric_correlations"][0]["correlation"] == pytest.approx(1.0)


def test_evidence_search_ranks_shared_terms():
    docs = [{"name": "a", "text": "Climate change increases flood risk.\n\nThe garden has flowers."}]
    hits = search_evidence("flood risk", docs)
    assert hits and "flood" in hits[0]["evidence"].lower()


def test_time_ordered_validation_compares_baselines():
    result = evaluate_forecast([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], test_size=2)
    assert result["test_observations"] == 2
    assert "linear_trend" in result and "naive_baseline" in result
