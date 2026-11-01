# Security integration status

The active application currently uses the recovered `predictai_core.phase8.accounts` sign-in/registration and `predictai_core.phase9.admin` owner dashboard. The separate `PredictAI_Secure_Upgrade_Bundle` and `PredictAI_User_Management_UI_Upgrade` have been preserved in `security_upgrade_reference/` so their code is not lost.

They are not activated by this recovery build because the security bundle's authentication/session API is different from the Phase 8 account gate. Blindly copying `auth_security.py` and `user_management.py` would not automatically integrate email verification, user blocking, or audit logging into every existing workspace. A deliberate adapter and tests are required.

Before public deployment, integrate and test the desired protections, including email verification, blocking/status enforcement at every protected action, authorization on the server side, rate limiting, secure cookie/session handling appropriate to the hosting platform, secret management, data isolation, backups, and HTTPS. This package is for local evaluation, not public production hosting.
