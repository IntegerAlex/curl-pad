/**
 * Cloudflare Worker to serve curlpad install script
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

const INSTALL_SCRIPT = `#!/usr/bin/env bash
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

    // Serve install script
    if (url.pathname === '/install.sh' || url.pathname === '/') {
      return new Response(INSTALL_SCRIPT, {
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

