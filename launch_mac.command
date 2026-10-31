#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ ! -x ".venv/bin/streamlit" ]; then
  echo "PredictAI environment not found. First run the setup commands in README.md."
  read -r -p "Press Return to close..." _
  exit 1
fi
if [ ! -f ".env" ]; then
  echo "No .env file found. Cloud AI and owner setup may not be configured."
  echo "You can copy .env.example to .env and edit it privately."
fi
exec .venv/bin/streamlit run app.py
