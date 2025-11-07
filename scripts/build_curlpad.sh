#!/usr/bin/env bash
set -Eeuo pipefail

# Build a standalone curlpad binary using PyInstaller

# Security: Validate ROOT_DIR is a directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)" || {
  echo "Error: Failed to determine ROOT_DIR" >&2
  exit 1
}

[[ -d "$ROOT_DIR" ]] || {
  echo "Error: Invalid ROOT_DIR: $ROOT_DIR" >&2
  exit 1
}

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

# Remove existing binary if it exists (to avoid permission errors)
if [[ -f "$ROOT_DIR/dist/curlpad" ]]; then
  echo "Removing existing binary: $ROOT_DIR/dist/curlpad"
  rm -f "$ROOT_DIR/dist/curlpad" || {
    echo "Warning: Could not remove existing binary (may be in use)" >&2
    echo "Please close any running instances and try again." >&2
    exit 1
  }
fi

# Build using spec file (works with modular structure)
# The spec file uses curlpad.py as entry point, which imports from src/curlpad
if [[ -f curlpad.spec ]]; then
  pyinstaller --clean curlpad.spec
else
  # Fallback: build directly (will work if package is installed)
  pyinstaller --clean --onefile --name curlpad curlpad.py
fi

BINARY_PATH="$ROOT_DIR/dist/curlpad"

if [[ ! -f "$BINARY_PATH" ]]; then
  echo "Error: Build failed - binary not found at $BINARY_PATH" >&2
  exit 1
fi

echo "Built binary at: $BINARY_PATH"

# Generate SHA256 hash for verification
if command -v sha256sum >/dev/null 2>&1; then
  cd "$ROOT_DIR/dist"
  sha256sum curlpad > curlpad.sha256
  echo "Generated hash file: $ROOT_DIR/dist/curlpad.sha256"
  cat curlpad.sha256
elif command -v shasum >/dev/null 2>&1; then
  cd "$ROOT_DIR/dist"
  shasum -a 256 curlpad > curlpad.sha256
  echo "Generated hash file: $ROOT_DIR/dist/curlpad.sha256"
  cat curlpad.sha256
else
  echo "Warning: sha256sum/shasum not found, skipping hash generation" >&2
fi

