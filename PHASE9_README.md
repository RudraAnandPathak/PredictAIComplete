# PredictAI Phase 9 — Owner Command Center

This package builds on Phase 8 and adds an owner-only dashboard, account role support,
special-access management, usage event summaries, and the Regular User document-count limit.

## Owner setup
1. Copy `.env.example` to `.env` only if you do not already have a `.env`; preserve existing Cloudflare credentials.
2. Set `PREDICTAI_OWNER_USERNAME` to the only username permitted to become owner.
3. Set `PREDICTAI_OWNER_SETUP_SECRET` to a random value generated from at least 32 bytes of entropy.
4. Restart Streamlit. Open the third **Special Owner Access Code** tab and initialize the configured username with a password and the one-time setup secret.
5. The database atomically consumes bootstrap after the first successful owner initialization. Remove the secret from `.env`; later accounts cannot claim owner. Special access is granted and revoked by the owner after account creation.
6. Keep `.env` private and out of version control.

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pytest
python -m pytest -q
streamlit run app.py
```

## Included Phase 9 work
- Owner-only Command Center page, gated by a server-side role check.
- Registered-user and special-user counts.
- Usage event tables for uploads, questions, reports, AI success/failure, logins and admin actions.
- Grant/revoke special access for non-owner accounts.
- Regular-account document-count limit of 3 and a 100-page check for PDF uploads.
- Event-history view and visible configuration status.

## Important implementation limits
- The dashboard only counts events recorded by instrumented application paths. Report and AI success/failure event instrumentation is not complete in every existing path, so those counters may remain zero until those paths are wired in.
- The 3-document cap is enforced in the main upload workflow; it uses application-recorded uploads. The 100-page check is enforced for PDFs. Page counting for DOCX and other file formats is not reliably implemented yet, so treat the page limit as fully enforced for PDFs only until parser-level checks are added for other formats.
- This is a local/testing implementation, not a hardened public multi-user deployment. Use a managed identity provider and server-side database, protect the app with HTTPS, and add rate limiting, CSRF/session protections, backups, and security review before public deployment.
- Account suspension, arbitrary platform setting edits, and detailed security event classification are not implemented as destructive controls; the dashboard exposes configuration status and records supported admin actions.
