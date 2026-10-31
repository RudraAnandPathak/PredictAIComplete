# PredictAI setup guide

## Requirements

- macOS, Windows, or Linux
- Python 3.11 or 3.12 recommended
- Internet access for dependency installation and optional cloud AI
- Tesseract OCR is optional and only needed for OCR on image based documents

## Install and launch

1. Extract the ZIP and open a terminal in the extracted `PredictAI` folder.
2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   On Windows PowerShell, use `.venv\Scripts\Activate.ps1` to activate it.

3. Install the Python packages:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`. To initialize the owner account, generate a random bootstrap secret and add it to `.env`:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

5. Start PredictAI:

   ```bash
   streamlit run app.py
   ```

6. Set `PREDICTAI_OWNER_USERNAME` to your one allowed owner username. Use the third **Special Owner Access Code** tab with that username, a password of at least 12 characters, and the bootstrap secret. Email and full name are optional. After setup, remove the secret from `.env`; owner sign-in always requires that password. Remote account services require their own server-side bootstrap implementation.

7. Sign in to grant or revoke special access in **Phase 9 — Owner Command Center**. Registration codes do not grant special or owner privileges.

## Optional integrations

- For Cloudflare Workers AI, enter the required account ID, API token and supported model in `.env`.
- For local AI, install Ollama separately and configure its URL and model as described in `.env.example` and `README.md`.
- For OCR on macOS, install Tesseract with `brew install tesseract`.

## Local account data and safety

By default, local accounts are stored in `~/.predictai/accounts.db`. Set `PREDICTAI_ACCOUNTS_DB` to choose another path. Keep `.env` and the account database private and back them up securely.

This application is intended for local evaluation. Do not expose the Streamlit development server directly to the public internet. Read the security and deployment limitations in `README.md` and `SECURITY_INTEGRATION_STATUS.md` before considering any hosted deployment.

## Verify the installation

Run the checks from the activated environment:

```bash
python -m pytest -q
python -m compileall -q app.py document_reader.py local_ai.py cloudflare_ai.py predictai_core
python healthcheck.py
```
