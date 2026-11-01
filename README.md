# PredictAI Complete — Recovery Build

A recovered local Streamlit application assembled from the supplied PredictAI Phase 1–11 archives. This package uses the Phase 11 unlimited-special-context recovery archive as its base, preserving the integrated Phase 1–9 workspaces and the Phase 11 exam-paper generator, with its quality and long-source handling updates.

> **Status:** Recovery build with Cloudflare D1 account support. The test suite passes locally; the Worker still needs deployment and credential configuration in your Cloudflare and Streamlit accounts. Tests do not connect to your live Cloudflare database or AI credentials.

## Included workspaces and modules

- Core document and dataset analysis
- Document extraction for supported PDF, Word, spreadsheet, CSV and text formats (actual support depends on parser and file structure)
- AutoML and evaluation
- Phase 5 Exam Intelligence, evidence, patterns and exam forecasting
- Phase 6 AI Analyst/World Intelligence, evidence tools, numerical forecasting and local document knowledge store
- Phase 7 reasoning, modelling lab, root-cause exploration, research and unified reports
- Phase 8 explanations and persistent Cloudflare D1 accounts through an authenticated Worker API (local SQLite is opt-in development only)
- Phase 9 owner command centre and usage monitoring
- Phase 11 exam paper generator, source-material chunking, quality heuristics and DOCX/PDF/Markdown exports
- Cloudflare Workers AI and optional local Ollama integration
- Original security-upgrade bundle files preserved under `security_upgrade_reference/` for review; they are **not silently spliced into the active login flow**, because their API differs from the recovered Phase 8–9 account system.

## Quick start (macOS)

1. Install Python 3.11 or 3.12 (recommended). Some dependencies may lag behind the newest Python release.
2. Install the Tesseract OCR system tool if you want image/syllabus OCR:

   ```bash
   brew install tesseract
   ```

3. In Terminal, enter this folder and create the environment:

   ```bash
   cd /path/to/PredictAI_Complete
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   cp .env.example .env
   ```

4. Open `.env` in a text editor and configure the Cloudflare values if you want cloud AI. Keep `.env` private. Do not send API tokens or owner secrets in chat.
5. Launch:

   ```bash
   streamlit run app.py
   ```

Streamlit normally opens the local app in your browser at `http://localhost:8501`.

### One-step setup and launch

Double-click `setup_and_launch_mac.command` (or run `./setup_and_launch_mac.command` in Terminal). It creates a project-local `.venv`, installs requirements, creates `.env` from the safe template if needed, and launches Streamlit. The first run may take several minutes. It does not change your system Python.

After setup, you can use `./launch_mac.command` for later launches.

## First account and owner setup

- Create a regular account in the app's sign-in screen.
- Production account storage must use Cloudflare D1. Follow [CLOUDFLARE_D1_SETUP.md](CLOUDFLARE_D1_SETUP.md); Streamlit Community Cloud must use `PREDICTAI_ACCOUNT_MODE="remote"` and keep the Worker API token only in Streamlit Secrets.
- Owner initialization is a one-time operation verified by the Worker. Special-user code is separate and cannot grant owner privileges.
- Local SQLite is available only after explicitly setting `PREDICTAI_ACCOUNT_MODE=local` for development. It is not suitable for Streamlit Community Cloud.

## Cloudflare AI configuration

The `.env.example` file lists the supported environment variable names. Use a Cloudflare account ID, a token with only the required Workers AI permissions, and a model identifier supported by your account. Leave credentials unset if you don't want to use cloud AI. Cloud AI features will not work until configured.

## Local Ollama option

Install Ollama separately and download a model you have enough disk/RAM to run. The app supports `PREDICTAI_OLLAMA_URL` and `PREDICTAI_OLLAMA_MODEL` where the local AI module uses them. Cloudflare-dependent workflows still require Cloudflare configuration; installing Ollama does not replace every cloud workflow.

## Tests and diagnostics

```bash
source .venv/bin/activate
python -m pytest -q
python -m compileall -q app.py document_reader.py local_ai.py cloudflare_ai.py predictai_core
python healthcheck.py
```

The package test suite currently contains 69 passing tests. Re-run it after installation; package versions and system tools can differ.

## Recovery and safety notes

- This build was assembled from the uploaded recovery archive; original archives are not modified.
- `security_upgrade_reference/` preserves the separate email-verification/user-management bundle for further integration work. It is intentionally labelled reference code, not active authentication.
- See [CLOUDFLARE_D1_SETUP.md](CLOUDFLARE_D1_SETUP.md) for persistent account deployment. The Worker requires a bearer token held in Streamlit server secrets; the browser does not access D1 or receive the token.
- Before public launch, arrange HTTPS and a reverse proxy/hosting platform, managed identity or a security-reviewed auth implementation, database isolation, rate limiting, secure secret storage, backups, privacy terms, monitoring and a security review.
- AI-generated forecasts, explanations, exam questions and answer keys can be wrong. Verify important outputs and review generated exam materials with a teacher.
- News retrieval and cloud AI require network access and valid configuration. No API credentials are bundled.

## Folder map

- `app.py` — Streamlit entry point
- `predictai_core/` — analysis engines and Phase 5–11 modules
- `tests/` — recovered automated tests
- `cloudflare/worker/` — D1 migration, Worker source, and Wrangler configuration
- `CLOUDFLARE_D1_SETUP.md` — Cloudflare deployment and Streamlit configuration steps
- `security_upgrade_reference/` — preserved but not yet integrated security bundle
- `.env.example` — safe configuration template
- `setup_and_launch_mac.command` — first-run setup and launcher
- `launch_mac.command` — subsequent launcher
- `healthcheck.py` — dependency/configuration diagnostics
