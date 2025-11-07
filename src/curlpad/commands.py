"""
Command extraction, validation, and execution for curlpad.

This module handles:
    - extract_commands(): Parse template file and extract curl commands
    - format_json_with_jq(): Format JSON in curl commands using jq
    - validate_command(): Validate curl command syntax
    - run_command(): Execute curl commands and display results

Functions:
    extract_commands(tmpfile: str) -> List[str]
        Extract uncommented curl commands from template file
        
    format_json_with_jq(commands: List[str]) -> List[str]
        Format JSON in curl commands using jq if available
        
    validate_command(command: str) -> bool
        Basic validation of curl command syntax
        
    run_command(command: str) -> None
        Execute curl command and display output

Flow:
    1. extract_commands() reads template file and extracts curl commands
    2. format_json_with_jq() formats any JSON in commands (optional)
    3. validate_command() checks each command is valid
    4. run_command() executes each command and displays results
"""

import json
import os
import re
import shlex
import shutil
import subprocess
from typing import List

from curlpad.constants import Colors
from curlpad.dependencies import check_command
from curlpad.output import print_error, print_warning
from curlpad.utils import debug_print


def extract_commands(tmpfile: str) -> List[str]:
    """
    Extract uncommented curl commands from template file.
    
    Parses the template file and extracts curl commands, handling:
        - Multiline commands (lines ending with \)
        - Continuation lines (lines starting with - or indented)
        - Commented lines (ignored)
        - Empty lines (ignored)
    
    Args:
        tmpfile: Path to the template file to parse
        
    Returns:
        List of extracted curl commands as strings
        
    Raises:
        SystemExit: If file read fails
        
    Command Extraction Rules:
        1. Ignore empty lines and comment lines (starting with #)
        2. Start new command when line starts with 'curl'
        3. Continue command if line ends with '\' (backslash continuation)
        4. Continue command if line starts with '-' (curl option)
        5. Continue command if line is indented (multiline format)
        6. Join continuation lines with single spaces
        
    Flow:
        1. Read all lines from template file
        2. Filter out comments and empty lines
        3. Identify command starts (lines starting with 'curl')
        4. Collect continuation lines
        5. Join lines into complete commands
        6. Return list of commands
    """
    # raw_lines: List of all lines from the template file (preserving original format)
    # Each line is stripped of trailing newline but preserves leading whitespace
    raw_lines: List[str] = []
    try:
        with open(tmpfile, 'r') as f:
            for raw in f:
                raw_lines.append(raw.rstrip('\n'))
    except OSError as e:
        print_error(f"Failed to read temp file: {e}")

    # Filter out comments and empty lines, but preserve indentation for continuation detection
    # filtered: List of non-comment, non-empty lines with original indentation preserved
    # This is important for detecting continuation lines (indented lines continue previous command)
    filtered: List[str] = []
    for raw in raw_lines:
        if not raw.strip():  # Skip empty lines
            continue
        if raw.lstrip().startswith('#'):  # Skip comment lines (starting with #)
            continue
        filtered.append(raw)  # Keep line with original indentation

    # coalesced: Final list of complete curl commands (one command per string)
    # Each command is a single string with all continuation lines joined
    coalesced: List[str] = []
    
    # current: List of lines that form the current command being built
    # Lines are collected here until the command is complete, then joined and added to coalesced
    current: List[str] = []

    def flush_current():
        """
        Join current command parts and add to coalesced list.
        
        This function is called when a command is complete (no more continuation lines).
        It joins all lines in 'current' into a single command string and adds it to 'coalesced'.
        Then it clears 'current' to start building the next command.
        
        Flow:
        1. Check if current has any lines
        2. Join all lines with single spaces (stripping each part)
        3. If joined string is not empty, add to coalesced
        4. Clear current list for next command
        """
        nonlocal current
        if current:
            # Join with single spaces
            # Each part is stripped of whitespace, then joined with single space
            # This handles cases where lines have extra whitespace
            joined = ' '.join(part.strip() for part in current if part.strip())
            if joined:
                coalesced.append(joined)
        current = []

    # Process each filtered line to extract curl commands
    for raw in filtered:
        # line: Line with trailing whitespace removed
        # lstrip: Line with leading whitespace removed (used for checking if line starts with 'curl' or '-')
        line = raw.rstrip()
        lstrip = raw.lstrip()
        
        # Determine if line is continuation of previous command
        # is_continuation: True if this line continues the previous command, False if it starts a new command
        # Continuation is detected if:
        #   1. Line ends with '\' (backslash continuation)
        #   2. Line starts with '-' (curl option, continues previous curl command)
        #   3. Line is indented (multiline format, continues previous command)
        is_continuation = False
        if current:  # If we're building a command
            if line.endswith('\\'):
                is_continuation = True
                line = line[:-1].rstrip()  # Remove trailing backslash
            elif lstrip.startswith('-'):  # Line starts with curl option
                is_continuation = True
            elif raw != lstrip:  # Line is indented (has leading whitespace)
                is_continuation = True

        if not current:
            # Start new command only when 'curl' begins the line (ignoring leading spaces)
            if lstrip.startswith('curl'):
                # Handle trailing backslash on curl line
                if line.endswith('\\'):
                    current.append(line[:-1].rstrip())  # Add line without backslash
                else:
                    current.append(line)  # Add complete single-line command
                    flush_current()  # Command is complete, flush it
            else:
                debug_print(f"Skipping non-curl leading line: {raw}")
        else:
            # Continuation for existing curl command
            current.append(line)  # Add line to current command
            if not is_continuation:  # If this line doesn't continue, command is complete
                flush_current()  # Flush current command and start new one

    # Flush at end to handle last command (in case file doesn't end with newline)
    flush_current()

    debug_print(f"Extracted {len(coalesced)} curl command(s) from {tmpfile}")
    return coalesced


