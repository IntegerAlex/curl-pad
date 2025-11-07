#!/usr/bin/env bash
set -Eeuo pipefail

# Install the built curlpad binary onto PATH

# Security: Validate ROOT_DIR
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)" || {
  echo "Error: Failed to determine ROOT_DIR" >&2
  exit 1
}

[[ -d "$ROOT_DIR" ]] || {
  echo "Error: Invalid ROOT_DIR: $ROOT_DIR" >&2
  exit 1
}

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
      
      # Security: Validate PREFIX is an absolute path
      case "${2}" in
        /*) PREFIX="$2" ;;
        *) echo "Error: --prefix must be an absolute path" >&2; exit 2 ;;
      esac
      
      # Security: Prevent installation to sensitive system directories
      case "$PREFIX" in
        /|/bin|/usr/bin|/sbin|/usr/sbin|/boot|/dev|/proc|/sys)
          echo "Error: Cannot install to protected system directory: $PREFIX" >&2
          exit 2
          ;;
      esac
      
      shift 2
      ;;
    --sudo)
      USE_SUDO=1
      # If user did not set a custom prefix, default to /usr/local/bin
      if [[ "$PREFIX" == "$PREFIX_DEFAULT" ]]; then
        PREFIX="/usr/local/bin"
      fi
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

