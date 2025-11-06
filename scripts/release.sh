#!/usr/bin/env bash
set -euo pipefail

# Create a GitHub release with built binary
# Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$ROOT_DIR"

# Check for gh CLI
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ GitHub CLI (gh) is not installed." >&2
  echo "Install it: https://cli.github.com/" >&2
  echo "  macOS:   brew install gh" >&2
  echo "  Linux:   See https://github.com/cli/cli/blob/trunk/docs/install_linux.md" >&2
  exit 1
fi

# Check if logged in
if ! gh auth status >/dev/null 2>&1; then
  echo "❌ Not logged in to GitHub." >&2
  echo "Run: gh auth login" >&2
  exit 1
fi

# Get version from curlpad.py
VERSION=$(grep '^__version__ = ' curlpad.py | cut -d'"' -f2)
if [[ -z "$VERSION" ]]; then
  echo "❌ Could not extract version from curlpad.py" >&2
  exit 1
fi

TAG="v${VERSION}"

echo "🚀 Creating release ${TAG}..."

# Check if tag already exists
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "❌ Tag ${TAG} already exists." >&2
  echo "Update __version__ in curlpad.py or delete the tag:" >&2
  echo "  git tag -d ${TAG}" >&2
  echo "  git push origin :refs/tags/${TAG}" >&2
  exit 1
fi

# Build binary
echo "📦 Building binary..."
./scripts/build_curlpad.sh

if [[ ! -f dist/curlpad ]]; then
  echo "❌ Binary not found at dist/curlpad" >&2
  exit 1
fi

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Create and push tag
echo "🏷️  Creating tag ${TAG}..."
git tag -a "${TAG}" -m "Release ${TAG}"
git push origin "${TAG}"

# Generate release notes
RELEASE_NOTES="Release ${TAG}

## Installation

\`\`\`bash
curl -fsSL https://curlpad-installer.gossorg.workers.dev/install.sh | bash
\`\`\`

Or download the binary directly and place it on your PATH.

## Changes

See commit history for details.
"

# Create GitHub release
echo "📝 Creating GitHub release..."
gh release create "${TAG}" \
  --title "curlpad ${TAG}" \
  --notes "${RELEASE_NOTES}" \
  dist/curlpad

echo ""
echo "✅ Release ${TAG} created successfully!"
echo "📦 Binary uploaded: dist/curlpad"
echo "🔗 View at: $(gh release view ${TAG} --json url -q .url)"

