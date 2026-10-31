# PredictAI Phase 7 — Intelligence Engine & Unified Reports

This package extends the Phase 6 project with a separate Phase 7 workspace. Existing Core Analysis and Exam Intelligence workspaces remain available.

## Included modules

- **Advanced Reasoning:** transparent decomposition of an analytical question into smaller tasks and guardrails.
- **Predictive Modelling Lab:** reuses the existing AutoML engine for held-out evaluation, cross-validation, model comparisons, feature importance and cautions.
- **Root Cause Analysis:** descriptive group comparisons and numeric associations. It explicitly does not claim causal identification.
- **What-If Simulator:** fits a separate predictive scenario model and lets the user inspect predictions under changed feature values. This is not a causal intervention model.
- **Research & Report Engine:** bundles evidence supplied by the user, assembles selected analytical outputs, runs basic report quality checks, and exports TXT, PDF, Word, and PowerPoint.

## Install and run on macOS

```bash
cd PredictAI_Phase7
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env  # optional; configure credentials only if needed by existing features
streamlit run app.py
```

Choose **Phase 7 — Intelligence & Reports** in the sidebar. Upload a CSV or Excel file to use dataset-based modules.

## Tests

```bash
python -m pytest -q
```

## Important implementation notes

- This is an initial Phase 7 integration, not a claim that every proposed future capability is complete.
- The research bundle does not pretend to search or verify the public web; external sources must be explicitly retrieved and supplied by a connected provider.
- The scenario simulator's model is separately fitted and can differ from the best model in the AutoML leaderboard. It is intended for exploratory predictions only.
- The report quality checker catches common omissions; it does not certify factual accuracy.
- No credentials are included in the ZIP. Keep `.env` local and never share API keys.