def format_json_with_jq(commands: List[str]) -> List[str]:
    """
    Format JSON in curl commands using jq if available.
    
    Attempts to format JSON strings in curl commands using jq.
    If jq is not available or formatting fails, returns original commands.
    
    Args:
        commands: List of curl command strings
        
    Returns:
        List of commands with JSON formatted (if jq available)
        
    Flow:
        1. Check if jq is available
        2. For each command, search for JSON in -d flag
        3. Extract JSON string and format with jq
        4. Replace original JSON with formatted version
        5. Return formatted commands
    """
    if not check_command('jq'):
        debug_print("jq not found; skipping JSON formatting")
        return commands

    # formatted_commands: List of commands with JSON formatted (if jq available)
    # Starts as empty list, commands are added one by one
    # Each command is either formatted (if JSON found) or original (if no JSON or jq fails)
    formatted_commands = []

    # Process each command to format JSON if present
    for line in commands:
        # original_line: Original command string before formatting
        # Kept for comparison and debug output
        original_line = line
        
        # Look for curl commands with -d containing JSON
        # pattern: Regular expression to match JSON in curl -d flag
        # Matches: (before -d flag)(JSON object)(after JSON)
        # Example: curl -X POST "url" -d '{"key":"value"}' -> matches '{"key":"value"}'
        pattern = r'(.*curl.*-d\s*[\'"])({[^}]*})([\'"].*)'
        match = re.search(pattern, line)

        if match:
            # match: Regex match object if JSON found in command
            # before: Part of command before JSON (curl command and -d flag)
            # json_str: JSON string extracted from command
            # after: Part of command after JSON (closing quote and rest of command)
            before, json_str, after = match.groups()
            try:
                # Format JSON using jq
                # result: CompletedProcess from jq subprocess
                # jq -c '.': Format JSON in compact mode (single line)
                # input=json_str: Pass JSON string to jq via stdin
                # text=True: Return output as string (not bytes)
                # capture_output=True: Capture stdout and stderr
                # check=True: Raise exception if jq fails
                result = subprocess.run(
                    ['jq', '-c', '.'],
                    input=json_str,
                    text=True,
                    capture_output=True,
                    check=True
                )
                # formatted_json: JSON string formatted by jq (compact format)
                # result.stdout.strip(): Remove trailing newline from jq output
                formatted_json = result.stdout.strip()
                # line: Reconstructed command with formatted JSON
                # Combines before, formatted_json, and after parts
                line = f"{before}{formatted_json}{after}"
                debug_print(f"Formatted JSON in command: {original_line} -> {line}")
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                # If jq fails (command not found or invalid JSON), keep original command
                # subprocess.CalledProcessError: jq command failed
                # json.JSONDecodeError: JSON was invalid (shouldn't happen, but safe to catch)
                debug_print("jq failed to format JSON; keeping original line")
                pass

        # Add command to formatted list (either formatted or original)
        formatted_commands.append(line)

    return formatted_commands


def validate_command(command: str) -> bool:
    """
    Basic validation of curl command syntax.
    
    Performs simple validation to ensure the command looks like a valid
    curl command. This is not comprehensive validation, just basic checks.
    
    Args:
        command: Curl command string to validate
        
    Returns:
        True if command appears valid, False otherwise
        
    Validation Rules:
        1. Command must start with 'curl' (after stripping whitespace)
        2. Basic structure check (curl followed by options/URL)
    """
    # Check if it starts with curl
    if not command.strip().startswith('curl'):
        return False

    # Basic syntax check - curl followed by options/URL
    # This is a simple check, real validation would be complex
    return True


