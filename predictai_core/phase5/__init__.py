"""PredictAI Phase 5: intelligence, exam analysis, forecasting and validation."""
from .exam_intelligence import analyze_exam_collection, generate_practice_paper
from .forecasting_engine import forecast_series
from .pattern_discovery import discover_patterns
from .evidence_engine import search_evidence
from .validation import evaluate_forecast

__all__ = ["analyze_exam_collection", "generate_practice_paper", "forecast_series", "discover_patterns", "search_evidence", "evaluate_forecast"]
