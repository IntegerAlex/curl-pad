#!/usr/bin/env python3

# curlpad - A simple curl editor for the command line
# Copyright (C) 2023-2025 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
#
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

import sys
import os
import subprocess
import tempfile
import shutil
import re
import argparse
import json
import platform
import signal

VERSION = "2.0.0"

# The template to write to the temporary script file
SCRIPT_TEMPLATE = """#!/bin/bash
# curlpad - scratchpad for curl.
# AUTHOR - Akshat Kotpalliwar (alias IntegerAlex)
# Use Ctrl-X Ctrl-K for autocomplete in vim
# curl -X POST "https://api.example.com" \\
#   -H "Content-Type: application/json" \\
#   -d '{"key":"value"}'

"""

# Updated vimrc template with autocomplete and syntax highlighting
VIMRC_TEMPLATE = """set nocompatible
syntax on
filetype plugin indent on
set filetype=sh
set number
set autoindent
set tabstop=2
set shiftwidth=2
set expandtab
set backspace=indent,eol,start

" --- Custom Curl Highlighting ---
syntax keyword curlCommand curl
syntax keyword curlMethod GET POST PUT DELETE PATCH HEAD OPTIONS
syntax match curlFlag /-\([A-Za-z]\)\>/
syntax match curlFlag /--\([a-zA-Z0-9-]\+\)/

hi def link curlCommand Statement
hi def link curlMethod Constant
hi def link curlFlag Identifier

" --- Autocomplete ---
set dictionary+={dictionary_path}
set complete+=k

" --- Key mappings for easier exit ---
" Allow :q to work even if file is modified
set hidden
"""

# Comprehensive curl completions
CURL_COMPLETIONS = [
    "curl",
    # HTTP Methods
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "CONNECT",
    # Common short flags
    "-X", "-H", "-d", "-i", "-I", "-s", "-S", "-L", "-o", "-O",
    "-v", "-u", "-b", "-c", "-k", "-A", "-e", "-f", "-w", "-D",
    # Common long flags
    "--request", "--header", "--data", "--data-raw", "--data-binary",
    "--data-urlencode", "--json", "--include", "--head", "--silent",
    "--show-error", "--location", "--output", "--remote-name", "--verbose",
    "--user", "--cookie", "--cookie-jar", "--insecure", "--user-agent",
    "--referer", "--compressed", "--max-time", "--connect-timeout",
    "--retry", "--retry-delay", "--form", "--upload-file", "--get",
    "--proxy", "--url", "--fail", "--write-out", "--dump-header",
    # Common headers
    "Content-Type: application/json",
    "Content-Type: application/x-www-form-urlencoded",
    "Content-Type: text/plain",
    "Content-Type: multipart/form-data",
    "Accept: application/json",
    "Accept: */*",
    "Authorization: Bearer ",
    "Authorization: Basic ",
    "User-Agent: Mozilla/5.0",
    "Cache-Control: no-cache",
    # Common URLs/patterns
    "https://api.example.com",
    "http://localhost:8080",
    "http://localhost:3000",
    "https://",
    "http://",
]

def find_editor():
    """Finds 'vim' or 'vi' in the user's PATH."""
    editor = shutil.which('vim')
    if editor:
        return editor, 'vim'
    
    editor = shutil.which('vi')
    if editor:
        return editor, 'vi'
        
    print("Error: Neither vim nor vi is installed or in your PATH.", file=sys.stderr)
    print("Please install vim to use this tool.", file=sys.stderr)
    sys.exit(1)

def format_json_in_file(script_path):
    """
    Finds curl commands with -d '{"json"}' and formats the JSON.
    """
    json_pattern = re.compile(r"(.+-d\s*['\"])(\{.+?\})(['\"].*$)", re.DOTALL)
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f_in:
            content = f_in.read()
        
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                match = json_pattern.search(line)
                if match:
                    before, json_str, after = match.groups()
                    try:
                        parsed_json = json.loads(json_str)
                        formatted_json = json.dumps(parsed_json, separators=(',', ':'), ensure_ascii=False)
                        formatted_lines.append(f"{before}{formatted_json}{after}")
                    except (json.JSONDecodeError, ValueError):
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)

        with open(script_path, 'w', encoding='utf-8') as f_out:
            f_out.write('\n'.join(formatted_lines))
            
    except IOError as e:
        print(f"Error: Could not read/write file {script_path}: {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Warning: Could not format JSON. Error: {e}", file=sys.stderr)

def get_uncommented_commands(script_path):
    """Extracts all executable (uncommented) lines from the script."""
    commands = []
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    commands.append(stripped)
    except IOError as e:
        print(f"Error: Could not read script file: {e}", file=sys.stderr)
        raise
    
    return commands

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    print("\n\nInterrupted by user. Cleaning up...", file=sys.stderr)
    sys.exit(130)

