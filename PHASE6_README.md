# PredictAI Phase 6 — Full Integrated Build

Phase 6 integrates the Cloudflare Workers AI Llama client, natural-language analysis, deterministic dataset statistics, live news retrieval, evidence-grounded summaries, news-informed scenario analysis, multi-file compatibility checks, opt-in persistent local document retrieval, and the existing Exam Intelligence workspace.

## Included capabilities

- **Two-workspace navigation:** Core Analysis and Exam Intelligence.
- **Cloudflare AI client:** `cloudflare_ai.py` uses Workers AI REST API. The default model identifier is `@cf/meta/llama-3.3-70b-instruct-fp8-fast`; override it using `CLOUDFLARE_MODEL` if the account's enabled model identifier differs.
- **AI Analyst:** sends a bounded JSON evidence package containing Python-computed dataset results, an analysis plan, document passages, and optionally retrieved news to Llama. The system prompt explicitly prohibits invented values/citations.
- **World Intelligence:** retrieves dated headline/snippet results from Google News RSS, links to each result, and asks Llama to summarise only supplied feed data. It does not claim to have read the full articles.
- **Forecasting:** linear-trend and last-value baselines, chronological holdout MAE/RMSE where enough rows exist, plus a separate user-controlled news-informed scenario. The scenario is not represented as a validated news-augmented ML model.
- **Multi-file analysis:** profiles files, shows common columns, lets the user explicitly confirm semantics/units before stacking compatible tables, and exports a combined CSV.
- **Persistent local knowledge:** opt-in SQLite passage index at `~/.predictai/knowledge.db`. This is retrieval, not model training. The UI includes search and clear-index controls.
- **Exam Intelligence:** existing workspace retained; its model calls now use Cloudflare Workers AI.
- **Existing capabilities:** prior data-analysis, document extraction, AutoML, report/export, and core numerical forecasting modules are retained.

## Setup on macOS

1. Make a backup of your working folder first.
2. Copy the ZIP contents into `~/Downloads/PredictAI_Phase1` (instructions below).
3. In the project folder, create a `.env` file containing:

```env
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_workers_ai_api_token
CLOUDFLARE_MODEL=@cf/meta/llama-3.3-70b-instruct-fp8-fast
```

Use a Cloudflare API token with Workers AI permissions. Never paste the real token into source code, commit it, or share it. `.gitignore` excludes `.env`.

4. Install requirements in the existing virtual environment:

```bash
cd ~/Downloads/PredictAI_Phase1
source .venv/bin/activate
pip install -r requirements.txt
```

5. Run tests and start the app:

```bash
python -m pytest -q
streamlit run app.py
```

## Safe install from the Phase 6 ZIP

The ZIP has a single top-level `PredictAI_Phase6` directory. Back up the project before copying files over it. Do not overwrite your `.env` or virtual environment.

```bash
cd ~/Downloads
cp -R PredictAI_Phase1 PredictAI_Phase1_backup_before_phase6
unzip -o PredictAI_Phase6_Complete.zip -d PredictAI_Phase6_Complete
cp -R PredictAI_Phase6_Complete/PredictAI_Phase6/. PredictAI_Phase1/
cd ~/Downloads/PredictAI_Phase1
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

## Important limitations

- Google News RSS provides headlines, source names, publication dates, and snippets; full articles may be paywalled, unavailable, or materially different from snippets. Verify important claims in the original source.
- Live news retrieval requires internet access. It does not require an API key, but availability and provider behaviour may change.
- News-informed scenarios are contextual what-if analyses. A credible test that news improves predictive accuracy requires a historical news dataset aligned to forecast cut-off dates and leakage-free backtesting. This build does not pretend that a slider-adjusted scenario is a validated news model.
- Forecasting uses simple linear-trend and last-value baselines; it is not intended to replace task-specific time-series validation or domain expertise.
- Persistent knowledge storage is local and opt-in. It uses lexical matching and can miss semantically related passages. Clear the index in the UI to delete its stored document passages.
- Llama output is generated text and can still be wrong. The app supplies evidence and instructs the model not to invent citations, but users should verify important conclusions.
- Check Cloudflare's current model availability, quota, and billing in the account dashboard. Quotas and model identifiers can change.
