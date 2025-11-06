#!/usr/bin/env bash
set -euo pipefail

# Install the built curlpad binary onto PATH

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

PREFIX_DEFAULT="$HOME/.local/bin"
PREFIX="$PREFIX_DEFAULT"
USE_SUDO=0

usage() {
  cat <<EOF
Usage: $0 [--prefix DIR] [--sudo]

Options:
  --prefix DIR   Install to DIR (default: $PREFIX_DEFAULT)
  --sudo         Install to /usr/local/bin using sudo
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      if [[ $# -lt 2 || -z "${2:-}" || "${2}" == --* ]]; then
        echo "Error: --prefix requires a directory argument" >&2
        usage
        exit 2
      fi
      PREFIX="$2"
      shift 2
      ;;
    --sudo)
      USE_SUDO=1
      PREFIX="/usr/local/bin"
      shift 1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

# Build if missing
if [[ ! -x "$ROOT_DIR/dist/curlpad" ]]; then
  echo "Binary not found at dist/curlpad; building..."
  "$ROOT_DIR/scripts/build_curlpad.sh"
fi

mkdir -p "$PREFIX"

if [[ $USE_SUDO -eq 1 ]]; then
  sudo cp "$ROOT_DIR/dist/curlpad" "$PREFIX/curlpad"
  sudo chmod 0755 "$PREFIX/curlpad"
else
  cp "$ROOT_DIR/dist/curlpad" "$PREFIX/curlpad"
  chmod 0755 "$PREFIX/curlpad"
fi

echo "Installed: $PREFIX/curlpad"

# PATH hint
case ":$PATH:" in
  *:"$PREFIX":*) ;;
  *) echo "Note: $PREFIX is not on your PATH. Add it, e.g.:"; echo "  export PATH=\"$PREFIX:\$PATH\"";;
esac

