# PredictAI Phase 8 — Clear Explanations & Accounts

Phase 8 builds on Phase 7 while retaining Core Analysis and Exam Intelligence.

## What's new

- **Intelligent Explanation Layer:** plain-English interpretations for AutoML metrics, exploratory root-cause results, what-if predictions, and analysis plans. It distinguishes observations from interpretations and repeatedly warns that association is not causation.
- **Phase 7 UI improvements:** readable explanations appear alongside raw values for model evaluation, root-cause exploration, scenario prediction, and reasoning plans. Raw results remain available for transparency.
- **Local accounts:** account registration and sign-in, salted PBKDF2 password hashes, SQLite storage, password confirmation, and persistent special-access status after a one-time special code is entered during registration.
- **Special code configuration:** set `PREDICTAI_SPECIAL_ACCESS_CODE` in `.env`. Use a long random secret and keep `.env` private. If the variable is unset, no registration can receive special access.

## Install and run (macOS)

```bash
cd ~/Downloads/PredictAI_Phase8
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pytest
# If you do not already have a .env file, copy .env.example to .env.
# Edit .env privately; configure Cloudflare credentials and an optional special-access code.
streamlit run app.py
```

To test:

```bash
python -m pytest -q
```

## Account behaviour

- New users register with a username and password of at least 10 characters.
- Users sign in with the same account on this local installation; account records live by default at `~/.predictai/accounts.db`.
- Special access is stored with the account and remains after sign-out/sign-in. It is a permission flag only; the Phase 9 owner-only analytics dashboard is not part of this phase.
- Account database location can be overridden with `PREDICTAI_ACCOUNTS_DB`.

## Important deployment limitations

This account implementation is intended for local evaluation, not as a hardened public multi-user authentication service. Before public deployment, replace it with a managed identity provider, HTTPS, rate limiting, CSRF/session hardening, secure server-side secret storage, and a proper authorization model. Do not expose a development Streamlit server directly to the public internet.

## Explanation limits

The explanation layer uses deterministic templates and known output structures; it does not invent unsupported findings or claim that association proves causation. Unknown output fields are displayed as observations and should be checked against the raw result. Model quality still depends on the data, validation setup, and appropriate baselines.


Phase 9 adds the Owner Command Center and usage monitoring; see `PHASE9_README.md`.
