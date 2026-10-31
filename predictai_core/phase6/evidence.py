"""Small transparent utilities for evidence aggregation and uncertainty notes."""
from __future__ import annotations
import re
from typing import Any

_STOPWORDS = {"the","and","for","that","with","this","from","what","when","where","which","would","could","should","about","have","has","are","was","were","into","your","you","does","did","can","will","why","how"}


def combine_document_evidence(question: str, documents: list[dict[str, Any]], top_k: int = 8) -> list[dict[str, Any]]:
    """Return ranked text snippets with source names; no generated or fabricated citations."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("A question is required.")
    terms = {t for t in re.findall(r"[a-z0-9]{3,}", question.lower()) if t not in _STOPWORDS}
    if not terms:
        return []
    hits = []
    for doc in documents:
        name = str(doc.get("name", "Untitled document"))
        raw = str(doc.get("text", ""))
        chunks = [p.strip() for p in re.split(r"\n\s*\n|(?<=[.!?])\s+", raw) if p.strip()]
        for i, chunk in enumerate(chunks):
            words = set(re.findall(r"[a-z0-9]{3,}", chunk.lower()))
            overlap = terms & words
            if overlap:
                hits.append({"source": name, "chunk_index": i, "matched_terms": sorted(overlap), "score": round(len(overlap) / len(terms), 3), "evidence": chunk[:1800]})
    hits.sort(key=lambda h: (h["score"], len(h["matched_terms"]), len(h["evidence"])), reverse=True)
    return hits[:max(1, min(int(top_k), 30))]


def assess_uncertainty(*, sample_size: int | None = None, missing_percent: float | None = None, validation_score: float | None = None, interval_available: bool = False) -> dict[str, Any]:
    """Create transparent caveats from known diagnostics without inventing confidence."""
    notes = []
    if sample_size is not None:
        if sample_size < 1:
            notes.append("No usable observations are available; conclusions cannot be supported.")
        elif sample_size < 30:
            notes.append("The sample is small; estimates may be unstable and sensitive to individual observations.")
    if missing_percent is not None:
        if not 0 <= missing_percent <= 100:
            raise ValueError("missing_percent must be between 0 and 100.")
        if missing_percent > 0:
            notes.append(f"{missing_percent:.1f}% of values are missing; results may depend on how missingness is handled.")
    if validation_score is not None:
        notes.append("A validation score was supplied; interpret it using its metric, baseline, split design and task context.")
    else:
        notes.append("No validation metric was supplied, so predictive reliability has not been quantified here.")
    if not interval_available:
        notes.append("No prediction or confidence interval is available; a point estimate alone does not show uncertainty.")
    return {"notes": notes, "evidence_inputs": {"sample_size": sample_size, "missing_percent": missing_percent, "validation_score": validation_score, "interval_available": bool(interval_available)}, "confidence_percent": None}
