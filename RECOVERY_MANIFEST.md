# Recovery manifest

## Source of the main application

The main application tree was extracted from `PredictAI_Phase11_Unlimited_Special_Context_Fix.zip` within the user-provided `PredictAICOMPLETE_RECOVERY 2.zip`. This archive contained the integrated Phase 1–9 project and the later Phase 11 generator update.

## Why this base was selected

- It contains the integrated app and `predictai_core` package for Phases 5–9.
- It includes the Phase 11 exam generator with long-source chunking and quality checks.
- It includes Phase 11 tests for the quality and unlimited-special-context fixes.
- Its existing test suite passed in the packaging environment.

## Other recovered code

The secure-upgrade and user-management UI bundles are retained in `security_upgrade_reference/` rather than being overlaid on active login code. Their API differs from the existing Phase 8/9 application and needs a planned integration pass.

## Verification performed

- Automated tests: 63 passed in the packaging environment.
- Syntax compilation and runtime checks should be repeated in the user's own environment.
- Live Cloudflare Workers AI, Ollama, Tesseract OCR, and browser-based workflows were not fully exercised as part of packaging.
