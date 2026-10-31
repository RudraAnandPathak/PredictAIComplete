"""Normalize uploaded text/document content for Phase 5 analysis."""
from __future__ import annotations
import re
from typing import Iterable, Any


def normalize_text(text: str) -> str:
    text = str(text or "").replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def collect_document_text(documents: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Accept records with name and text; return normalized, non-empty records."""
    result = []
    for item in documents:
        name = str(item.get("name") or "Untitled document")
        text = normalize_text(item.get("text", ""))
        if text:
            result.append({"name": name, "text": text, "characters": len(text), "words": len(text.split())})
    return result
