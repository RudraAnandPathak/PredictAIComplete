# Persistent account storage with Cloudflare D1

PredictAI's Streamlit server sends account requests to a private authenticated Cloudflare Worker. The Worker uses its D1 binding for every account read and write. Passwords are PBKDF2-SHA-256 hashes with per-user random salts; the Worker never stores the password, owner setup secret, or special access code. `PREDICTAI_ACCOUNT_MODE` defaults to `remote`, and account operations fail closed if the API is unavailable or not configured. Local SQLite is available only after explicitly setting `PREDICTAI_ACCOUNT_MODE=local` for development.

## 1. Install Wrangler and create the D1 database

Use Node.js 20 or newer and authenticate Wrangler to the Cloudflare account that will host the Worker:

```sh
npm install --global wrangler
wrangler login
cd cloudflare/worker
wrangler d1 create predictai-accounts
```

Copy the returned database UUID into `cloudflare/worker/wrangler.toml`, replacing `REPLACE_WITH_DATABASE_ID`.

## 2. Apply the initial schema

From `cloudflare/worker` run:

```sh
wrangler d1 migrations apply predictai-accounts --remote
```

The migration creates account, one-time owner state, usage event, and daily task tables and indexes. It does not contain credentials or seed an owner.

## 3. Configure Worker secrets and owner identity

Generate long random values locally. Do not put them in source control, this guide, or a browser bundle. Set the configured owner username as a regular Worker variable and the codes/token as Worker secrets:

```sh
wrangler secret put API_TOKEN
wrangler secret put OWNER_SETUP_SECRET
wrangler secret put SPECIAL_ACCESS_CODE
wrangler secret put OWNER_USERNAME
```

When prompted, provide a distinct random bearer token, a distinct one-time owner setup secret, a separate optional special-user code, and the intended owner username. The owner username is a secret here because it is submitted as an initialization target. `OWNER_SETUP_SECRET` is accepted only for that exact username. Owner initialization is guarded by both the persistent `owner_state` row and the unique role check, so later attempts cannot create a second owner. Special access only grants the special-user flag and never grants owner role.

## 4. Deploy the Worker

```sh
wrangler deploy
```

Wrangler prints a URL such as `https://predictai-accounts.<your-subdomain>.workers.dev`. The Streamlit API URL is that Worker root URL without an appended path. Each request uses HTTPS POST and the server adds the bearer token; requests from browser JavaScript are not part of this design. Keep Cloudflare's Worker secrets private and do not enable permissive CORS.

## 5. Configure Streamlit Community Cloud secrets

In the deployed app's **Settings → Secrets**, add:

```toml
PREDICTAI_ACCOUNT_MODE = "remote"
PREDICTAI_API_URL = "https://predictai-accounts.YOUR-SUBDOMAIN.workers.dev"
PREDICTAI_API_TOKEN = "the-same-random-value-entered-for-Worker-API_TOKEN"
```

Replace the URL and token with your actual values. The API token belongs only in Streamlit server secrets and the Worker secret store. Never include it in `app.py`, `st.markdown` HTML/JavaScript, query strings, screenshots, or a committed `.env` file. Restart/reboot the Streamlit app after saving secrets.

## 6. Initialize the one owner account

In the deployed PredictAI app, create the account with the configured owner username and the one-time `OWNER_SETUP_SECRET` in the **Owner setup secret** field. Do not enter the special access code for this account. The Worker verifies it and atomically creates the only owner record. After that, owner setup attempts are rejected. Do not reuse the owner setup secret as `API_TOKEN` or `SPECIAL_ACCESS_CODE`.

For a normal user, create an account with username/password. An optional special access code grants only special access. An owner can later grant or revoke special access in the Owner Command Center. Existing lost accounts cannot be recovered from an ephemeral SQLite database; users whose records are gone need to register again after D1 is deployed.

## Local development

To intentionally use the local SQLite account store, set `PREDICTAI_ACCOUNT_MODE=local` in a private `.env` file and run the app locally. This path is for development only and is not suitable for Streamlit Community Cloud. If remote mode is selected but the API URL/token is missing or the Worker is unreachable, registration/login/admin account operations return an error instead of switching to a local database.

## Updating the schema

Add a new numbered SQL file under `migrations/` and apply it with `wrangler d1 migrations apply predictai-accounts --remote`. Do not edit an already-applied migration. Back up the D1 database before changing account schema or production data.
