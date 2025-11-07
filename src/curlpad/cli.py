"""
Command-line interface for curlpad.

This module provides the main CLI entry point and handles:
    - Argument parsing (--help, --version, --install, --debug)
    - Main application flow
    - User confirmation prompts
    - Orchestrating all modules

Functions:
    confirm_execution(commands: List[str]) -> bool
        Prompt user for confirmation before executing commands
        
    show_help() -> None
        Display help message
        
    show_version() -> None
        Display version information
        
    main() -> None
        Main entry point for the application

Flow:
    1. Parse command-line arguments
    2. Handle --help, --version, --install flags
    3. Check dependencies (curl)
    4. Create template file
    5. Open editor with autocomplete
    6. Extract commands from edited file
    7. Format JSON (if jq available)
    8. Validate commands
    9. Prompt for confirmation
    10. Execute commands
"""

import os
import sys
from typing import List

from curlpad.commands import extract_commands, format_json_with_jq, run_command, validate_command
from curlpad.constants import __version__
from curlpad.dependencies import check_dependencies, install_deps, get_editor
from curlpad.editor import open_editor
from curlpad.output import print_error, print_info, print_warning
from curlpad.templates import create_template_file
from curlpad.utils import DEBUG, debug_print


def confirm_execution(commands: List[str]) -> bool:
    """
    Prompt user for confirmation before executing commands.
    
    Attempts to use stdin for interactive confirmation. If stdin is unavailable
    (e.g., in frozen binaries or non-interactive environments), falls back to:
        - Windows: MessageBox dialog
        - Other platforms: Proceeds without confirmation
    
    Args:
        commands: List of curl commands to be executed
        
    Returns:
        True if user confirms execution, False if cancelled
        
    Flow:
        1. Try to use stdin for interactive prompt
        2. If stdin fails, try Windows MessageBox (if on Windows)
        3. If all fail, proceed without confirmation (with warning)
    """
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


def show_help() -> None:
    """
    Display help message.
    
    Shows usage information, options, examples, and dependencies.
    """
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
    """
    Display version information.
    
    Shows the application version from constants.py.
    """
    print(f"curlpad version {__version__}")


def main() -> None:
    """
    Main entry point for the application.
    
    Orchestrates the entire application flow:
        1. Parse command-line arguments
        2. Handle special flags (--help, --version, --install)
        3. Check dependencies
        4. Create template file
        5. Open editor
        6. Extract and process commands
        7. Execute commands
        
    Command-Line Arguments:
        --help, -h: Show help message and exit
        --version, -v: Show version and exit
        --install: Install dependencies and exit
        --debug: Enable debug mode (verbose logging)
        
    Flow:
        1. Parse arguments
        2. Set DEBUG flag if --debug provided
        3. Handle --help, --version, --install flags
        4. Check curl is installed
        5. Create template file with curl examples
        6. Open editor (nvim/vim) with autocomplete
        7. Extract curl commands from edited file
        8. Format JSON in commands (if jq available)
        9. Validate commands
        10. Display commands to user
        11. Prompt for confirmation
        12. Execute commands one by one
    """
    import argparse
    
    # Initialize argument parser
    # add_help=False: We handle --help manually to show custom help message
    parser = argparse.ArgumentParser(add_help=False)
    
    # Define command-line arguments:
    # --help, -h: Show help message and exit
    # --version, -v: Show version information and exit
    # --install: Install missing dependencies (vim, jq) and exit
    # --debug: Enable verbose debug logging throughout the application
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('--version', '-v', action='store_true')
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--debug', action='store_true')

    # Parse command-line arguments
    # args: Parsed arguments (contains help, version, install, debug flags)
    # unknown: Unrecognized arguments (not used, but kept for compatibility)
    args, unknown = parser.parse_known_args()

    # Set global DEBUG flag
    # This enables verbose logging throughout the application
    # When True, all debug_print() calls will output messages with timestamps
    # Modified in utils.py module, used by all modules via debug_print()
    global DEBUG
    DEBUG = bool(args.debug)
    if DEBUG:
        # Output debug information about the execution environment
        debug_print(f"argv: {sys.argv}")  # Command-line arguments
        debug_print(f"python: {sys.version}")  # Python version
        debug_print(f"platform: {os.name}")  # Operating system (nt=Windows, posix=Unix)
        debug_print(f"cwd: {os.getcwd()}")  # Current working directory

    # Handle early-exit flags (help, version, install)
    # These flags cause the program to exit immediately after displaying information
    if args.help:
        show_help()
        return

    if args.version:
        show_version()
        return

    if args.install:
        install_deps()  # Install vim and jq using platform-specific package managers
        return

    # Check dependencies
    # Verifies that curl is installed (required for executing HTTP requests)
    # Raises SystemExit if curl is not found
    check_dependencies()

    # Create template file
    # Creates a temporary .sh file with commented curl examples
    # Returns: Path to the created template file
    # The file is added to temp_files list for automatic cleanup on exit
    tmpfile = create_template_file()
    debug_print(f"Editor target file: {tmpfile}")

    # Open editor with autocomplete
    # Launches nvim or vim with the template file and autocomplete configuration
    # The editor is opened with cursor at line 8 (empty line in template) in insert mode
    # User edits commands in the editor, then saves and exits
    # Control returns to this function after editor closes
    open_editor(tmpfile)

    # Extract commands from edited template file
    # Parses the file and extracts uncommented curl commands
    # Handles multiline commands, continuation lines, and comments
    # Returns: List of extracted curl commands as strings
    commands = extract_commands(tmpfile)

    # Check if any commands were extracted
    # If no commands found, warn user and exit
    if not commands:
        print_warning("No uncommented command found. Exiting.")
        return

    # Format JSON in commands if jq is available
    # Attempts to format JSON strings in curl commands using jq
    # If jq is not available, returns original commands unchanged
    # This improves readability of JSON payloads in curl commands
    commands = format_json_with_jq(commands)

    # Validate commands
    # Checks each command to ensure it's a valid curl command
    # Basic validation: command must start with 'curl'
    # Raises SystemExit if invalid command is found
    for cmd in commands:
        debug_print(f"Validating command: {cmd}")
        if not validate_command(cmd):
            print_error(f"Invalid curl command: {cmd}")

    # Show final commands to user
    # Displays all commands that will be executed
    # This gives the user a chance to review before execution
    print("\n📋 Final command(s) to execute:")
    print("----------------------------------------")
    for cmd in commands:
        print(cmd)
    print("----------------------------------------")

    # Prompt for confirmation
    # Attempts to use stdin for interactive confirmation
    # Falls back to Windows MessageBox if stdin unavailable
    # Returns: True if user confirms, False if cancelled
    # If False, program exits without executing commands
    if not confirm_execution(commands):
        return

    # Execute commands one by one
    # For each command in the list:
    #   1. Parse command into arguments (platform-specific)
    #   2. Execute via subprocess
    #   3. Capture stdout and stderr
    #   4. Pretty-print JSON if detected in output
    #   5. Display results with appropriate colors
    #   6. Check exit code and display error if non-zero
    for cmd in commands:
        run_command(cmd)

