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

_ALLOWED_CMD = "curl"
# Blocklist for known dangerous flags
_BLOCKED_FLAGS = {"--exec", "-e", "--eval", "-K", "--config", "--write-out", "-w"}
# Allowlist: Only permit known-safe flags (security-first approach)
_ALLOWED_FLAGS = {
    "-X", "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS",
    "-H", "--header", "-d", "--data", "--data-raw", "--data-binary", "--data-urlencode",
    "--url", "-i", "--include", "-v", "--verbose", "-s", "--silent", "-S", "--show-error",
    "-o", "--output", "-O", "--remote-name", "-L", "--location", "-k", "--insecure",
    "--connect-timeout", "--max-time", "-m", "--max-redirs",
    "-u", "--user", "-x", "--proxy", "--proxy-user",
    "-A", "--user-agent", "-b", "--cookie", "-c", "--cookie-jar",
    "-e", "--referer", "-f", "--fail", "-I", "--head",
    "--compressed", "--digest", "--negotiate", "--ntlm", "--basic",
    "--cert", "--key", "--cacert", "--capath",
    "-4", "-6", "--ipv4", "--ipv6",
    "-g", "--globoff", "-j", "--junk-session-cookies",
    "-1", "--tlsv1", "--tlsv1.0", "--tlsv1.1", "--tlsv1.2", "--tlsv1.3",
    "--ssl", "--ssl-reqd", "--sslv2", "--sslv3",
    "-#", "--progress-bar", "-N", "--no-buffer",
    "--raw", "--tr-encoding", "--no-keepalive", "--no-sessionid",
    "--noproxy", "--local-port", "--interface", "--dns-servers",
    "--keepalive-time", "--no-alpn", "--no-npn",
    "--http1.0", "--http1.1", "--http2", "--http2-prior-knowledge",
    "-0", "--http1.0"
}
# Dangerous shell metacharacters to block in entire command
_DANGEROUS_PATTERNS = ['&&', '||', ';', '|', '$', '`', '$(', '${', '>', '<', '\n', '\r']


