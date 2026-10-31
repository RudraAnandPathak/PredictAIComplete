# PredictAI Secure Upgrade — integrated project bundle

This bundle is built from the `app.py` uploaded in this conversation. It integrates the user-management scaffold into that app rather than replacing the app with the scaffold's demo.

## Included
- Existing PredictAI document/dataset analysis, local Ollama assistant, and PDF/PowerPoint report generation from the supplied app.
- Sign-in using username or email; signup with full name, email, username, and confirmation.
- Password hashing with PBKDF2-HMAC-SHA256 (600,000 rounds), salted per password.
- Email verification via SMTP, random single-use token hashes, 30-minute expiry, and resend throttling.
- Persistent SQLite user records, account status re-checks on each Streamlit rerun, and logout.
- Owner-only account search, block/unblock, grant/revoke Special User access, usage dashboard, and audit log.
- Regular account quota of 3 unique documents; PDF documents over 100 pages are rejected. Special User and Owner accounts are not limited by these document caps.
- Usage counters for document uploads, questions, and AI successes/failures.
- Dark, responsive Streamlit UI theme.

## Important limits / security notes
- This is a local/staging-ready integration, not a security certification or a complete production SaaS. Test it before exposing it publicly.
- Email delivery requires real SMTP settings. No verification emails will be sent until `.env` is configured.
- The 100-page cap is enforced exactly for PDFs when `pypdf` can read them. DOCX page count is not reliably represented in the file format and is not enforced as an exact page count in this version.
- Password reset, email change, MFA, distributed rate limiting, CSRF protections for any separate API, and multi-tenant document/history storage permissions are not implemented here.
- Owner usage dashboards track recorded events in this app; they are not a tamper-proof forensic audit system.
- Never put `.env`, SMTP credentials, database files, or user uploads into a public repository.
- For public deployment, use HTTPS, managed secrets, backups, rate limiting, monitoring, and a reviewed database/deployment configuration.

## First run on macOS
See `INSTALL_MAC.md` for copy-paste Terminal commands. Keep your original project and safety backup untouched until all tests pass.
