# Security integration status

The active application uses `predictai_core.phase8.accounts` sign-in/registration and `predictai_core.phase9.admin` owner dashboard. The separate security bundle remains preserved in `security_upgrade_reference/`; it is not imported into the active application.

The active local account flow hashes passwords with PBKDF2, grants one owner through a one-time bootstrap secret, and stores revocable special access separately. Owner-only user and analytics operations confirm the role against the local account database. Owner bootstrap is consumed atomically and is tied to the account created with it.

The app remains for local evaluation. Before public deployment, use a managed identity provider and a server-side account service that independently verifies roles, owner initialization and special-access changes. Add HTTPS, rate limiting, session protections, database isolation, secret management, backups and a security review. Do not treat client supplied role data or the shared account-service API token as user authentication.
