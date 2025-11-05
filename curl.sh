#!/bin/bash

# curlpad - A simple curl editor for the command line
# Copyright (C) 2023 Akshat Kotpalliwar <akshat.kotpalliwar@agribid.ai>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

VERSION="1.0.0"

# Function to display help
show_help() {
  cat << EOF
Usage: $0 [OPTIONS]

A simple curl editor for Linux.

Options:
  --help     Show this help message
  --version  Show version info
  --install  Install missing dependencies (vim, jq)

Examples:
  $0                     # Start interactive editor
  $0 --help              # Show help
  $0 --version           # Show version
  $0 --install           # Install vim and jq if missing

Dependencies:
  - vim (or vi)       : For editing
  - jq                : For JSON formatting (optional)
EOF
}

# Function to install dependencies
install_deps() {
  echo "🔧 Installing missing dependencies..."

  if command -v apt-get >/dev/null 2>&1; then
    # Debian/Ubuntu
    sudo apt-get update
    sudo apt-get install -y vim jq
  elif command -v dnf >/dev/null 2>&1; then
    # RHEL/CentOS/Fedora
    sudo dnf install -y vim jq
  elif command -v yum >/dev/null 2>&1; then
    # Older RHEL/CentOS
    sudo yum install -y vim jq
  else
    echo "❌ Cannot auto-install: unsupported package manager."
    echo "Please install vim and jq manually:"
    echo "  Ubuntu/Debian: sudo apt install vim jq"
    echo "  RHEL/CentOS: sudo yum install vim jq"
    exit 1
  fi

  echo "✅ Dependencies installed."
}

# Parse arguments
case "$1" in
  --help|-h)
    show_help
    exit 0
    ;;
  --version|-v)
    echo "curlpad version $VERSION"
    exit 0
    ;;
  --install)
    install_deps
    exit 0
    ;;
  "")
    # No args → proceed normally
    ;;
  *)
    echo "Unknown option: $1"
    show_help
    exit 1
    ;;
esac

# Create temporary files
tmpfile=$(mktemp)
vimrc_tmp=$(mktemp)

# Template: 7 lines of comments + 1 blank line = total 8 lines
cat > "$tmpfile" << 'EOF'
#!/bin/bash
# curlpad - scratchpad for curl.
# AUTHOR - Akshat Kotpalliwar (alias IntegerAlex)
# LICENSE - GPLv2 or later
# curl -X POST "https://api.example.com" \
#   -H "Content-Type: application/json" \
#   -d '{"key":"value"}'

EOF
# ↑ Line 8 is empty (this is where cursor should go)

# Vim config
cat > "$vimrc_tmp" << 'EOF'
set nocompatible
syntax on
filetype plugin indent on
set filetype=sh
set number
set autoindent
set tabstop=2
set shiftwidth=2
set expandtab
set backspace=indent,eol,start
EOF

# Check for vim or vi
if command -v vim >/dev/null 2>&1; then
  editor="vim"
elif command -v vi >/dev/null 2>&1; then
  editor="vi"
else
  echo "Error: Neither vim nor vi is installed."
  echo "Run '$0 --install' to install them automatically."
  rm -f "$tmpfile" "$vimrc_tmp"
  exit 1
fi

# Open editor at line 8, enter Insert mode
if [[ "$editor" == "vim" ]]; then
  $editor -u "$vimrc_tmp" -c "8" -c "startinsert" "$tmpfile"
else
  # For vi, use :goto 8 and start insert mode
  $editor -c "8" -c "startinsert" "$tmpfile"
fi

rm -f "$vimrc_tmp"

# Check if user added any UNCOMMENTED command
if ! grep -q "^[^#]" "$tmpfile" 2>/dev/null; then
  echo "No uncommented command found. Exiting."
  rm -f "$tmpfile"
  exit 0
fi

# Optional: format JSON in -d '...' using jq
if command -v jq >/dev/null 2>&1; then
  formatted_file=$(mktemp)
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^[^#]*curl.*-d[[:space:]]*\'\{[^}]*\}\' ]]; then
      if [[ "$line" =~ (.+-d[[:space:]]*\')(\{[^}]*\})(\'.*) ]]; then
        before="${BASH_REMATCH[1]}"
        json_str="${BASH_REMATCH[2]}"
        after="${BASH_REMATCH[3]}"
        if formatted_json=$(echo "$json_str" | jq -c . 2>/dev/null); then
          echo "${before}${formatted_json}${after}"
        else
          echo "$line"
        fi
      else
        echo "$line"
      fi
    else
      echo "$line"
    fi
  done < "$tmpfile" > "$formatted_file"
  mv "$formatted_file" "$tmpfile"
fi

# Show final commands
echo
echo "📋 Final command(s) to execute:"
echo "----------------------------------------"
grep "^[^#]" "$tmpfile"
echo "----------------------------------------"

read -p "Press Enter to run, or Ctrl+C to cancel... " _

echo
echo "▶ Running your cURL command(s)..."
bash -c "$(grep "^[^#]" "$tmpfile")"

rm -f "$tmpfile"
