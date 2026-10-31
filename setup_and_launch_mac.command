#!/bin/bash
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3.11 or 3.12, then run this again."
  read -r -p "Press Return to close..." _
  exit 1
fi
if [ ! -d ".venv" ]; then
  echo "Creating a project-local virtual environment..."
  python3 -m venv .venv
fi
echo "Installing/updating PredictAI dependencies. This may take several minutes..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from the safe template. Add your own credentials privately if needed."
fi
echo "Launching PredictAI..."
exec .venv/bin/streamlit run app.py
