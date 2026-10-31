# PredictAI User Management & UI Upgrade Pack

This is an integration scaffold, not a replacement for your current app.py. Merge it into a backup/copy of your current project to preserve existing AI features.

Includes:
- auth_security.py: email-format validation, password hashing, SQLite account helpers, active-session checks.
- user_management.py: account search/listing, Owner-only blocking/unblocking helpers, audit log.
- ui_theme.py: modern Streamlit theme and reusable dashboard components.
- integration_example.py: illustrative signup/login/Owner UI.
- INTEGRATION_GUIDE.md: important setup and security instructions.
- requirements-additions.txt

Important:
- Email format validation is not email verification. The sample keeps new accounts pending until you implement a real verification email flow.
- Do not overwrite your existing app.py with integration_example.py.
- Adapt these helpers to your existing account database and roles; avoid creating two competing user stores.
- Block status must be checked on every protected action, including AI requests and file access.
- Provision Owner securely; registration always assigns Regular User.
- Test in a backup/staging copy before deployment.
