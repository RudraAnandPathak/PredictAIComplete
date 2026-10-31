# Changelog

## PredictAI recovery and security correction

- Preserved the existing core analysis, AutoML, Phase 5–9, Phase 11, Cloudflare and optional Ollama workspaces.
- Replaced username-bound reusable owner setup with a one-time high-entropy bootstrap secret. Owner initialization is serialized in SQLite and permanently consumed after the first owner account is created.
- Kept owner privilege tied to the created account and to normal password authentication. Special-access invitations grant special access only and the owner can revoke that access.
- Kept the 12-character minimum password; email and full name are optional.
- Added a third owner bootstrap tab restricted to the configured owner username.
- Added owner checks to local user-list and analytics account operations.
- Updated setup guidance, configuration examples, and deployment limitations.
- Added a standalone setup guide and build verification record.
- Reworked authentication tests to cover one-time owner initialization and role separation.
