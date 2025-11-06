/**
 * Cloudflare Worker to serve curlpad install script
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

const INSTALL_SCRIPT = `#!/usr/bin/env bash
set -euo pipefail

# curlpad installer
# Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

REPO_URL="https://github.com/IntegerAlex/curlpad"
BINARY_URL="https://github.com/IntegerAlex/curlpad/releases/latest/download/curlpad"
INSTALL_DIR="\${HOME}/.local/bin"

echo "🚀 Installing curlpad..."

# Detect platform
OS="\$(uname -s)"
ARCH="\$(uname -m)"

if [[ "\$OS" != "Linux" && "\$OS" != "Darwin" ]]; then
  echo "❌ Unsupported OS: \$OS" >&2
  echo "curlpad supports Linux and macOS only." >&2
  exit 1
fi

if [[ "\$ARCH" != "x86_64" && "\$ARCH" != "aarch64" && "\$ARCH" != "arm64" ]]; then
  echo "⚠️  Architecture \$ARCH may not be supported. Trying anyway..." >&2
fi

# Check dependencies
if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl is required but not installed." >&2
  exit 1
fi

# Create install directory
mkdir -p "\$INSTALL_DIR"

# Download binary
echo "📥 Downloading curlpad binary..."
if ! curl -fsSL "\$BINARY_URL" -o "\$INSTALL_DIR/curlpad"; then
  echo "❌ Failed to download binary from \$BINARY_URL" >&2
  echo "You can manually download from: \$REPO_URL/releases" >&2
  exit 1
fi

# Make executable
chmod +x "\$INSTALL_DIR/curlpad"

echo "✅ curlpad installed to \$INSTALL_DIR/curlpad"

# Check if directory is on PATH
case ":\$PATH:" in
  *:"\\$INSTALL_DIR":*)
    echo "✓ \$INSTALL_DIR is on your PATH"
    ;;
  *)
    echo ""
    echo "⚠️  \$INSTALL_DIR is not on your PATH."
    echo "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo ""
    echo "  export PATH=\"\$INSTALL_DIR:\\\$PATH\""
    echo ""
    ;;
esac

echo ""
echo "🎉 Installation complete! Run 'curlpad' to get started."
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