def extract_commands(tmpfile: str) -> List[str]:
    """
    Extract uncommented curl commands from template file.
    
    Parses the template file and extracts curl commands, handling:
        - Multiline commands (lines ending with backslash)
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
    debug_print(f"Extracting commands from template file: {tmpfile}")
    
    # raw_lines: List of all lines from the template file (preserving original format)
    # Each line is stripped of trailing newline but preserves leading whitespace
    raw_lines: List[str] = []
    try:
        with open(tmpfile, 'r') as f:
            for raw in f:
                raw_lines.append(raw.rstrip('\n'))
        debug_print(f"Read {len(raw_lines)} lines from template file")
    except OSError as e:
        debug_print(f"Failed to read temp file {tmpfile}: {e}")
        print_error(f"Failed to read temp file: {e}")

    # Filter out comments and empty lines, but preserve indentation for continuation detection
    # filtered: List of non-comment, non-empty lines with original indentation preserved
    # This is important for detecting continuation lines (indented lines continue previous command)
    filtered: List[str] = []
    comments_count = 0
    empty_count = 0
    for raw in raw_lines:
        if not raw.strip():  # Skip empty lines
            empty_count += 1
            continue
        if raw.lstrip().startswith('#'):  # Skip comment lines (starting with #)
            comments_count += 1
            continue
        filtered.append(raw)  # Keep line with original indentation
    
    debug_print(f"Filtered {len(filtered)} non-comment lines (skipped {comments_count} comments, {empty_count} empty lines)")

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
    command_count = 0
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
                debug_print(f"Detected backslash continuation on line: {raw[:80]}")
            elif lstrip.startswith('-'):  # Line starts with curl option
                is_continuation = True
                debug_print(f"Detected option continuation on line: {raw[:80]}")
            elif raw != lstrip:  # Line is indented (has leading whitespace)
                is_continuation = True
                debug_print(f"Detected indented continuation on line: {raw[:80]}")

        if not current:
            # Start new command only when 'curl' begins the line (ignoring leading spaces)
            if lstrip.startswith('curl'):
                command_count += 1
                debug_print(f"Starting new curl command #{command_count}: {line[:80]}")
                # Handle trailing backslash on curl line
                if line.endswith('\\'):
                    current.append(line[:-1].rstrip())  # Add line without backslash
                    debug_print(f"Command continues on next line (backslash detected)")
                else:
                    current.append(line)  # Add complete single-line command
                    flush_current()  # Command is complete, flush it
            else:
                debug_print(f"Skipping non-curl leading line: {raw[:80]}")
        else:
            # Continuation for existing curl command
            current.append(line)  # Add line to current command
            debug_print(f"Adding continuation line to command: {line[:80]}")
            if not is_continuation:  # If this line doesn't continue, command is complete
                flush_current()  # Flush current command and start new one

    # Flush at end to handle last command (in case file doesn't end with newline)
    flush_current()

    debug_print(f"Extracted {len(coalesced)} curl command(s) from {tmpfile}")
    for i, cmd in enumerate(coalesced, 1):
        debug_print(f"  Command {i}: {cmd[:100]}{'...' if len(cmd) > 100 else ''}")
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
    debug_print(f"Formatting JSON in {len(commands)} command(s) using jq")
    
    if not check_command('jq'):
        debug_print("jq not found; skipping JSON formatting")
        return commands

    debug_print("jq found, attempting to format JSON in commands")

    # formatted_commands: List of commands with JSON formatted (if jq available)
    # Starts as empty list, commands are added one by one
    # Each command is either formatted (if JSON found) or original (if no JSON or jq fails)
    formatted_commands = []

    # Process each command to format JSON if present
    for i, line in enumerate(commands, 1):
        debug_print(f"Processing command {i}/{len(commands)} for JSON formatting")
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
            debug_print(f"Found JSON in command {i}, attempting to format")
            # match: Regex match object if JSON found in command
            # before: Part of command before JSON (curl command and -d flag)
            # json_str: JSON string extracted from command
            # after: Part of command after JSON (closing quote and rest of command)
            before, json_str, after = match.groups()
            try:
                debug_print(f"Extracted JSON string: {json_str[:50]}{'...' if len(json_str) > 50 else ''}")
                # Format JSON using jq
                # result: CompletedProcess from jq subprocess
                # jq -c '.': Format JSON in compact mode (single line)
                # input=json_str: Pass JSON string to jq via stdin
                # text=True: Return output as string (not bytes)
                # capture_output=True: Capture stdout and stderr
                # check=True: Raise exception if jq fails
                debug_print(f"Running jq to format JSON: jq -c .")
                result = subprocess.run(
                    ['jq', '-c', '.'],
                    input=json_str,
                    text=True,
                    capture_output=True,
                    check=True
                )
                debug_print(f"jq completed: returncode={result.returncode}, stdout_len={len(result.stdout)}")
                # formatted_json: JSON string formatted by jq (compact format)
                # result.stdout.strip(): Remove trailing newline from jq output
                formatted_json = result.stdout.strip()
                debug_print(f"Formatted JSON: {formatted_json[:50]}{'...' if len(formatted_json) > 50 else ''}")
                # line: Reconstructed command with formatted JSON
                # Combines before, formatted_json, and after parts
                line = f"{before}{formatted_json}{after}"
                debug_print(f"Formatted JSON in command {i}: {original_line[:80]}... -> {line[:80]}...")
            except subprocess.CalledProcessError as e:
                # If jq fails (command not found or invalid JSON), keep original command
                debug_print(f"jq failed to format JSON (returncode={e.returncode}): {e.stderr[:100] if e.stderr else 'no stderr'}")
                debug_print("Keeping original command line")
                pass
            except json.JSONDecodeError as e:
                # JSON was invalid (shouldn't happen, but safe to catch)
                debug_print(f"JSON decode error: {e}")
                debug_print("Keeping original command line")
                pass

        # Add command to formatted list (either formatted or original)
        formatted_commands.append(line)
        debug_print(f"Added command {i} to formatted list")

    debug_print(f"JSON formatting complete: {len(formatted_commands)} command(s) processed")
    return formatted_commands


def validate_command(command: str) -> bool:
    """
    Strict allowlist-based validation of curl command syntax.

    Performs comprehensive validation to ensure the command is safe and
    looks like a valid curl command.

    Args:
        command: Curl command string to validate

    Returns:
        True if command appears valid, False otherwise

    Validation Rules:
        1. Command must start with 'curl' (after stripping whitespace)
        2. Block multiline commands (newlines, carriage returns)
        3. Block dangerous shell metacharacters (&&, ||, ;, |, $, `, etc.)
        4. Use allowlist for flags - only permit known-safe curl options
        5. Block known dangerous flags (--exec, -K/--config, -w/--write-out)
        6. Use shlex parsing to ensure proper command structure
    """
    try:
        cmd = command.strip()
        
        # Basic validation
        if not cmd:
            debug_print("Validation failed: empty command")
            return False
        
        # Block multiline commands
        if '\n' in cmd or '\r' in cmd:
            debug_print("Validation failed: multiline command detected")
            return False
        
        # Block dangerous shell metacharacters in entire command
        for pattern in _DANGEROUS_PATTERNS:
            if pattern in cmd:
                debug_print(f"Validation failed: dangerous pattern '{pattern}' detected")
                return False
        
        # Parse command safely
        debug_print(f"Parsing command with shlex.split (posix=True)...")
        parts = shlex.split(cmd, posix=True)
        debug_print(f"Parsed into {len(parts)} parts: {parts[:5]}{'...' if len(parts) > 5 else ''}")
        
        # Must start with 'curl'
        if not parts or parts[0] != _ALLOWED_CMD:
            debug_print(f"Validation failed: command must start with 'curl', got '{parts[0] if parts else 'empty'}'")
            return False
        
        debug_print(f"Command starts with '{_ALLOWED_CMD}', validating {len(parts) - 1} argument(s)...")
        
        # Validate each argument
        i = 1
        while i < len(parts):
            part = parts[i]
            debug_print(f"  Validating part {i}/{len(parts)-1}: {part[:50]}{'...' if len(part) > 50 else ''}")
            
            # Check if it's a flag
            if part.startswith('-'):
                # Extract flag name (handle -X GET vs --header=value)
                flag = part.split('=')[0]
                debug_print(f"    Detected flag: {flag}")
                
                # Block explicitly dangerous flags
                if flag in _BLOCKED_FLAGS:
                    debug_print(f"    Validation failed: blocked flag '{flag}' detected")
                    return False
                
                # Allowlist validation: Only permit known-safe flags
                if flag not in _ALLOWED_FLAGS:
                    debug_print(f"    Validation failed: unknown/disallowed flag '{flag}' (not in allowlist)")
                    return False
                debug_print(f"    Flag '{flag}' is allowed")
            else:
                # Non-flag argument (URL, header value, data, etc.)
                debug_print(f"    Non-flag argument detected, checking for shell metacharacters...")
                # Check for shell metacharacters in arguments too
                for pattern in ['`', '$(', '${']:
                    if pattern in part:
                        debug_print(f"    Validation failed: shell metacharacter '{pattern}' in argument '{part[:50]}'")
                        return False
                debug_print(f"    Argument validated: no shell metacharacters")
            
            i += 1
        
        debug_print(f"Validation passed for command: {cmd[:100]}...")
        return True
        
    except (ValueError, AttributeError) as e:
        debug_print(f"Validation failed: parsing error - {e}")
        return False


def run_curl_command(command: str, *, windows: bool = False):
    """
    Execute curl command safely with validation.

    Args:
        command: Curl command string to execute
        windows: Whether running on Windows (affects parsing)

    Returns:
        subprocess.CompletedProcess object

    Raises:
        ValueError: If command validation fails
        RuntimeError: If command execution fails
    """
    debug_print(f"run_curl_command called: windows={windows}, command length={len(command)}")
    
    if not validate_command(command):
        debug_print(f"Command validation failed, raising ValueError")
        raise ValueError(f"Invalid curl command: {command!r}")
    
    debug_print(f"Command validation passed, parsing command")
    try:
        parts = shlex.split(command, posix=not windows)
        debug_print(f"Parsed command into {len(parts)} arguments: {parts[:5]}{'...' if len(parts) > 5 else ''}")
        debug_print(f"Executing subprocess.run with shell=False (security: no shell execution)")
        # Never use shell=True
        result = subprocess.run(parts, capture_output=True, text=True, check=False)
        debug_print(f"Subprocess completed: returncode={result.returncode}, stdout_len={len(result.stdout)}, stderr_len={len(result.stderr)}")
        return result
    except (ValueError, OSError) as e:
        debug_print(f"Command execution failed: {type(e).__name__}: {e}")
        raise RuntimeError(f"Command execution failed: {e}") from e


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
    debug_print(f"run_command called with command: {command[:100]}{'...' if len(command) > 100 else ''}")
    debug_print(f"Platform: {os.name} (windows={os.name == 'nt'})")
    
    try:
        print(f"\n{Colors.CYAN}▶ Running your cURL command...{Colors.RESET}")

        # Use the hardened command execution
        try:
            debug_print(f"Calling run_curl_command with windows={os.name == 'nt'}")
            result = run_curl_command(command, windows=(os.name == 'nt'))
            debug_print(f"Command execution successful: returncode={result.returncode}")
        except (ValueError, RuntimeError) as e:
            debug_print(f"Command execution failed with {type(e).__name__}: {e}")
            print_error(f"Command execution failed: {e}")
            return

        # Print stdout (standard output from curl command)
        if result.stdout:
            debug_print(f"STDOUT received: {len(result.stdout)} bytes")
            print(f"{Colors.GREEN}STDOUT:{Colors.RESET}")
            # out: Stripped stdout (removes leading/trailing whitespace)
            out = result.stdout.strip()
            
            # Try to pretty-print JSON if applicable
            # pretty_printed: Flag indicating if JSON was detected and formatted
            # If True, JSON was found and pretty-printed; if False, output is printed as-is
            pretty_printed = False
            if out:
                debug_print(f"Checking if STDOUT is JSON (first 50 chars: {out[:50]})")
                # Fast-path: Check if output looks like JSON
                # trimmed: Output with leading whitespace removed (for checking start)
                # Check if output starts with { or [ and ends with } or ]
                trimmed = out.lstrip()
                if (trimmed.startswith('{') and out.rstrip().endswith('}')) or (trimmed.startswith('[') and out.rstrip().endswith(']')):
                    debug_print("STDOUT looks like JSON, attempting to parse")
                    try:
                        # data: Parsed JSON object (dict or list)
                        data = json.loads(out)
                        debug_print(f"JSON parsed successfully: type={type(data).__name__}")
                        # formatted: Pretty-printed JSON string with 2-space indentation
                        # ensure_ascii=False: Allow Unicode characters in output
                        formatted = json.dumps(data, indent=2, ensure_ascii=False)
                        print(formatted)
                        pretty_printed = True
                        debug_print("Pretty-printed JSON response")
                    except json.JSONDecodeError as e:
                        # If JSON parsing fails, output didn't contain valid JSON
                        debug_print(f"STDOUT looked like JSON but failed to parse: {e}")
                        debug_print("Printing raw output instead")
            if not pretty_printed:
                # If JSON not detected or parsing failed, print output as-is
                debug_print("Printing STDOUT as raw text (not JSON)")
                print(result.stdout)
        else:
            debug_print("No STDOUT received from command")

        # Print stderr (error output from curl command)
        # stderr typically contains warnings, errors, or verbose output
        if result.stderr:
            debug_print(f"STDERR received: {len(result.stderr)} bytes")
            print(f"{Colors.RED}STDERR:{Colors.RESET}")
            print(result.stderr)
        else:
            debug_print("No STDERR received from command")

        # Check exit code
        # result.returncode: Exit code from curl command
        # 0 = success, non-zero = error
        debug_print(f"Process exited with code: {result.returncode}")
        if result.returncode != 0:
            debug_print(f"Command failed with non-zero exit code: {result.returncode}")
            print_error(f"cURL execution failed with exit code {result.returncode}")
        else:
            debug_print("Command executed successfully (exit code 0)")

    except Exception as e:
        debug_print(f"Unexpected exception in run_command: {type(e).__name__}: {e}")
        import traceback
        debug_print(f"Traceback: {traceback.format_exc()}")
        print_error(f"Failed to execute command: {e}")

