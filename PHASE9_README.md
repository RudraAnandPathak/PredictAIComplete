# PredictAI Phase 9 — Owner Command Center

This package builds on Phase 8 and adds an owner-only dashboard, account role support,
special-access management, usage event summaries, and the Regular User document-count limit.

## Owner setup
1. Copy `.env.example` to `.env` only if you do not already have a `.env`; preserve existing Cloudflare credentials.
2. Set `PREDICTAI_OWNER_USERNAME` and a long private `PREDICTAI_OWNER_SETUP_SECRET`.
3. Restart Streamlit. Register the configured username and enter the matching owner setup secret.
4. Only that first successful owner initialization is accepted. The special-access code never grants owner status.
5. Keep `.env` private and out of version control.

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
