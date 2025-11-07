#!/usr/bin/env python3
"""
curlpad - A simple curl editor for the command line
Copyright (C) 2023 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>

SPDX-License-Identifier: GPL-3.0-or-later

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

__version__ = "1.0.0"
__author__ = "Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>"
__license__ = "GPL-3.0-or-later"

import argparse
import atexit
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import shlex
from typing import List
from datetime import datetime

# ANSI color codes for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Global variables for cleanup
temp_files: List[str] = []
DEBUG = False

def debug_print(message: str) -> None:
    """Print debug message when DEBUG is enabled."""
    if DEBUG:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{Colors.MAGENTA}[DEBUG {ts}] {message}{Colors.RESET}")

def cleanup_temp_files():
    """Clean up all temporary files."""
    debug_print(f"Cleanup starting for {len(temp_files)} temp files")
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                debug_print(f"Removing temp file: {temp_file}")
                os.unlink(temp_file)
        except OSError:
            pass  # Ignore cleanup errors

# Register cleanup function
atexit.register(cleanup_temp_files)

def signal_handler(signum, frame):
    """Handle signals and cleanup."""
    cleanup_temp_files()
    sys.exit(1)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def print_error(message: str) -> None:
    """Print error message and exit."""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}", file=sys.stderr)
    cleanup_temp_files()
    sys.exit(1)

def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}", file=sys.stderr)

def print_success(message: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def confirm_execution(commands: List[str]) -> bool:
    """Confirm execution, handling cases where stdin is unavailable."""
    # Try to use stdin first (even if isatty() returns False in frozen binaries)
    # With console=True, stdin should work even in frozen binaries
    if sys.stdin is not None:
        try:
            # Try to use stdin - this works even if isatty() returns False
            print("Press Enter to run, or Ctrl+C to cancel... ", end='', flush=True)
            input()
            return True
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return False
        except (RuntimeError, EOFError, OSError) as exc:
            debug_print(f"stdin unavailable: {exc}")
            # Fall through to MessageBox fallback

    # Fallback to MessageBox on Windows if stdin failed
    if os.name == 'nt':
        try:
            import ctypes

            MB_OKCANCEL = 0x00000001
            MB_ICONINFORMATION = 0x00000040
            IDOK = 1

            message = "Run the following command(s)?\n\n" + "\n".join(commands)
            result = ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                None,
                message,
                "curlpad",
                MB_OKCANCEL | MB_ICONINFORMATION,
            )
            if result == IDOK:
                return True
            print_info("Operation cancelled.")
            return False
        except Exception as exc:  # pragma: no cover - Windows specific
            debug_print(f"Failed to show Windows prompt: {exc}")

    print_warning("No interactive console detected; proceeding without confirmation.")
    return True

def check_command(command: str) -> bool:
    """Check if a command exists in PATH."""
    path = shutil.which(command)
    debug_print(f"Check command '{command}': {'found at ' + path if path else 'not found'}")
    return path is not None

def get_editor() -> str:
    """Get the available editor (prefer nvim over vim)."""
    if check_command('nvim'):
        debug_print("Selected editor: nvim")
        return 'nvim'
    elif check_command('vim'):
        debug_print("Selected editor: vim")
        return 'vim'
    else:
        print_error("Neither nvim nor vim is installed.\nRun 'python3 curlpad.py --install' to install dependencies.")

def check_dependencies() -> None:
    """Check for required dependencies."""
    if not check_command('curl'):
        print_error("curl is not installed. Please install curl first.")

def show_help() -> None:
    """Display help message."""
    help_text = f"""
curlpad - A simple curl editor for the command line

Usage: {sys.argv[0]} [OPTIONS]

A simple curl editor for Linux and macOS with built-in autocomplete in Vim/Neovim.

Options:
  --help, -h      Show this help message
  --version, -v   Show version info
  --install       Install missing dependencies (vim, jq)
  --debug         Enable extremely verbose debug output

Examples:
  {sys.argv[0]}                     # Start editor with curl autocomplete
  {sys.argv[0]} --help              # Show help
  {sys.argv[0]} --version           # Show version
  {sys.argv[0]} --install           # Install vim and jq if missing

