from predictai_core.phase11_exam_paper import validate_paper, render_markdown, render_answer_markdown


def test_validate_paper_accepts_correct_mark_total():
    data = {"sections": [{"name": "Section A", "questions": [
        {"number": 1, "question": "What is 2+2?", "marks": 1, "answer": "4", "marking_points": ["Correct answer"]},
        {"number": 2, "question": "Explain photosynthesis.", "marks": 4, "answer": "Plants make food", "marking_points": ["Light", "Chlorophyll"]},
    ]}]}
    assert validate_paper(data, 5) == []


def test_validate_paper_flags_wrong_mark_total():
    data = {"sections": [{"name": "Section A", "questions": [{"number": 1, "question": "Q?", "marks": 2}]}]}
    assert any("not the requested 5" in issue for issue in validate_paper(data, 5))


def test_render_outputs_contain_question_and_answer():
    data = {"sections": [{"name": "Section A", "questions": [{"number": 1, "type": "MCQ", "question": "What is 2+2?", "marks": 1, "options": ["A. 3", "B. 4"], "answer": "B", "marking_points": ["1 mark for B"]}]}]}
    details = {"title": "Demo", "class_board": "Class 5", "subject": "Maths", "duration": "1 hour", "marks": 1}
    assert "What is 2+2?" in render_markdown(data, details)
    assert "1 mark for B" in render_answer_markdown(data, details)


def test_source_chunking_preserves_full_text_with_overlap():
    from predictai_core.phase11_exam_paper import _chunk_source_materials
    source = ("Important syllabus line with a formula and units.\n" * 500)
    chunks = _chunk_source_materials(source, chunk_chars=1000)
    assert len(chunks) > 1
    # Each chunk retains content; overlap is intentional to avoid cutting context.
    assert all(chunk.strip() for chunk in chunks)
    assert "formula and units" in " ".join(chunks)


def test_quality_check_flags_missing_case_based_context():
    from predictai_core.phase11_exam_paper import validate_quality
    data = {"sections": [{"questions": [{"number": 1, "type": "Case-based", "question": "What is the function of a plant?", "marks": 2}]}]}
    issues = validate_quality(data, "Very challenging", ["Case-based"], "Include a case study", "source")
    assert any("substantial real-world context" in issue for issue in issues)


def test_quality_check_flags_definition_prompts_for_very_challenging():
    from predictai_core.phase11_exam_paper import validate_quality
    data = {"sections": [{"questions": [
        {"number": 1, "type": "Very short answer", "question": "What is the use of photosynthesis?", "marks": 1},
        {"number": 2, "type": "Very short answer", "question": "What is the function of chlorophyll?", "marks": 1},
        {"number": 3, "type": "Long answer", "question": "Analyse the experimental results in the table and explain the trend at 25 °C.", "marks": 5},
    ]}]}
    issues = validate_quality(data, "Very challenging", ["Long answer", "Case-based"], "", "source")
    assert any("basic recall/definition" in issue for issue in issues)


def test_source_brief_processes_all_chunks(monkeypatch):
    from predictai_core import phase11_exam_paper as p11
    seen = []

    def fake_chat(messages, temperature=0.2, max_tokens=900, timeout=90):
        seen.append(messages[-1]["content"])
        return "Preserved evidence: Chapter A; 12 cm; exclude topic Z."

    monkeypatch.setattr(p11, "chat_with_cloudflare", fake_chat)
    source = "\n\n".join([f"Material section {i}. Formula and measurement: {i} cm." for i in range(1, 250)])
    brief = p11._build_source_brief(source)
    assert len(seen) >= 2
    assert "Preserved evidence" in brief
    assert all("Inspect source chunk" in item or "Consolidate this group" in item or "Create a source evidence brief" in item for item in seen)


def test_source_chunking_keeps_end_of_long_source():
    from predictai_core.phase11_exam_paper import _chunk_source_materials
    source = "START " + ("ordinary content " * 1200) + " END_MARKER"
    chunks = _chunk_source_materials(source, chunk_chars=5000)
    assert len(chunks) > 1
    assert any("START" in chunk for chunk in chunks)
    assert any("END_MARKER" in chunk for chunk in chunks)
