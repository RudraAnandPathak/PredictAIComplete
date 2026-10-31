# PredictAI Complete — Recovery Build

A recovered local Streamlit application assembled from the supplied PredictAI Phase 1–11 archives. This package uses the Phase 11 unlimited-special-context recovery archive as its base, preserving the integrated Phase 1–9 workspaces and the Phase 11 exam-paper generator, with its quality and long-source handling updates.

> **Status:** Recovery build for local evaluation. The included automated test suite passes in the build environment (63 tests). This is not a claim that every feature has been tested against live Cloudflare/Ollama credentials or is safe for public production deployment.

## Included workspaces and modules

- Core document and dataset analysis
- Document extraction for supported PDF, Word, spreadsheet, CSV and text formats (actual support depends on parser and file structure)
- AutoML and evaluation
- Phase 5 Exam Intelligence, evidence, patterns and exam forecasting
- Phase 6 AI Analyst/World Intelligence, evidence tools, numerical forecasting and local document knowledge store
- Phase 7 reasoning, modelling lab, root-cause exploration, research and unified reports
- Phase 8 explanations and local SQLite accounts
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

- Copy `.env.example` to `.env`, set `PREDICTAI_OWNER_USERNAME` to the only permitted owner username, and set `PREDICTAI_OWNER_SETUP_SECRET` to a one-time secret generated from at least 32 random bytes (the example command in `.env.example` generates one).
- Create regular accounts with username and password; email and full name are optional. Initialize the owner through the third **Special Owner Access Code** tab using the configured username, a password, and the bootstrap secret. The secret initializes only that account and is not a login credential. Owner sign-in always requires the password. Remote account services must implement owner bootstrap server-side before owner setup can be used in remote mode.
- The database atomically records that owner initialization has been consumed. Remove the secret from `.env` after successful setup. A later account cannot claim ownership, even if the secret is accidentally retained.
- Special access is granted and revoked by the authenticated owner in the command center. Registration codes cannot grant elevated access.
- Account records are stored locally, by default at `~/.predictai/accounts.db`; `PREDICTAI_ACCOUNTS_DB` can override the path.
- If you previously used another PredictAI folder, this build may not automatically use its database. Back up any existing database before changing configuration.

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

The recovered suite passed **63 tests** during packaging. Re-run the tests on your Mac after installation; package versions and system tools can differ.

## Recovery and safety notes

- This build is based on the public PredictAI repository and preserves its existing workspace modules.
- `security_upgrade_reference/` preserves the separate email-verification/user-management bundle for further integration work. It is intentionally labelled reference code, not active authentication.
- The active Phase 8 account system hashes passwords with PBKDF2 and stores local account data in SQLite. Streamlit's session model and this local account service are intended for local evaluation, not public multi-user hosting. Do not expose the Streamlit development server directly to the public internet.
- In Cloudflare account-service mode, the remote service must independently implement the same one-time owner initialization, authenticated actor checks, password hashing, special-access revocation, and rate limits. The client-side `role` field is not a security boundary for a public deployment.
- Before public launch, arrange HTTPS and a reverse proxy/hosting platform, managed identity or a security-reviewed auth implementation, database isolation, rate limiting, secure secret storage, backups, privacy terms, monitoring and a security review.
- AI-generated forecasts, explanations, exam questions and answer keys can be wrong. Verify important outputs and review generated exam materials with a teacher.
- News retrieval and cloud AI require network access and valid configuration. No API credentials are bundled.

## Folder map

- `app.py` — Streamlit entry point
- `predictai_core/` — analysis engines and Phase 5–11 modules
- `tests/` — recovered automated tests
- `security_upgrade_reference/` — preserved but not yet integrated security bundle
- `.env.example` — safe configuration template
- `setup_and_launch_mac.command` — first-run setup and launcher
- `launch_mac.command` — subsequent launcher
- `healthcheck.py` — dependency/configuration diagnostics