In the editor:
  - Press Ctrl+X Ctrl+K in insert mode to autocomplete curl options, methods, headers, etc.
  - Use Tab for normal indentation
  - Uncomment and edit the example commands

Dependencies:
  - nvim or vim     : For editing with autocomplete
  - curl            : For executing commands
  - jq              : For JSON formatting (optional)
"""
    print(help_text)

def show_version() -> None:
    """Display version info."""
    print(f"curlpad version {__version__}")

def install_deps() -> None:
    """Install missing dependencies."""
    print_info("Installing missing dependencies...")

    system = platform.system().lower()
    debug_print(f"Detected platform: {system}")
    if system == "linux":
        # Try different package managers
        if check_command('apt-get'):
            # Debian/Ubuntu
            debug_print("Using apt-get for installation")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'vim', 'jq'], check=True)
        elif check_command('dnf'):
            # RHEL/CentOS/Fedora
            debug_print("Using dnf for installation")
            subprocess.run(['sudo', 'dnf', 'install', '-y', 'vim', 'jq'], check=True)
        elif check_command('yum'):
            # Older RHEL/CentOS
            debug_print("Using yum for installation")
            subprocess.run(['sudo', 'yum', 'install', '-y', 'vim', 'jq'], check=True)
        else:
            print_error("Cannot auto-install: unsupported package manager.\nPlease install vim and jq manually:\n  Ubuntu/Debian: sudo apt install vim jq\n  RHEL/CentOS: sudo yum install vim jq")
    elif system == "darwin":
        # macOS
        if check_command('brew'):
            debug_print("Using Homebrew for installation")
            subprocess.run(['brew', 'install', 'vim', 'jq'], check=True)
        else:
            print_error("Cannot auto-install: Homebrew not found.\nPlease install Homebrew and run: brew install vim jq")
    else:
        print_error(f"Unsupported platform: {system}")

    print_success("Dependencies installed.")

def create_template_file() -> str:
    """Create temporary file with curl template."""
    template = """#!/bin/bash
# curlpad - scratchpad for curl.
# AUTHOR - Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# curl -X POST "https://api.example.com" \\
#   -H "Content-Type: application/json" \\
#   -d '{"key":"value"}'

