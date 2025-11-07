/**
 * Cloudflare Worker to serve curlpad install script
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

const INSTALL_SCRIPT_BASH = `#!/usr/bin/env bash
set -euo pipefail

# curlpad - Scratchpad for curl.
# Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

# Color codes
C_RESET=$'\\033[0m'
C_BLUE=$'\\033[38;2;66;135;245m'      # #4287f5
C_GREEN=$'\\033[38;2;76;175;80m'      # #4caf50
C_RED=$'\\033[38;2;244;67;54m'        # #f44336
C_YELLOW=$'\\033[38;2;255;193;7m'     # #ffc107
C_BOLD=$'\\033[1m'

REPO_URL="https://github.com/IntegerAlex/curl-pad"
BINARY_URL="https://github.com/IntegerAlex/curl-pad/releases/latest/download/curlpad"
INSTALL_DIR="\${HOME}/.local/bin"

echo ""
echo "\${C_BOLD}\${C_BLUE}curlpad installer\${C_RESET}"
echo "\${C_BLUE}A simple curl editor for the command line\${C_RESET}"
echo ""
echo "Author:  Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>"
echo "License: GPL-3.0-or-later"
echo "Repo:    \${REPO_URL}"
echo ""
echo "\${C_BOLD}Installing curlpad...\${C_RESET}"
echo ""

# Detect platform
OS="\$(uname -s)"
ARCH="\$(uname -m)"

if [[ "\$OS" != "Linux" && "\$OS" != "Darwin" ]]; then
  echo "\${C_RED}[ERROR] Unsupported OS: \$OS\${C_RESET}" >&2
  echo "curlpad supports Linux and macOS only." >&2
  exit 1
fi

if [[ "\$ARCH" != "x86_64" && "\$ARCH" != "aarch64" && "\$ARCH" != "arm64" ]]; then
  echo "\${C_YELLOW}[WARNING] Architecture \$ARCH may not be supported. Trying anyway...\${C_RESET}" >&2
fi

# Check dependencies
if ! command -v curl >/dev/null 2>&1; then
  echo "\${C_RED}[ERROR] curl is required but not installed.\${C_RESET}" >&2
  exit 1
fi

# Create install directory
mkdir -p "\$INSTALL_DIR"

# Download binary
echo "Downloading curlpad binary..."
if ! curl -fsSL "\$BINARY_URL" -o "\$INSTALL_DIR/curlpad"; then
  echo "\${C_RED}[ERROR] Failed to download binary from \$BINARY_URL\${C_RESET}" >&2
  echo "You can manually download from: \$REPO_URL/releases" >&2
  exit 1
fi

# Download SHA256 hash for verification
echo "Downloading hash file for verification..."
HASH_URL="https://github.com/IntegerAlex/curl-pad/releases/latest/download/curlpad.sha256"
if curl -fsSL "\$HASH_URL" -o "\$INSTALL_DIR/curlpad.sha256" 2>/dev/null; then
  echo "Verifying binary integrity..."
  cd "\$INSTALL_DIR"
  if command -v sha256sum >/dev/null 2>&1; then
    if sha256sum -c curlpad.sha256 >/dev/null 2>&1; then
      echo "\${C_GREEN}[OK] Binary integrity verified\${C_RESET}"
    else
      echo "\${C_RED}[ERROR] Binary integrity check failed!\${C_RESET}" >&2
      echo "The downloaded binary does not match the expected hash." >&2
      echo "This could indicate a compromised download." >&2
      rm -f curlpad curlpad.sha256
      exit 1
    fi
  elif command -v shasum >/dev/null 2>&1; then
    if shasum -a 256 -c curlpad.sha256 >/dev/null 2>&1; then
      echo "\${C_GREEN}[OK] Binary integrity verified\${C_RESET}"
    else
      echo "\${C_RED}[ERROR] Binary integrity check failed!\${C_RESET}" >&2
      rm -f curlpad curlpad.sha256
      exit 1
    fi
  else
    echo "\${C_YELLOW}[WARNING] sha256sum/shasum not found, skipping integrity check\${C_RESET}" >&2
  fi
  rm -f curlpad.sha256
else
  echo "\${C_YELLOW}[WARNING] Could not download hash file, skipping integrity check\${C_RESET}" >&2
fi

# Make executable
chmod +x "\$INSTALL_DIR/curlpad"

echo "\${C_GREEN}[SUCCESS] curlpad installed to \$INSTALL_DIR/curlpad\${C_RESET}"
echo ""

# Check if directory is on PATH
case ":\$PATH:" in
  *:"\\$INSTALL_DIR":*)
    echo "\${C_GREEN}[OK] \$INSTALL_DIR is on your PATH\${C_RESET}"
    ;;
  *)
    echo "\${C_YELLOW}[WARNING] \$INSTALL_DIR is not on your PATH.\${C_RESET}"
    echo "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo ""
    echo "  export PATH=\"\$INSTALL_DIR:\\\$PATH\""
    echo ""
    ;;
esac

echo ""
echo "\${C_BOLD}\${C_GREEN}Installation complete! Run 'curlpad' to get started.\${C_RESET}"
echo ""
`;

const INSTALL_SCRIPT_PS1 = `# Install curlpad binary onto PATH (Windows)
# Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

$ErrorActionPreference = "Stop"

# Color output functions
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Error { Write-ColorOutput Red $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Info { Write-ColorOutput Cyan $args }

# Configuration
$REPO_URL = "https://github.com/IntegerAlex/curl-pad"
$BINARY_URL = "https://github.com/IntegerAlex/curl-pad/releases/latest/download/curlpad.exe"
$INSTALL_DIR = Join-Path $env:LOCALAPPDATA "Programs\\curlpad"
$BINARY_PATH = Join-Path $INSTALL_DIR "curlpad.exe"

Write-Output ""
Write-Info "curlpad installer"
Write-Info "A simple curl editor for the command line"
Write-Output ""
Write-Output "Author:  Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>"
Write-Output "License: GPL-3.0-or-later"
Write-Output "Repo:    $REPO_URL"
Write-Output ""
Write-Info "Installing curlpad..."
Write-Output ""

# Check if running on Windows
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error "[ERROR] PowerShell 5.0 or later is required."
    exit 1
}

# Check dependencies
if (-not (Get-Command curl -ErrorAction SilentlyContinue)) {
    Write-Error "[ERROR] curl is required but not installed."
    Write-Output "Install curl: https://curl.se/windows/"
    exit 1
}

# Create install directory
Write-Output "Creating install directory: $INSTALL_DIR"
New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null

# Download binary
Write-Output "Downloading curlpad binary..."
try {
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $BINARY_URL -OutFile $BINARY_PATH -UseBasicParsing
    Write-Success "[SUCCESS] Downloaded curlpad.exe"
} catch {
    Write-Error "[ERROR] Failed to download binary from $BINARY_URL"
    Write-Output "You can manually download from: $REPO_URL/releases"
    exit 1
}

Write-Success "[SUCCESS] curlpad installed to $BINARY_PATH"
Write-Output ""

# Check if directory is on PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathArray = $currentPath -split ';' | Where-Object { $_ -ne '' }

if ($pathArray -contains $INSTALL_DIR) {
    Write-Success "[OK] $INSTALL_DIR is on your PATH"
} else {
    Write-Warning "[WARNING] $INSTALL_DIR is not on your PATH."
    Write-Output ""
    Write-Output "Would you like to add it to your PATH? (Y/N)"
    $response = Read-Host
    
    if ($response -eq 'Y' -or $response -eq 'y') {
        try {
            $newPath = $currentPath
            if ($newPath -and -not $newPath.EndsWith(';')) {
                $newPath += ';'
            }
            $newPath += $INSTALL_DIR
            
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
            Write-Success "[SUCCESS] Added $INSTALL_DIR to PATH"
            Write-Warning "[NOTE] You may need to restart your terminal for the PATH change to take effect."
        } catch {
            Write-Error "[ERROR] Failed to add to PATH: $_"
            Write-Output ""
            Write-Output "You can manually add it by:"
            Write-Output "1. Open System Properties > Environment Variables"
            Write-Output "2. Edit User PATH variable"
            Write-Output "3. Add: $INSTALL_DIR"
        }
    } else {
        Write-Output ""
        Write-Output "To use curlpad, either:"
        Write-Output "1. Add $INSTALL_DIR to your PATH manually"
        Write-Output "2. Or run: $BINARY_PATH"
    }
}

Write-Output ""
Write-Success "Installation complete! Run 'curlpad' to get started."
Write-Output ""
`;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle OPTIONS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: corsHeaders,
      });
    }

    // Serve Windows PowerShell install script
    if (url.pathname === '/install.ps1') {
      return new Response(INSTALL_SCRIPT_PS1, {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'text/x-powershell',
          'Content-Disposition': 'inline; filename="install.ps1"',
          'Cache-Control': 'public, max-age=300',
        },
      });
    }

    // Serve bash install script (default for Linux/macOS)
    if (url.pathname === '/install.sh' || url.pathname === '/') {
      return new Response(INSTALL_SCRIPT_BASH, {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'text/x-shellscript',
          'Content-Disposition': 'inline; filename="install.sh"',
          'Cache-Control': 'public, max-age=300',
        },
      });
    }

    // Health check endpoint
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok', service: 'curlpad-installer' }), {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
        },
      });
    }

    // 404 for other paths
    return new Response('Not Found', {
      status: 404,
      headers: corsHeaders,
    });
  },
};

