# PredictAI Phase 5 — Updated UI

## Main navigation
The sidebar now has only two workspaces: **Core Analysis** and **Exam Intelligence**.

## Core Analysis
- Keeps the existing Phase 1–4 analysis workflows.
- Adds **Forecast Numerical Values** for CSV/Excel datasets, numeric tables extracted from PDFs, or manually entered historical values.
- Forecasting requires ordered historical values. PDF table extraction is best-effort; scanned or complex tables may need OCR or manual checking.
- The floating assistant button uses a robot emoji instead of a purple heart.

## Exam Intelligence
- Exam Forecasting: analyse previous papers, paste the current syllabus and exam pattern, rank likely revision topics with evidence, and generate a full current-year forecast practice paper plus answer key using local Ollama. This is a study aid, not a guarantee of actual exam questions.
- Pattern Discovery: inspect missing values, numeric correlations, and potential outliers in CSV/Excel datasets.
- Ask Anything About Documents: upload PDFs, Word files, or text files, ask a natural-language question, and get an answer grounded in matching passages. The local Ollama model must be running for generated answers.

## Install on macOS
Back up the current project first. Extract this ZIP and copy its contents into the project directory, then run the tests.

```bash
cd ~/Downloads
cp -R PredictAI_Phase1 PredictAI_Phase1_backup_before_phase5_ui_update
unzip -o PredictAI_Phase5_Complete.zip -d PredictAI_Phase5_Complete
cp -R PredictAI_Phase5_Complete/. PredictAI_Phase1/
cd ~/Downloads/PredictAI_Phase1
source .venv/bin/activate
python -m pytest -q
streamlit run app.py
```

Predictions are estimates, not guarantees. Review extracted PDF tables and forecast results before relying on them.
