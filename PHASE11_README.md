# PredictAI Phase 11 — Exam Paper Generator

Phase 11 adds a teacher-oriented question-paper workflow to the existing PredictAI Phase 9 project. It keeps the previous workspaces and adds a new sidebar workspace.

## Features
- Enter board/class, subject, chapter names, maximum marks, duration, difficulty and question types.
- Add free-form special instructions (including exclusions, chapter weightage, internal-choice preferences and school format requirements).
- Upload syllabus photos (PNG/JPG/TIFF/BMP/WEBP) and documents (PDF/DOCX/TXT/MD/RTF). Regular accounts are limited to 5 materials per exam-generation request; Special Users and the Owner have no material-count limit.
- OCR image text locally with Tesseract, then review and correct the extracted text before sending it to Cloudflare Workers AI.
- Generate a structured practice question paper with answers and per-question marking points.
- Process long uploads in bounded chunks and hierarchically consolidate source evidence, avoiding a single oversized prompt. All extracted chunks are submitted for processing; summaries are consolidated to fit the model context window.
- Generate with a bounded output allowance and a smaller repair prompt to reduce Cloudflare 24,000-token context-window errors.
- Basic Python validation of the sum of question marks.
- Export the question paper and answer key/marking scheme to DOCX, PDF and Markdown.
- No source upload is required: teachers may enter chapter names and instructions only. In that case, the output is clearly not textbook-verified.

## Setup
1. Use the existing Phase 9 installation steps in `PHASE9_README.md`.
2. Preserve your own `.env` file; never distribute it or place API credentials in source code.
3. Install Python dependencies with `python -m pip install -r requirements.txt`.
4. For photo OCR on macOS, install the Tesseract executable: `brew install tesseract`. Pillow and pytesseract are installed from `requirements.txt`.
5. Start with `streamlit run app.py` and choose **Phase 11 — Exam Paper Generator** from the sidebar.

## Daily AI task limits
- Regular accounts get 3 new AI tasks per calendar day, shared across PredictAI workspaces.
- Follow-up questions in an existing AI conversation do not consume another task.
- Special Users and the Owner are exempt from this regular-user quota in this version. They also have no per-generation upload-count limit.
- The daily counter is stored in the same persistent SQLite account database and resets by date in `PREDICTAI_QUOTA_TIMEZONE` (defaults to `Asia/Kolkata`).
- Optional `.env` settings: `PREDICTAI_REGULAR_DAILY_TASK_LIMIT=3` and `PREDICTAI_QUOTA_TIMEZONE=Asia/Kolkata`.
- Only successful AI calls are charged; failed calls release their reserved slot. Exporting existing results and browsing workspaces do not call the AI and are not charged.

## How photo handling works
Images are OCR'd locally using Tesseract. The teacher sees the extracted text and can correct it before generation. The corrected text and typed exam specification are then sent to Cloudflare Workers AI when the teacher explicitly clicks Generate. A photo alone communicates the syllabus/requirements; it does not guarantee the model has the complete textbook content.

## Important limitations
- The system does not automatically guarantee that it can retrieve an official textbook from the internet. Uploaded content is the strongest grounding source. Without source material, generation uses the model's general knowledge and is not textbook-verified.
- The model response is parsed as JSON. If the model returns malformed JSON, generation will fail visibly rather than silently displaying a broken paper.
- The mark-total validator checks arithmetic only. It cannot guarantee factual accuracy, pedagogical quality, syllabus compliance, fairness, or official board compliance. A teacher must review every generated paper and answer key.
- OCR may misread blurry handwriting, tables, diagrams or low-quality photos. Review and correct extracted text.
- Tesseract must be installed separately as a system application; installing `pytesseract` alone is not sufficient.
- The application transmits the approved extracted text to Cloudflare Workers AI during generation. Do not upload confidential student data or documents without permission.
- This remains a local/testing application, not a hardened public multi-user deployment. Review authentication, storage, rate limits, privacy and access controls before public release.

## Large-source / context-window handling
- The source processor divides extracted content into overlapping chunks, sends every chunk through source-evidence extraction, and consolidates summaries in bounded batches. The final generation prompt includes the consolidated brief once (not duplicated as both an assistant message and user prompt).
- Generation and repair requests use bounded output tokens. This substantially reduces the chance of exceeding the configured model context window, but it cannot override Cloudflare/model limits, and very large or complex papers may still need to be generated with smaller mark totals or fewer output sections.
- Consolidation is lossy by nature: the model is instructed to preserve every unique instruction, exclusion, formula, measurement and unit, but teachers must review the source brief and resulting paper. Do not treat automatic summaries as a guarantee that every source detail survives.
