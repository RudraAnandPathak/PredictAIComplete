# Build verification

Verified on 2026-10-31 with Python 3.14 in the project virtual environment.

- Automated test suite: **68 passed**.
- `compileall`: passed for the Streamlit app modules and `predictai_core`.
- Dependency health check: all declared runtime modules were present; Tesseract was present on the build machine.
- Streamlit app smoke check: Streamlit `AppTest` ran the app with no exceptions and found the three authentication tabs.
- A direct HTTP server bind was blocked by this execution environment's socket permissions, so an HTTP response check was not available in this run.
- Archive check: ZIP directory integrity and required setup/changelog files verified after packaging.

The test run emitted deprecation warnings from third party libraries and pandas/scikit-learn API use. Cloudflare and Ollama credentials were not configured, so live external AI requests were not tested. Remote owner bootstrap is intentionally disabled unless the remote account service implements the configured-username and one-time-consumption checks on its server. The local health check does not certify security for public hosting; see `README.md` for deployment limitations.
