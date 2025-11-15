# Create a GitHub release with built binary (Windows)
# Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

$ErrorActionPreference = "Stop"

$ROOT_DIR = Split-Path -Parent $PSScriptRoot
Set-Location $ROOT_DIR

# Check for gh CLI
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) is not installed."
    Write-Output "Install it: https://cli.github.com/"
    Write-Output "  Windows: winget install --id GitHub.cli"
    Write-Output "  Or: https://github.com/cli/cli/releases"
    exit 1
}

# Check if logged in
try {
    gh auth status | Out-Null
} catch {
    Write-Error "Not logged in to GitHub."
    Write-Output "Run: gh auth login"
    exit 1
}

# Get version from Python constants (secure extraction)
if (-not (Get-Command python -ErrorAction SilentlyContinue) -and -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
    Write-Error "python or python3 is required"
    exit 1
}

$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }

$VERSION = & $pythonCmd -c "import sys; sys.path.insert(0, 'src'); from curlpad.constants import __version__; print(__version__)" 2>$null
if (-not $VERSION -or $LASTEXITCODE -ne 0) {
    Write-Error "Could not extract version from curlpad.constants"
    exit 1
}

# Security: Validate version format (semantic versioning)
if ($VERSION -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Invalid version format: $VERSION (expected: X.Y.Z)"
    exit 1
}

$TAG = "v$VERSION"

Write-Output "Creating release $TAG..."

# Check if tag already exists
try {
    git rev-parse "$TAG" | Out-Null
    Write-Error "Tag $TAG already exists."
    Write-Output "Update __version__ in src/curlpad/constants.py or delete the tag:"
    Write-Output "  git tag -d $TAG"
    Write-Output "  git push origin :refs/tags/$TAG"
    exit 1
} catch {
    # Tag doesn't exist, continue
}

# Build binary
Write-Output "Building binary..."
& "$ROOT_DIR\scripts\build_curlpad.ps1"

$binaryPath = Join-Path $ROOT_DIR "dist\curlpad.exe"
if (-not (Test-Path $binaryPath)) {
    Write-Error "Binary not found at $binaryPath"
    exit 1
}

# Get current branch
$BRANCH = git rev-parse --abbrev-ref HEAD

# Create and push tag
Write-Output "Creating tag $TAG..."
git tag -a "$TAG" -m "Release $TAG"
git push origin "$TAG"

# Generate release notes
$RELEASE_NOTES = @"
Release $TAG

## Installation

**Windows:**
\`\`\`powershell
irm curlpad-installer.gossorg.in/install.ps1 | iex
\`\`\`

**Linux/macOS:**
\`\`\`bash
curl -fsSL curlpad-installer.gossorg.in/install.sh | bash
\`\`\`

Or download the binary directly and place it on your PATH.

## Changes

See commit history for details.
"@

# Create GitHub release
Write-Output "Creating GitHub release..."
# Upload with explicit filename to ensure .exe extension is preserved
$tempUpload = "$binaryPath#curlpad.exe"
gh release create "$TAG" `
    --title "curlpad $TAG" `
    --notes $RELEASE_NOTES `
    --latest `
    "$tempUpload"

Write-Output ""
Write-Output "Release $TAG created successfully!"
Write-Output "Binary uploaded: $binaryPath"
$releaseUrl = gh release view $TAG --json url -q .url
Write-Output "View at: $releaseUrl"
Write-Output ""
Write-Output "Download URL: https://github.com/IntegerAlex/curl-pad/releases/latest/download/curlpad.exe"
Write-Output ""

