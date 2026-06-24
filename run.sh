#!/usr/bin/env bash
# Convenience launcher for local development.
set -euo pipefail

cd "$(dirname "$0")"

# Create a venv on first run.
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment…"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing dependencies…"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

echo ""
echo "▶  Visual Learn Everything running at http://${HOST}:${PORT}"
echo ""
exec uvicorn backend.main:app --host "$HOST" --port "$PORT" --reload
