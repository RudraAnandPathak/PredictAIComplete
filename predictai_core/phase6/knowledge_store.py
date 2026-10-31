"""Local, opt-in SQLite knowledge store for uploaded document passages."""
from __future__ import annotations
import hashlib
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

DEFAULT_DB = Path.home() / ".predictai" / "knowledge.db"
_STOPWORDS = {"the", "and", "for", "that", "with", "this", "from", "what", "when", "where", "which", "would", "could", "should", "about", "have", "has", "are", "was", "were", "into", "your", "you", "does", "did", "can", "will", "why", "how"}


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path).expanduser() if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, name TEXT NOT NULL, content_hash TEXT NOT NULL UNIQUE, indexed_at TEXT NOT NULL)")
    con.execute("CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, document_id INTEGER NOT NULL, chunk_index INTEGER NOT NULL, text TEXT NOT NULL, FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE)")
    con.execute("PRAGMA foreign_keys = ON")
    return con


def index_documents(documents: list[dict[str, Any]], db_path: str | Path | None = None) -> dict[str, int]:
    """Explicitly index extracted document text locally; same content hash is not duplicated."""
    indexed = skipped = chunks_added = 0
    with _connect(db_path) as con:
        for doc in documents:
            name, text = str(doc.get("name", "Untitled document")), str(doc.get("text", "")).strip()
            if not text:
                skipped += 1
                continue
            digest = hashlib.sha256((name + "\0" + text).encode("utf-8", errors="replace")).hexdigest()
            if con.execute("SELECT 1 FROM documents WHERE content_hash = ?", (digest,)).fetchone():
                skipped += 1
                continue
            cur = con.execute("INSERT INTO documents(name, content_hash, indexed_at) VALUES (?, ?, ?)", (name, digest, datetime.now(timezone.utc).isoformat()))
            doc_id = cur.lastrowid
            chunks = [p.strip() for p in re.split(r"\n\s*\n|(?<=[.!?])\s+", text) if p.strip()]
            for i, chunk in enumerate(chunks):
                con.execute("INSERT INTO chunks(document_id, chunk_index, text) VALUES (?, ?, ?)", (doc_id, i, chunk[:6000]))
                chunks_added += 1
            indexed += 1
    return {"documents_indexed": indexed, "documents_skipped_existing_or_empty": skipped, "chunks_added": chunks_added}


def search_knowledge(question: str, top_k: int = 8, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    terms = {t for t in re.findall(r"[a-z0-9]{3,}", (question or "").lower()) if t not in _STOPWORDS}
    if not terms:
        return []
    hits = []
    with _connect(db_path) as con:
        rows = con.execute("SELECT d.name, d.indexed_at, c.chunk_index, c.text FROM chunks c JOIN documents d ON d.id=c.document_id").fetchall()
    for name, indexed_at, chunk_index, text in rows:
        words = set(re.findall(r"[a-z0-9]{3,}", text.lower()))
        overlap = terms & words
        if overlap:
            hits.append({"source": name, "indexed_at": indexed_at, "chunk_index": chunk_index, "matched_terms": sorted(overlap), "score": round(len(overlap) / len(terms), 3), "evidence": text[:1800]})
    hits.sort(key=lambda x: (x["score"], len(x["matched_terms"]), len(x["evidence"])), reverse=True)
    return hits[:max(1, min(int(top_k), 30))]


def knowledge_stats(db_path: str | Path | None = None) -> dict[str, int]:
    with _connect(db_path) as con:
        docs = con.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunks = con.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return {"documents": int(docs), "chunks": int(chunks)}


def clear_knowledge(db_path: str | Path | None = None) -> None:
    with _connect(db_path) as con:
        con.execute("DELETE FROM chunks")
        con.execute("DELETE FROM documents")
