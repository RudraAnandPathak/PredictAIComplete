"""Heuristic exam-paper analysis. Outputs are study aids, not guaranteed predictions."""
from __future__ import annotations
import re
from collections import Counter
from typing import Iterable

STOPWORDS = set("a an and are as at be been being by for from has have he her hers him his i in into is it its of on or our she that the their them they this to was were will with we you your not but if than then also can may might should would could about over under per each any all more most such these there which who what when where why how based using used use data page table figure source result results report analysis document section total summary according example including within between across explain calculate find give state write following answer question questions marks mark each".split())
QUESTION_START = re.compile(r"(?im)^\s*(?:(?:Q(?:uestion)?\.?\s*)?\d{1,3}\s*[.)\]:-]|\([a-zA-Z0-9]+\))\s+(.+?)(?=^\s*(?:(?:Q(?:uestion)?\.?\s*)?\d{1,3}\s*[.)\]:-]|\([a-zA-Z0-9]+\))\s+|\Z)", re.S | re.M)
MARKS = re.compile(r"\[\s*(\d+)\s*marks?\s*\]|\(\s*(\d+)\s*marks?\s*\)|\b(\d+)\s+marks?\b", re.I)


def extract_questions(text: str) -> list[dict]:
    """Extract numbered question blocks using a transparent heuristic."""
    text = str(text or "").replace("\r", "\n")
    matches = list(QUESTION_START.finditer(text))
    questions = []
    for idx, match in enumerate(matches, start=1):
        block = re.sub(r"\s+", " ", match.group(0)).strip()
        marks_match = MARKS.search(block)
        marks = next((int(g) for g in marks_match.groups() if g), None) if marks_match else None
        clean = MARKS.sub("", block).strip()
        questions.append({"number": idx, "text": clean[:1500], "marks": marks, "word_count": len(clean.split())})
    if not questions and text.strip():
        # Keep a useful fallback for papers without consistent numbering.
        chunks = [x.strip() for x in re.split(r"\n\s*\n", text) if len(x.strip()) >= 35]
        questions = [{"number": i, "text": re.sub(r"\s+", " ", x)[:1500], "marks": None, "word_count": len(x.split())} for i, x in enumerate(chunks, 1) if i <= 200]
    return questions[:300]


def topic_counts(texts: Iterable[str], top_n: int = 25) -> list[dict]:
    counts = Counter()
    for text in texts:
        tokens = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", str(text).lower())
        counts.update(t for t in tokens if t not in STOPWORDS and not t.isdigit())
    return [{"topic_term": word, "mentions": count} for word, count in counts.most_common(max(1, top_n))]


def analyze_exam_collection(papers: Iterable[dict]) -> dict:
    papers = list(papers)
    all_questions = []
    per_paper = []
    for paper in papers:
        name, text = str(paper.get("name", "Paper")), str(paper.get("text", ""))
        questions = extract_questions(text)
        all_questions.extend([{**q, "paper": name} for q in questions])
        per_paper.append({"paper": name, "characters": len(text), "word_count": len(text.split()), "questions_detected": len(questions), "marks_detected": sum(q["marks"] or 0 for q in questions)})
    return {"paper_count": len(papers), "papers": per_paper, "question_count": len(all_questions), "questions": all_questions, "topic_terms": topic_counts([q["text"] for q in all_questions] or [p.get("text", "") for p in papers]), "limitations": ["Question extraction uses numbering/format heuristics; inspect the extracted questions.", "Keyword frequency is not proof a topic will appear again.", "The analysis cannot guarantee the contents of a future examination."]}


def generate_practice_paper(analysis: dict, count: int = 10) -> list[dict]:
    """Create a transparent practice set from historical question styles; no fabricated answer key."""
    questions = analysis.get("questions", [])
    count = max(1, min(int(count), 50))
    if not questions:
        return []
    # Prefer questions from different papers where possible, then rotate through source questions.
    selected, used = [], set()
    for q in questions:
        paper = q.get("paper")
        if paper not in used:
            selected.append(q); used.add(paper)
        if len(selected) >= count:
            break
    index = 0
    while len(selected) < min(count, len(questions)):
        q = questions[index % len(questions)]
        if q not in selected:
            selected.append(q)
        index += 1
    return [{"question_number": i + 1, "source_paper": q.get("paper", "Source paper"), "question": q["text"], "marks": q.get("marks"), "note": "Historical question selected for practice; not a prediction of the actual exam."} for i, q in enumerate(selected)]
