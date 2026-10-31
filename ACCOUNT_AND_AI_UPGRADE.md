# PredictAI account, access and AI Analyst upgrade

## Account registration
- New accounts must provide a full legal name, a syntactically valid email address, a unique username, and a password of at least 12 characters. Duplicate email addresses are rejected.
- Existing accounts are preserved through additive SQLite migrations. Legacy accounts may have blank legal-name/email fields; their credentials are not reset.
- The local app collects email but does not send a verification email. Do not treat the address as verified.

## Owner account controls
- Owner Command Center shows usernames, legal names, email addresses, roles, access status, and creation time.
- Owner can block/unblock regular accounts and grant/revoke special access. The owner role is protected from these controls.
- Blocked users are rejected at authentication and an already-open session is rechecked against the database on the next Streamlit rerun.
- Back up `~/.predictai/accounts.db` before launching this version. Existing database fields are added in place.

## Stricter regular-user limits
- 2 distinct document uploads per account (based on recorded upload events).
- Maximum 10 MB per uploaded file.
- PDFs limited to 30 pages.
- 3 AI Analyst investigations per day. Owners and special-access accounts are exempt from these limits.
- These quotas currently cover document upload enforcement and the Phase 6 AI Analyst investigation button; they are not a universal rate limit on every AI feature. Public deployment should add centralized request quotas and rate limiting.

## AI Analyst data reading
- The AI Analyst parses uploaded supported documents and tables, runs Python-calculated summaries on every uploaded tabular dataset, and passes dataset schemas, summaries, retrieved document evidence, and optional retrieved news into the model context.
- Model responses are instructed to distinguish evidence from interpretation and not invent calculations or citations.

## Security caveats
- This is a local Streamlit application, not a full production identity system. There is no email verification, password-reset workflow, or independent security audit. Store the database and `.env` securely, keep secrets private, and test with a database backup first.
