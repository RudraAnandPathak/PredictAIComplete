"""Small lexical evidence retrieval utility for document-grounded workflows."""
from __future__ import annotations
import re


def search_evidence(question: str, documents: list[dict], top_k: int = 5) -> list[dict]:
    terms = {t for t in re.findall(r"[A-Za-z0-9]{3,}", str(question).lower())}
    if not terms:
        return []
    hits = []
    for doc in documents:
        text = str(doc.get("text", ""))
        # Split into paragraph-sized chunks so results retain local context.
        chunks = [c.strip() for c in re.split(r"\n\s*\n|(?<=[.!?])\s+", text) if c.strip()]
        for idx, chunk in enumerate(chunks):
            words = set(re.findall(r"[A-Za-z0-9]{3,}", chunk.lower()))
            overlap = len(terms & words)
            if overlap:
                hits.append({"document": str(doc.get("name", "Document")), "chunk_index": idx, "score": overlap / len(terms), "evidence": chunk[:1200]})
    hits.sort(key=lambda x: (x["score"], len(x["evidence"])), reverse=True)
    return hits[:max(1, min(int(top_k), 20))]
