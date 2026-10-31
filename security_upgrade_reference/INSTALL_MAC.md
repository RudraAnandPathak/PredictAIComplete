# Install on macOS — copy/paste steps

These steps assume you have the bundle ZIP in `~/Downloads` and your current project is `~/Downloads/PredictAI_UserManagement_Working`. **Do not run these commands in your only original project.** They create a separate test folder.

## 1. Extract to a new folder

```bash
cd ~/Downloads
unzip -o PredictAI_Secure_Upgrade_Bundle.zip -d PredictAI_Secure_Upgrade_Extracted
```

The extracted folder should be `~/Downloads/PredictAI_Secure_Upgrade_Extracted/PredictAI_Secure_Upgrade`.

## 2. Create a separate test project

```bash
cd ~/Downloads
mkdir -p PredictAI_Secure_Test
cp -R PredictAI_Secure_Upgrade_Extracted/PredictAI_Secure_Upgrade/. PredictAI_Secure_Test/
```

This is a new folder. Do not delete `PredictAI_SAFETY_BACKUP` or overwrite your existing working copy.

## 3. Create and activate a virtual environment

If you want to reuse the virtual environment from your existing working copy, you can activate it instead. Otherwise:

```bash
cd ~/Downloads/PredictAI_Secure_Test
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install streamlit pandas matplotlib scipy reportlab python-pptx python-dotenv pypdf
```

The app also imports your existing `document_reader.py` and `local_ai.py`; these are included in this bundle. The local assistant expects Ollama to be installed and a model already pulled, as in your current setup.

## 4. Configure email verification

```bash
cd ~/Downloads/PredictAI_Secure_Test
cp .env.example .env
open -e .env
```

Replace the example SMTP values with credentials from your email provider. Do not paste SMTP credentials into chat or commit `.env` to Git. For local testing, leave `PREDICTAI_PUBLIC_URL=http://localhost:8501`. For hosted deployment, use the public HTTPS URL of your app.

If you do not configure SMTP, users can register but will remain pending and cannot sign in. This is intentional.

## 5. Create the first Owner account

```bash
cd ~/Downloads/PredictAI_Secure_Test
source .venv/bin/activate
python provision_owner.py
```

Enter the Owner details at the prompts. The password is typed into a hidden prompt. Registration through the UI can never assign Owner role.

## 6. Launch the app

```bash
cd ~/Downloads/PredictAI_Secure_Test
source .venv/bin/activate
streamlit run app.py
```

Open the local address printed by Streamlit (usually `http://localhost:8501`). Create a regular test account, click the email verification link, then sign in. Sign in as the Owner in a separate browser session to test the Owner Command Center.

## 7. Test the essential controls

- Duplicate email and username should be rejected.
- A new user should not sign in before verifying email.
- A verified user can sign in using username or email.
- Block the test user in the Owner Command Center; the next rerun should end their active session.
- Grant and revoke Special User access and verify the role persists after sign-out/sign-in.
- A Regular User should be limited to 3 unique documents; Special User/Owner should bypass that count limit.
- A Regular User PDF over 100 pages should be rejected.
- Confirm upload, question, AI-success/failure events appear in the Owner usage dashboard.
- Verify your existing dataset analysis, local assistant, PDF report, and PowerPoint report still work.

## Database and backup

The database is `predictai_auth.db` in the project folder by default. Keep it private and back it up before upgrades. You can set `PREDICTAI_AUTH_DB` to an absolute path if you want it stored elsewhere. Do not copy a test database into production without reviewing it.
