# PredictAI Premium UI Upgrade

This update refreshes the Streamlit presentation with a premium dark-green editorial design, soft gradients, lime accent, rounded panels, clearer authentication layout, and a redesigned workspace hero. The style is inspired by the broad visual qualities of premium editorial landing pages, adapted for an AI analytics product rather than copied from the reference site.

## Install

1. Back up your current PredictAI folder and `~/.predictai/accounts.db`.
2. Extract this ZIP into a new folder.
3. Copy your existing `.env` into the extracted `PredictAI_Complete` folder. Do not share `.env`.
4. Create/activate the virtual environment and install requirements as described in `README.md`.
5. Run `python -m streamlit run app.py`.

## Scope and safety

- This is a UI redesign; it does not intentionally change the account schema or authentication flow.
- The local account database remains wherever `PREDICTAI_ACCOUNTS_DB` points, or at `~/.predictai/accounts.db` by default.
- Existing account/owner behavior has not been independently security-audited by this UI update.
- The design imports Google Fonts when network access is available and falls back to system fonts if not.
- Streamlit DOM selectors can vary between versions; inspect the UI after installing and report any layout issues.
- Do not expose Streamlit's development server directly to the public internet.