"""

    fd, tmpfile = tempfile.mkstemp(suffix='.sh')
    temp_files.append(tmpfile)
    debug_print(f"Created template file at: {tmpfile}")

    try:
        with os.fdopen(fd, 'w') as f:
            f.write(template)
    except OSError as e:
        print_error(f"Failed to create template file: {e}")

    return tmpfile

def create_curl_dict() -> str:
    """Create temporary curl dictionary file for Vim completion."""
    curl_options = [
        '-X', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS',
        '-H', '--header', 'Content-Type:', 'application/json', 'application/xml', 'text/plain',
        '-d', '--data', '--data-raw', '--data-binary', '--data-urlencode',
        '--url', '-i', '--include', '-v', '--verbose', '-s', '--silent',
        '-o', '--output', '-L', '--location', '-k', '--insecure',
        '--connect-timeout', '--max-time', '-u', '--user', '-x', '--proxy',
        '--cert', '--key', '--cacert', '-A', '--user-agent',
        '-b', '--cookie', '-c', '--cookie-jar', '-e', '--referer',
        '-f', '--fail', '-I', '--head', '-m', '--max-redirs',
        '--compressed', '--digest', '--negotiate', '--ntlm',
        'curl', 'https://', 'http://', 'localhost', '127.0.0.1'
    ]

    fd, dict_tmp = tempfile.mkstemp(suffix='.dict')
    temp_files.append(dict_tmp)
    debug_print(f"Created curl dictionary at: {dict_tmp} with {len(curl_options)} entries")

    try:
        with os.fdopen(fd, 'w') as f:
            for option in curl_options:
                f.write(f"{option}\n")
        if DEBUG:
            # Verify dictionary file was created correctly
            with open(dict_tmp, 'r') as f:
                lines = f.readlines()
                debug_print(f"Dictionary file verified: {len(lines)} lines, first 5: {[l.strip() for l in lines[:5]]}")
    except OSError as e:
        print_error(f"Failed to create dictionary file: {e}")

    return dict_tmp

def create_editor_config(target_file: str) -> str:
    """Create temporary vimrc/lua file (Neovim Lua or Vimscript) with curl completion.

    Settings are applied buffer-locally and scoped to the provided target file.
    """
    dict_file = create_curl_dict()
    editor = get_editor()

    if editor == 'nvim':
        # Use Lua config for Neovim
        config_content = f'''-- Neovim Lua configuration for curl completion
local dict_file = [[{dict_file}]]
local target_path = [[{target_file}]]

-- Enable syntax highlighting
vim.cmd('syntax on')

-- Basic UI/options
vim.o.number = true
vim.o.autoindent = true
vim.o.tabstop = 2
vim.o.shiftwidth = 2
vim.o.expandtab = true
vim.o.backspace = 'indent,eol,start'

-- Enable truecolor and try to apply a builtin colorscheme
vim.o.termguicolors = true
pcall(vim.cmd, 'colorscheme elflord')

-- Enable filetype detection, plugins, indent
vim.cmd('filetype plugin indent on')

-- Function to setup buffer
local function setup_buffer(buf)
  vim.bo[buf].filetype = 'sh'
  -- Clear and set dictionary
  vim.opt_local.dictionary = {{ dict_file }}
  vim.opt_local.complete:append('k')
  vim.opt_local.completeopt = {{ 'menu', 'menuone', 'preview' }}
  -- Map Ctrl-Space to trigger dictionary completion for this buffer
  pcall(vim.keymap.set, 'i', '<C-Space>', '<C-x><C-k>', {{ buffer = buf, noremap = true, silent = true }})
  -- Debug: verify settings
  local dict_setting = vim.opt_local.dictionary:get()
  local complete_setting = vim.opt_local.complete:get()
  vim.api.nvim_echo({{
    {{ 'Curl autocomplete: Ctrl+Space or Ctrl+X Ctrl+K', 'Normal' }},
    {{ '  Dictionary: ' .. (dict_setting[1] or 'not set'), 'Comment' }},
    {{ '  Complete: ' .. table.concat(complete_setting, ','), 'Comment' }}
  }}, true, {{}})
end

-- Apply to current buffer immediately
vim.schedule(function()
  local current_buf = vim.api.nvim_get_current_buf()
  setup_buffer(current_buf)
end)

-- Also setup on buffer events
vim.api.nvim_create_autocmd({{ 'BufEnter', 'BufWinEnter' }}, {{
  callback = function(args)
    setup_buffer(args.buf)
  end,
  once = false,
}})
'''
        suffix = '.lua'
    else:
        # Fallback to Vimscript for regular Vim
        config_content = f'''set nocompatible
syntax on
filetype plugin indent on
set filetype=sh
set number
set autoindent
set tabstop=2
set shiftwidth=2
set expandtab
set backspace=indent,eol,start

" Enable dictionary completion for curl commands
set dictionary={dict_file}
set complete+=k
set completeopt=menu,menuone,preview

" Show helpful message
echo "Curl autocomplete available: Press Ctrl+X Ctrl+K in insert mode for completion"
'''
        suffix = '.vimrc'

    fd, config_tmp = tempfile.mkstemp(suffix=suffix)
    temp_files.append(config_tmp)
    debug_print(f"Created editor config at: {config_tmp} (editor={editor}, suffix={suffix})")

    try:
        with os.fdopen(fd, 'w') as f:
            f.write(config_content)
        if DEBUG:
            lines = config_content.split('\n')
            debug_print(f"Config file content ({len(config_content)} bytes):")
            for i, line in enumerate(lines[:20], 1):
                debug_print(f"  {i:3d}: {line}")
            total_lines = len(lines)
            if total_lines > 20:
                remaining_lines = total_lines - 20
                debug_print(f"  ... ({remaining_lines} more lines)")
    except OSError as e:
        print_error(f"Failed to create config file: {e}")

    return config_tmp

def open_editor(tmpfile: str) -> None:
    """Open the editor with the template file."""
    editor = get_editor()
    config_tmp = create_editor_config(tmpfile)

    try:
        if editor == 'nvim':
            # Neovim command with Lua config
            # Load file first, then apply config, then go to line 8 and start insert
            cmd = [editor, '--clean', '-u', 'NONE', tmpfile, '-c', f'luafile {config_tmp}', '-c', 'doautocmd BufEnter', '+8', '+startinsert']
        else:
            # Vim command with vimrc
            cmd = [editor, '-u', config_tmp, '+8', '+startinsert', tmpfile]
        debug_print(f"Launching editor with command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print_error(f"Editor exited with error: {e}")
    except FileNotFoundError:
        print_error(f"Editor '{editor}' not found.")
    finally:
        # Clean up config file
        try:
            debug_print(f"Removing editor config: {config_tmp}")
            os.unlink(config_tmp)
            temp_files.remove(config_tmp)
        except OSError:
            pass

def extract_commands(tmpfile: str) -> List[str]:
    """Extract uncommented commands and coalesce multiline curls into single commands.

    Rules:
    - Ignore empty and comment lines
    - Start a new command when a line starts with 'curl'
    - Lines ending with '\\' are continued on the next line (backslash removed)
    - Lines starting with an option ('-', '--') continue the previous curl command
    - Indented lines also continue the previous curl command
    """
    raw_lines: List[str] = []
    try:
        with open(tmpfile, 'r') as f:
            for raw in f:
                raw_lines.append(raw.rstrip('\n'))
    except OSError as e:
        print_error(f"Failed to read temp file: {e}")

    # Filter out comments and empty lines, but preserve indentation for continuation detection
    filtered: List[str] = []
    for raw in raw_lines:
        if not raw.strip():
            continue
        if raw.lstrip().startswith('#'):
            continue
        filtered.append(raw)

    coalesced: List[str] = []
    current: List[str] = []

    def flush_current():
        nonlocal current
        if current:
            # Join with single spaces
            joined = ' '.join(part.strip() for part in current if part.strip())
            if joined:
                coalesced.append(joined)
        current = []

    for raw in filtered:
        line = raw.rstrip()
        lstrip = raw.lstrip()
        # Determine if line is continuation
        is_continuation = False
        if current:
            if line.endswith('\\'):
                is_continuation = True
                line = line[:-1].rstrip()
            elif lstrip.startswith('-'):
                is_continuation = True
            elif raw != lstrip:  # indented
                is_continuation = True

        if not current:
            # Start only when 'curl' begins the line (ignoring leading spaces)
            if lstrip.startswith('curl'):
                # Handle trailing backslash
                if line.endswith('\\'):
                    current.append(line[:-1].rstrip())
                else:
                    current.append(line)
                    flush_current()
            else:
                debug_print(f"Skipping non-curl leading line: {raw}")
        else:
            # Continuation for existing curl
            current.append(line)
            if not is_continuation:
                flush_current()

    # Flush at end
    flush_current()

    debug_print(f"Extracted {len(coalesced)} curl command(s) from {tmpfile}")
    return coalesced

def format_json_with_jq(commands: List[str]) -> List[str]:
    """Format JSON in curl commands using jq if available."""
    if not check_command('jq'):
        debug_print("jq not found; skipping JSON formatting")
        return commands

    formatted_commands = []

    for line in commands:
        original_line = line
        # Look for curl commands with -d containing JSON
        pattern = r'(.*curl.*-d\s*[\'"])({[^}]*})([\'"].*)'
        match = re.search(pattern, line)

        if match:
            before, json_str, after = match.groups()
            try:
                # Format JSON using jq
                result = subprocess.run(
                    ['jq', '-c', '.'],
                    input=json_str,
                    text=True,
                    capture_output=True,
                    check=True
                )
                formatted_json = result.stdout.strip()
                line = f"{before}{formatted_json}{after}"
                debug_print(f"Formatted JSON in command: {original_line} -> {line}")
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                # If jq fails, keep original
                debug_print("jq failed to format JSON; keeping original line")
                pass

        formatted_commands.append(line)

    return formatted_commands

def validate_command(command: str) -> bool:
    """Basic validation of curl command."""
    # Check if it starts with curl
    if not command.strip().startswith('curl'):
        return False

    # Basic syntax check - curl followed by options/URL
    # This is a simple check, real validation would be complex
    return True

def run_command(command: str) -> None:
    """Execute the curl command."""
    try:
        print(f"\n{Colors.CYAN}▶ Running your cURL command...{Colors.RESET}")

        if os.name == 'nt':
            debug_print(f"Executing directly (Windows): {command}")
            try:
                args = shlex.split(command, posix=True)
            except ValueError as exc:
                print_warning(f"Failed to parse command; running via cmd.exe: {exc}")
                args = None

            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

            if args:
                if args and args[0].lower() == 'curl':
                    curl_exe = shutil.which('curl.exe') or shutil.which('curl')
                    if curl_exe:
                        args[0] = curl_exe
                    else:
                        args[0] = 'curl.exe'
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    check=False,
                    creationflags=creationflags,
                )
            else:
                result = subprocess.run(
                    ['cmd', '/c', command],
                    capture_output=True,
                    text=True,
                    check=False,
                    creationflags=creationflags,
                )
        else:
            debug_print(f"Executing via bash -c: {command}")
            result = subprocess.run(
                ['bash', '-c', command],
                capture_output=True,
                text=True,
                check=False
            )

        # Print stdout
        if result.stdout:
            print(f"{Colors.GREEN}STDOUT:{Colors.RESET}")
            out = result.stdout.strip()
            # Try to pretty-print JSON if applicable
            pretty_printed = False
            if out:
                # Fast-path: looks like a single JSON value
                trimmed = out.lstrip()
                if (trimmed.startswith('{') and out.rstrip().endswith('}')) or (trimmed.startswith('[') and out.rstrip().endswith(']')):
                    try:
                        data = json.loads(out)
                        formatted = json.dumps(data, indent=2, ensure_ascii=False)
                        print(formatted)
                        pretty_printed = True
                        debug_print("Pretty-printed JSON response")
                    except json.JSONDecodeError:
                        debug_print("STDOUT looked like JSON but failed to parse; printing raw")
            if not pretty_printed:
                print(result.stdout)

        # Print stderr
        if result.stderr:
            print(f"{Colors.RED}STDERR:{Colors.RESET}")
            print(result.stderr)

        debug_print(f"Process exited with code: {result.returncode}")
        if result.returncode != 0:
            print_error(f"cURL execution failed with exit code {result.returncode}")

    except Exception as e:
        print_error(f"Failed to execute command: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('--version', '-v', action='store_true')
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--debug', action='store_true')

    args, unknown = parser.parse_known_args()

    global DEBUG
    DEBUG = bool(args.debug)
    if DEBUG:
        debug_print(f"argv: {sys.argv}")
        debug_print(f"python: {sys.version}")
        debug_print(f"platform: {platform.platform()}")
        debug_print(f"cwd: {os.getcwd()}")

    if args.help:
        show_help()
        return

    if args.version:
        show_version()
        return

    if args.install:
        install_deps()
        return

    # Check dependencies
    check_dependencies()

    # Create template file
    tmpfile = create_template_file()
    debug_print(f"Editor target file: {tmpfile}")

    # Open editor with autocomplete
    open_editor(tmpfile)

    # Extract commands
    commands = extract_commands(tmpfile)

    if not commands:
        print_warning("No uncommented command found. Exiting.")
        return

    # Format JSON if jq is available
    commands = format_json_with_jq(commands)

    # Validate commands
    for cmd in commands:
        debug_print(f"Validating command: {cmd}")
        if not validate_command(cmd):
            print_error(f"Invalid curl command: {cmd}")

    # Show final commands
    print("\n📋 Final command(s) to execute:")
    print("----------------------------------------")
    for cmd in commands:
        print(cmd)
    print("----------------------------------------")

    # Prompt for confirmation
    if not confirm_execution(commands):
        return

    # Execute commands
    for cmd in commands:
        run_command(cmd)

if __name__ == '__main__':
    main()

