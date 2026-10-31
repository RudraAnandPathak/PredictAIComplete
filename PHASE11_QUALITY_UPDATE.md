# Phase 11 exam-quality update

This update strengthens the exam generator, but AI-generated material still requires teacher review.

## What changed
- Extracted text is no longer silently truncated to 18,000 characters per file or 22,000 characters for the combined prompt.
- Long extracted source text is split into overlapping chunks; each chunk is sent through source analysis to preserve chapter scope, exact school instructions, formulas, units, measurements, exclusions, and assessment patterns. Chunk summaries are supplied to paper generation.
- The generation prompt explicitly requires every special instruction to be mapped in an `instruction_compliance_check`.
- “Very challenging” now explicitly means application, multi-step reasoning, data interpretation, evaluation, error analysis, and non-routine syllabus-grounded problems—not basic definition questions.
- Case-based questions are required to have a realistic stimulus, linked analytical subparts, and usable measurements/data with units when appropriate.
- Answer keys are required to include worked solutions and mark-aware marking points.
- Deterministic quality checks flag weak recall questions, missing case-based context, absent data/units where relevant, and missing instruction-compliance mapping. One correction pass asks the model to repair detected issues.
- Internal source-reading and repair calls are framed as follow-up turns so the logical exam-generation task should consume one daily task rather than one per internal call.

## Important limitations
- OCR quality depends on image clarity and Tesseract. Inspect and correct extracted text before generation.
- Large source sets require multiple AI calls and may hit provider rate/context limits; errors are surfaced rather than silently claiming every file was used.
- Automated checks are heuristics, not proof of factual correctness or perfect compliance. Review the question paper, answer key, calculations, syllabus coverage, and every item in the instruction-compliance check before use.
