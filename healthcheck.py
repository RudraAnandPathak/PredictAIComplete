"""Non-destructive environment check for PredictAI."""
from __future__ import annotations
import importlib.util
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULES = [
    "streamlit", "pandas", "numpy", "scipy", "matplotlib", "reportlab",
    "pptx", "fitz", "docx", "requests", "openpyxl", "sklearn", "dotenv",
    "PIL", "pytesseract",
]
print("PredictAI health check")
print(f"Project folder: {ROOT}")
missing = []
for module in MODULES:
    ok = importlib.util.find_spec(module) is not None
    print(f"{'OK' if ok else 'MISSING':7} Python module: {module}")
    if not ok:
        missing.append(module)
print(f"{'OK' if shutil.which('tesseract') else 'OPTIONAL':7} OCR executable: tesseract")
print(f"{'OK' if (ROOT / '.env').exists() else 'OPTIONAL':7} .env configuration file")
print(f"{'SET' if os.getenv('CLOUDFLARE_ACCOUNT_ID') else 'NOT SET':7} Cloudflare credentials in current shell (the app loads .env)")
print(f"{'OK' if (ROOT / 'predictai_core' / 'phase11_exam_paper.py').exists() else 'MISSING':7} Phase 11 exam generator")
print(f"{'OK' if (ROOT / 'predictai_core' / 'phase9' / 'admin.py').exists() else 'MISSING':7} Phase 9 owner dashboard")
if missing:
    print("\nInstall missing dependencies with: python -m pip install -r requirements.txt")
    raise SystemExit(1)
print("\nDependency check complete. This does not test live AI credentials or guarantee runtime correctness.")
