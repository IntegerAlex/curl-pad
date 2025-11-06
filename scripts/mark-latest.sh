#!/usr/bin/env bash
set -euo pipefail

# Mark a GitHub release as latest
# Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

# Check for gh CLI
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ GitHub CLI (gh) is not installed." >&2
  exit 1
fi

# Check if logged in
if ! gh auth status >/dev/null 2>&1; then
  echo "❌ Not logged in to GitHub." >&2
  echo "Run: gh auth login" >&2
  exit 1
fi

TAG="${1:-}"

if [[ -z "$TAG" ]]; then
  echo "Usage: $0 <tag>" >&2
  echo "Example: $0 v1.0.0" >&2
  exit 1
fi

echo "🏷️  Marking ${TAG} as latest release..."

# Edit the release to mark it as latest
gh release edit "${TAG}" --latest

echo "✅ Release ${TAG} is now marked as latest!"
echo "📦 Download URL: https://github.com/IntegerAlex/curl-pad/releases/latest/download/curlpad"

