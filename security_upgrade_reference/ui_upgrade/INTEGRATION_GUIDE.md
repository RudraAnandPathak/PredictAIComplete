# Integration guide

## Back up first
Duplicate your current PredictAI folder and its data. Never experiment on the only working copy.

## Account store
The sample uses its own SQLite database. Your existing app may use JSON, another SQLite file, or another database. Adapt the helpers to the current store or perform a planned migration with backup and rollback. Avoid two competing user databases.

## Email address vs verification
The form requires an email address and checks its format. That does not prove mailbox ownership. New accounts remain `pending_verification` and cannot sign in until you add a real email verification flow. Use SMTP or a transactional email provider; create a random single-use token, store only its hash, set an expiry, send the code/link, and activate the account only after successful verification. Keep mail credentials in server-side secrets and add signup/verification rate limits.

## Owner setup
Registration always creates a Regular User. Do not trust roles submitted by a user. Provision the Owner through a one-time secure migration or adapt the code to your existing Owner identity. Every admin action must check the role server-side.

## Blocking
The helper changes account status and records an audit event. The production app must re-check status before every protected page/action, AI request, upload/download/export, and data access. If your app has separate API tokens or persistent sessions, revoke them as well. Check ownership for each user's documents, datasets, and history.

## UI theme
Import `apply_theme()` after `st.set_page_config()` in your existing app. Use `render_hero()` and `render_feature_cards()` selectively. Do not replace your app with `integration_example.py`; it is only a demonstration.

## Local test
In a copy of your project:
```bash
python -m pip install -r requirements-additions.txt
streamlit run integration_example.py
```
It is a scaffold, not production-ready. New registrations remain pending until email verification is implemented, and an Owner account must be provisioned securely.

## Production checklist
- Keep API keys in server-side environment variables/secrets; never commit them.
- Use HTTPS and optionally Cloudflare Access.
- Protect Owner Command Center and all administrative actions server-side.
- Test blocked users with old sessions, duplicate email/username, wrong passwords, non-owner admin attempts, cross-user data access, and AI quota bypass.
- Add password recovery, email-change verification, privacy/terms notices, backups, and restoration tests.
- Review existing code before deploying.