def main_app():
    """The main application logic."""
    
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if platform.system() == "Windows":
        print("Error: This tool is designed for Linux/macOS and requires bash.", file=sys.stderr)
        print("It is not compatible with Windows (cmd.exe or PowerShell).", file=sys.stderr)
        sys.exit(1)

    try:
        editor_path, editor_name = find_editor()
    except SystemExit:
        raise
    except Exception as e:
        print(f"Error: Failed to find editor: {e}", file=sys.stderr)
        sys.exit(1)
    
    tmp_script_fd = None
    tmp_vimrc_fd = None
    tmp_dict_fd = None
    tmp_script_path = None
    tmp_vimrc_path = None
    tmp_dict_path = None

    try:
        # Create temp files
        tmp_script_fd, tmp_script_path = tempfile.mkstemp(suffix='.sh', text=True)
        tmp_vimrc_fd, tmp_vimrc_path = tempfile.mkstemp(suffix='.vimrc', text=True)
        tmp_dict_fd, tmp_dict_path = tempfile.mkstemp(suffix='.dict', text=True)
        
        # Write script template
        try:
            with os.fdopen(tmp_script_fd, 'w', encoding='utf-8') as f:
                f.write(SCRIPT_TEMPLATE)
                tmp_script_fd = None  # Prevent double close
        except Exception as e:
            print(f"Error writing script template: {e}", file=sys.stderr)
            raise
        
        # Write autocomplete dictionary
        try:
            with os.fdopen(tmp_dict_fd, 'w', encoding='utf-8') as f:
                f.write("\n".join(CURL_COMPLETIONS))
                tmp_dict_fd = None  # Prevent double close
        except Exception as e:
            print(f"Error writing dictionary: {e}", file=sys.stderr)
            raise
        
        # Write vimrc
        try:
            with os.fdopen(tmp_vimrc_fd, 'w', encoding='utf-8') as f:
                f.write(VIMRC_TEMPLATE.format(dictionary_path=tmp_dict_path))
                tmp_vimrc_fd = None  # Prevent double close
        except Exception as e:
            print(f"Error writing vimrc: {e}", file=sys.stderr)
            raise

        # Display usage tips
        if editor_name == 'vim':
            print("\n" + "=" * 60)
            print("💡 CURLPAD EDITOR TIPS:")
            print("   • Use Ctrl-X Ctrl-K for curl command autocomplete")
            print("   • Press 'i' to enter insert mode")
            print("   • Press ESC to exit insert mode")
            print("   • Type :wq and press Enter to save and exit")
            print("   • Type :q! and press Enter to exit without saving")
            print("=" * 60 + "\n")

        # Open the editor
        cmd_args = [editor_path]
        if editor_name == 'vim':
            cmd_args.extend(['-u', tmp_vimrc_path, '-c', '8', '-c', 'startinsert', tmp_script_path])
        else:
            # vi doesn't support as many features
            cmd_args.extend(['+8', tmp_script_path])

        # Run editor with proper error handling
        try:
            result = subprocess.run(cmd_args, check=False)
            # Exit codes: 0 = normal, 1 = vim exited with :cq or error
            if result.returncode not in [0, 1]:
                print(f"Warning: Editor exited with code {result.returncode}", file=sys.stderr)
        except subprocess.SubprocessError as e:
            print(f"Error: Failed to run editor: {e}", file=sys.stderr)
            return
        except FileNotFoundError:
            print(f"Error: Editor not found: {editor_path}", file=sys.stderr)
            return
        except KeyboardInterrupt:
            print("\nEditor interrupted. Exiting.", file=sys.stderr)
            return

        # Check if file was modified
        if not os.path.exists(tmp_script_path):
            print("Error: Script file was deleted.", file=sys.stderr)
            return

        # Check file size to ensure content exists
        file_stat = os.stat(tmp_script_path)
        if file_stat.st_size == 0:
            print("No content in file. Exiting.")
            return

        # Format JSON
        try:
            format_json_in_file(tmp_script_path)
        except Exception as e:
            print(f"Error during JSON formatting: {e}", file=sys.stderr)
        
        # Get commands
        try:
            commands = get_uncommented_commands(tmp_script_path)
        except Exception as e:
            print(f"Error reading commands: {e}", file=sys.stderr)
            return
        
        if not commands:
            print("No uncommented command found. Exiting.")
            return

        # Show final commands and ask for confirmation
        print("\n📋 Final command(s) to execute:")
        print("-" * 60)
        for cmd in commands:
            print(cmd)
        print("-" * 60)

        try:
            response = input("\nPress Enter to run, or Ctrl+C to cancel... ")
        except KeyboardInterrupt:
            print("\n\nCancelled by user. Exiting.")
            return
        except EOFError:
            print("\n\nEOF received. Exiting.")
            return

        # Run commands
        print("\n▶ Running your cURL command(s)...\n")
        all_commands = "\n".join(commands)
        
        try:
            result = subprocess.run(
                ['bash', '-c', all_commands],
                check=False,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"\n⚠ Warning: Command exited with code {result.returncode}", file=sys.stderr)
            else:
                print("\n✓ Command executed successfully")
                
        except subprocess.TimeoutExpired:
            print("\n✗ Error: Command execution timed out after 5 minutes", file=sys.stderr)
        except subprocess.SubprocessError as e:
            print(f"\n✗ Error executing commands: {e}", file=sys.stderr)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.", file=sys.stderr)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Guaranteed cleanup - close any open file descriptors
        for fd in [tmp_script_fd, tmp_vimrc_fd, tmp_dict_fd]:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        
        # Remove temp files
        for path in [tmp_script_path, tmp_vimrc_path, tmp_dict_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError as e:
                    print(f"Warning: Could not remove temp file {path}: {e}", file=sys.stderr)

def main():
    """Entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="curlpad - A simple curl editor for Linux and macOS.",
        epilog="Examples:\n"
               "  curlpad           # Start interactive curl editor\n"
               "  curlpad --version # Show version info\n"
               "\n"
               "Editor shortcuts:\n"
               "  Ctrl-X Ctrl-K     # Autocomplete (vim only)\n"
               "  :wq               # Save and exit\n"
               "  :q!               # Exit without saving",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'curlpad version {VERSION}'
    )
    
    try:
        args = parser.parse_args()
        main_app()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Exiting.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
