#!/usr/bin/env bash
set -euo pipefail

# Build a standalone curlpad binary using PyInstaller

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found" >&2
  exit 1
fi

# Prefer local venv if present
if [[ -d .venv ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python3 -m pip install --upgrade pip >/dev/null
python3 -m pip install -r requirements.txt >/dev/null

# Build
pyinstaller --clean --onefile --name curlpad curlpad.py

echo "Built binary at: $ROOT_DIR/dist/curlpad"