def run_command(command: str) -> None:
    """
    Execute curl command and display output.
    
    Executes the curl command using subprocess and displays the results.
    Handles platform-specific execution (Windows vs Unix).
    Attempts to pretty-print JSON responses if applicable.
    
    Args:
        command: Curl command string to execute
        
    Raises:
        SystemExit: If command execution fails
        
    Platform Handling:
        - Windows: Uses shlex.split() or cmd.exe fallback
        - Unix: Uses bash -c for execution
        
    Output Formatting:
        - STDOUT: Displayed in green, JSON is pretty-printed if detected
        - STDERR: Displayed in red
        - Exit code: Checked and error displayed if non-zero
        
    Flow:
        1. Parse command into arguments (platform-specific)
        2. Execute command via subprocess
        3. Capture stdout and stderr
        4. Attempt to pretty-print JSON in stdout
        5. Display output with appropriate colors
        6. Check exit code and display error if non-zero
    """
    try:
        print(f"\n{Colors.CYAN}▶ Running your cURL command...{Colors.RESET}")

        if os.name == 'nt':
            # Windows execution
            # Windows requires special handling because:
            # 1. Command parsing is different (shlex.split with posix=True works for most cases)
            # 2. Need to find curl.exe explicitly (may be curl.exe or curl)
            # 3. May need to fall back to cmd.exe if parsing fails
            debug_print(f"Executing directly (Windows): {command}")
            try:
                # args: List of command arguments parsed from command string
                # shlex.split() splits the command string into a list of arguments
                # posix=True: Use POSIX-style splitting (handles quotes correctly)
                args = shlex.split(command, posix=True)
            except ValueError as exc:
                # If parsing fails (e.g., complex quoting), fall back to cmd.exe
                print_warning(f"Failed to parse command; running via cmd.exe: {exc}")
                args = None

            # creationflags: Windows-specific subprocess flags
            # CREATE_NO_WINDOW: Prevents creating a new console window for the subprocess
            # This keeps output in the current console window
            creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

            if args:
                # If parsing succeeded, execute directly
                if args and args[0].lower() == 'curl':
                    # Find curl executable (may be curl.exe or curl)
                    # curl_exe: Path to curl executable, or None if not found
                    curl_exe = shutil.which('curl.exe') or shutil.which('curl')
                    if curl_exe:
                        args[0] = curl_exe  # Use full path to curl
                    else:
                        args[0] = 'curl.exe'  # Fallback to curl.exe (may fail if not in PATH)
                
                # result: CompletedProcess object containing stdout, stderr, returncode
                # capture_output=True: Capture both stdout and stderr
                # text=True: Return output as strings (not bytes)
                # check=False: Don't raise exception on non-zero exit code
                # creationflags: Windows-specific flag to prevent new console window
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    check=False,
                    creationflags=creationflags,
                )
            else:
                # Fallback: Execute via cmd.exe if parsing failed
                # This handles complex commands that shlex.split can't parse
                result = subprocess.run(
                    ['cmd', '/c', command],
                    capture_output=True,
                    text=True,
                    check=False,
                    creationflags=creationflags,
                )
        else:
            # Unix execution (Linux, macOS)
            # Unix systems can execute commands directly via bash
            # bash -c: Execute command string in bash shell
            debug_print(f"Executing via bash -c: {command}")
            result = subprocess.run(
                ['bash', '-c', command],
                capture_output=True,
                text=True,
                check=False
            )

        # Print stdout (standard output from curl command)
        if result.stdout:
            print(f"{Colors.GREEN}STDOUT:{Colors.RESET}")
            # out: Stripped stdout (removes leading/trailing whitespace)
            out = result.stdout.strip()
            
            # Try to pretty-print JSON if applicable
            # pretty_printed: Flag indicating if JSON was detected and formatted
            # If True, JSON was found and pretty-printed; if False, output is printed as-is
            pretty_printed = False
            if out:
                # Fast-path: Check if output looks like JSON
                # trimmed: Output with leading whitespace removed (for checking start)
                # Check if output starts with { or [ and ends with } or ]
                trimmed = out.lstrip()
                if (trimmed.startswith('{') and out.rstrip().endswith('}')) or (trimmed.startswith('[') and out.rstrip().endswith(']')):
                    try:
                        # data: Parsed JSON object (dict or list)
                        data = json.loads(out)
                        # formatted: Pretty-printed JSON string with 2-space indentation
                        # ensure_ascii=False: Allow Unicode characters in output
                        formatted = json.dumps(data, indent=2, ensure_ascii=False)
                        print(formatted)
                        pretty_printed = True
                        debug_print("Pretty-printed JSON response")
                    except json.JSONDecodeError:
                        # If JSON parsing fails, output didn't contain valid JSON
                        debug_print("STDOUT looked like JSON but failed to parse; printing raw")
            if not pretty_printed:
                # If JSON not detected or parsing failed, print output as-is
                print(result.stdout)

        # Print stderr (error output from curl command)
        # stderr typically contains warnings, errors, or verbose output
        if result.stderr:
            print(f"{Colors.RED}STDERR:{Colors.RESET}")
            print(result.stderr)

        # Check exit code
        # result.returncode: Exit code from curl command
        # 0 = success, non-zero = error
        debug_print(f"Process exited with code: {result.returncode}")
        if result.returncode != 0:
            print_error(f"cURL execution failed with exit code {result.returncode}")

    except Exception as e:
        print_error(f"Failed to execute command: {e}")

