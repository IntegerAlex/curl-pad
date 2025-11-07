# curlpad Module Documentation

This document provides detailed documentation for each module in the curlpad package, including variable explanations, function flows, and usage examples.

## Table of Contents

1. [constants.py](#constantspy)
2. [utils.py](#utilspy)
3. [output.py](#outputpy)
4. [dependencies.py](#dependenciespy)
5. [templates.py](#templatespy)
6. [editor.py](#editorpy)
7. [commands.py](#commandspy)
8. [cli.py](#clipy)

---

## constants.py

**Purpose:** Application-wide constants and configuration

### Variables

- **`__version__: str`**
  - **Purpose:** Application version string
  - **Value:** "1.0.0"
  - **Usage:** Displayed in `--version` output and used for release tagging
  - **Modified:** Only when releasing new version

- **`__author__: str`**
  - **Purpose:** Author name and email
  - **Value:** "Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>"
  - **Usage:** Displayed in help and installer output

- **`__license__: str`**
  - **Purpose:** License identifier
  - **Value:** "GPL-3.0-or-later"
  - **Usage:** License information for legal compliance

- **`Colors: class`**
  - **Purpose:** ANSI color codes for terminal output
  - **Attributes:**
    - `RED: str` - Red text (`\033[91m`) - Used for errors
    - `GREEN: str` - Green text (`\033[92m`) - Used for success messages
    - `YELLOW: str` - Yellow text (`\033[93m`) - Used for warnings
    - `BLUE: str` - Blue text (`\033[94m`) - Used for info messages
    - `MAGENTA: str` - Magenta text (`\033[95m`) - Used for debug messages
    - `CYAN: str` - Cyan text (`\033[96m`) - Used for status messages
    - `RESET: str` - Reset color (`\033[0m`) - Reset to default terminal color
    - `BOLD: str` - Bold text (`\033[1m`) - Bold text formatting

### Usage Example

```python
from curlpad.constants import Colors, __version__
print(f"{Colors.GREEN}Success{Colors.RESET}")
print(f"Version: {__version__}")
```

---

## utils.py

**Purpose:** Utility functions and global state management

### Global Variables

- **`temp_files: List[str]`**
  - **Purpose:** Tracks all temporary files created during execution
  - **Type:** List of file paths (strings)
  - **Lifecycle:**
    1. Starts as empty list when application starts
    2. Files added when created (by `templates.py`, `editor.py`)
    3. All files removed on exit via `cleanup_temp_files()`
  - **Modified by:**
    - `templates.py`: Adds template file and dictionary file
    - `editor.py`: Adds editor config file
  - **Cleaned by:** `cleanup_temp_files()` function
  - **Why needed:** Ensures no temporary files are left behind after execution

- **`DEBUG: bool`**
  - **Purpose:** Global debug flag that enables verbose logging
  - **Type:** Boolean
  - **Default:** False
  - **Set by:** `cli.py` when `--debug` CLI flag is provided
  - **Used by:** All modules via `debug_print()` function
  - **When True:** All `debug_print()` calls output messages with timestamps
  - **When False:** Debug messages are suppressed

### Functions

- **`debug_print(message: str) -> None`**
  - **Purpose:** Print debug message with timestamp when DEBUG is enabled
  - **Args:** `message` - Debug message to print
  - **Flow:**
    1. Check if `DEBUG` is True
    2. If True, format message with timestamp and magenta color
    3. Print message to stdout
  - **Usage:** `debug_print("Creating template file at: /tmp/file.sh")`

- **`cleanup_temp_files() -> None`**
  - **Purpose:** Remove all tracked temporary files
  - **Flow:**
    1. Iterate through `temp_files` list
    2. Check if file exists
    3. Attempt to delete (os.unlink)
    4. Ignore errors (file may already be deleted)
  - **Called automatically on:**
    - Normal program exit (via `atexit.register`)
    - SIGINT/SIGTERM signals (via `signal_handler`)
    - Error conditions (via `print_error` in `output.py`)

- **`signal_handler(signum, frame) -> None`**
  - **Purpose:** Handle signals (SIGINT/SIGTERM) and cleanup before exit
  - **Args:**
    - `signum`: Signal number (not used, but required by signal handler signature)
    - `frame`: Current stack frame (not used, but required by signal handler signature)
  - **Flow:**
    1. User presses Ctrl+C or process receives SIGTERM
    2. `signal_handler()` is called
    3. `cleanup_temp_files()` removes all temp files
    4. `sys.exit(1)` terminates the program

---

## output.py

**Purpose:** User-facing output formatting

### Functions

- **`print_error(message: str) -> None`**
  - **Purpose:** Print error message in red and exit the program
  - **Args:** `message` - Error message to display
  - **Flow:**
    1. Print red error message with ❌ emoji to stderr
    2. Clean up all temporary files
    3. Exit program with code 1
  - **Usage:** `print_error("curl is not installed")`

- **`print_warning(message: str) -> None`**
  - **Purpose:** Print warning message in yellow (non-fatal)
  - **Args:** `message` - Warning message to display
  - **Flow:** Print yellow warning message with ⚠ emoji to stderr, continue execution
  - **Usage:** `print_warning("No uncommented command found")`

- **`print_success(message: str) -> None`**
  - **Purpose:** Print success message in green
  - **Args:** `message` - Success message to display
  - **Flow:** Print green success message with ✅ emoji to stdout
  - **Usage:** `print_success("Dependencies installed")`

- **`print_info(message: str) -> None`**
  - **Purpose:** Print informational message in blue
  - **Args:** `message` - Info message to display
  - **Flow:** Print blue info message with ℹ emoji to stdout
  - **Usage:** `print_info("Installing missing dependencies...")`

---

## dependencies.py

**Purpose:** Dependency checking and installation

### Functions

- **`check_command(command: str) -> bool`**
  - **Purpose:** Check if a command exists in the system PATH
  - **Args:** `command` - Command name to check (e.g., 'curl', 'vim', 'nvim')
  - **Returns:** True if command found, False otherwise
  - **Variables:**
    - `path: str | None` - Full path to command executable, or None if not found
  - **Flow:**
    1. Call `shutil.which(command)` to search PATH
    2. Log result if DEBUG mode enabled
    3. Return True if path is not None, False otherwise

- **`get_editor() -> str`**
  - **Purpose:** Detect and return available editor (prefers nvim over vim)
  - **Returns:** 'nvim' or 'vim'
  - **Raises:** SystemExit if neither editor is found
  - **Flow:**
    1. Check for 'nvim' in PATH
    2. If not found, check for 'vim' in PATH
    3. If neither found, print error and exit

- **`check_dependencies() -> None`**
  - **Purpose:** Verify that required dependencies are installed
  - **Raises:** SystemExit if curl is not found
  - **Flow:**
    1. Check if 'curl' command exists in PATH
    2. If not found, print error and exit

- **`install_deps() -> None`**
  - **Purpose:** Install missing dependencies (vim, jq) using platform-specific package managers
  - **Variables:**
    - `system: str` - Operating system name in lowercase ('linux', 'darwin', etc.)
  - **Flow:**
    1. Detect platform (linux/darwin)
    2. Detect package manager (apt-get/dnf/yum/brew)
    3. Run package manager commands to install vim and jq
    4. Print success message

---

## templates.py

**Purpose:** Template file creation

### Functions

- **`create_template_file() -> str`**
  - **Purpose:** Create temporary shell script template with curl examples
  - **Returns:** Path to created template file
  - **Variables:**
    - `template: str` - Template content (shebang, comments, example curl command)
    - `fd: int` - File descriptor (integer) for the opened file
    - `tmpfile: str` - Path to the created temporary template file (.sh extension)
  - **Flow:**
    1. Create temporary file with .sh suffix
    2. Add file path to `temp_files` list
    3. Write template content to file
    4. Return file path

- **`create_curl_dict() -> str`**
  - **Purpose:** Create dictionary file for Vim/Neovim autocomplete
  - **Returns:** Path to created dictionary file
  - **Variables:**
    - `curl_options: List[str]` - List of curl-related keywords for autocomplete
      - Includes: HTTP methods, curl flags, headers, common URLs
    - `fd: int` - File descriptor (integer) for the opened file
    - `dict_tmp: str` - Path to the created temporary dictionary file (.dict extension)
    - `lines: List[str]` - List of all lines in the dictionary file (for verification)
  - **Flow:**
    1. Create temporary file with .dict suffix
    2. Add file path to `temp_files` list
    3. Write each curl option to file (one per line)
    4. Verify file content if DEBUG mode enabled
    5. Return file path

---

## editor.py

**Purpose:** Editor configuration and launching

### Functions

- **`create_editor_config(target_file: str) -> str`**
  - **Purpose:** Create temporary vimrc/lua file with curl completion settings
  - **Args:** `target_file` - Path to template file being edited
  - **Returns:** Path to created configuration file
  - **Variables:**
    - `dict_file: str` - Path to dictionary file containing curl options
    - `editor: str` - Editor name ('nvim' or 'vim')
    - `config_content: str` - Editor-specific configuration content (Lua or Vimscript)
    - `suffix: str` - File extension ('.lua' for Neovim, '.vimrc' for Vim)
    - `fd: int` - File descriptor (integer) for the opened file
    - `config_tmp: str` - Path to the created temporary config file
    - `lines: List[str]` - List of lines from config content (for debug output)
  - **Flow:**
    1. Create curl dictionary file for autocomplete
    2. Detect editor type (nvim or vim)
    3. Generate editor-specific config content
    4. Create temporary config file (.lua or .vimrc)
    5. Add file to `temp_files` list
    6. Return config file path

- **`open_editor(tmpfile: str) -> None`**
  - **Purpose:** Launch editor with template file and autocomplete configuration
  - **Args:** `tmpfile` - Path to template file to edit
  - **Variables:**
    - `editor: str` - Editor name ('nvim' or 'vim')
    - `config_tmp: str` - Path to editor configuration file
    - `cmd: List[str]` - List of command arguments to launch editor
    - `result: CompletedProcess` - Result from subprocess.run()
  - **Flow:**
    1. Get available editor (nvim or vim)
    2. Create editor configuration file
    3. Build editor command with config and template file
    4. Launch editor as subprocess
    5. Wait for editor to close (blocks until user saves and quits)
    6. Clean up config file

---

## commands.py

**Purpose:** Command extraction, validation, and execution

### Functions

- **`extract_commands(tmpfile: str) -> List[str]`**
  - **Purpose:** Parse template file and extract curl commands
  - **Args:** `tmpfile` - Path to template file
  - **Returns:** List of extracted curl commands
  - **Variables:**
    - `raw_lines: List[str]` - List of all lines from template file (preserving original format)
    - `filtered: List[str]` - List of non-comment, non-empty lines with original indentation
    - `coalesced: List[str]` - Final list of complete curl commands (one command per string)
    - `current: List[str]` - List of lines that form the current command being built
    - `line: str` - Line with trailing whitespace removed
    - `lstrip: str` - Line with leading whitespace removed
    - `is_continuation: bool` - True if line continues previous command
  - **Flow:**
    1. Read all lines from template file
    2. Filter out comments and empty lines
    3. Identify command starts (lines starting with 'curl')
    4. Collect continuation lines
    5. Join lines into complete commands
    6. Return list of commands

- **`format_json_with_jq(commands: List[str]) -> List[str]`**
  - **Purpose:** Format JSON in curl commands using jq if available
  - **Args:** `commands` - List of curl command strings
  - **Returns:** List of commands with JSON formatted (if jq available)
  - **Variables:**
    - `formatted_commands: List[str]` - List of commands with JSON formatted
    - `original_line: str` - Original command string before formatting
    - `pattern: str` - Regular expression to match JSON in curl -d flag
    - `match: Match | None` - Regex match object if JSON found
    - `before: str` - Part of command before JSON
    - `json_str: str` - JSON string extracted from command
    - `after: str` - Part of command after JSON
    - `result: CompletedProcess` - Result from jq subprocess
    - `formatted_json: str` - JSON string formatted by jq
  - **Flow:**
    1. Check if jq is available
    2. For each command, search for JSON in -d flag
    3. Extract JSON string and format with jq
    4. Replace original JSON with formatted version
    5. Return formatted commands

- **`validate_command(command: str) -> bool`**
  - **Purpose:** Basic validation of curl command syntax
  - **Args:** `command` - Curl command string to validate
  - **Returns:** True if command appears valid
  - **Validation Rules:**
    1. Command must start with 'curl' (after stripping whitespace)
    2. Basic structure check (curl followed by options/URL)

- **`run_command(command: str) -> None`**
  - **Purpose:** Execute curl command and display results
  - **Args:** `command` - Curl command string to execute
  - **Variables:**
    - `args: List[str] | None` - List of command arguments parsed from command string
    - `creationflags: int` - Windows-specific subprocess flags
    - `curl_exe: str | None` - Path to curl executable
    - `result: CompletedProcess` - Result from subprocess.run()
    - `out: str` - Stripped stdout (removes leading/trailing whitespace)
    - `trimmed: str` - Output with leading whitespace removed
    - `pretty_printed: bool` - Flag indicating if JSON was detected and formatted
    - `data: dict | list` - Parsed JSON object
    - `formatted: str` - Pretty-printed JSON string
  - **Flow:**
    1. Parse command into arguments (platform-specific)
    2. Execute via subprocess
    3. Capture stdout and stderr
    4. Attempt to pretty-print JSON in stdout
    5. Display output with appropriate colors
    6. Check exit code and display error if non-zero

---

## cli.py

**Purpose:** Command-line interface and main orchestration

### Functions

- **`confirm_execution(commands: List[str]) -> bool`**
  - **Purpose:** Prompt user for confirmation before executing commands
  - **Args:** `commands` - List of curl commands to be executed
  - **Returns:** True if user confirms, False if cancelled
  - **Flow:**
    1. Try to use stdin for interactive prompt
    2. If stdin fails, try Windows MessageBox (if on Windows)
    3. If all fail, proceed without confirmation (with warning)

- **`show_help() -> None`**
  - **Purpose:** Display help message
  - **Flow:** Print formatted help text with usage, options, examples, and dependencies

- **`show_version() -> None`**
  - **Purpose:** Display version information
  - **Flow:** Print version string from `constants.py`

- **`main() -> None`**
  - **Purpose:** Main entry point for the application
  - **Variables:**
    - `parser: ArgumentParser` - Argument parser instance
    - `args: Namespace` - Parsed arguments (contains help, version, install, debug flags)
    - `unknown: List[str]` - Unrecognized arguments (not used)
    - `tmpfile: str` - Path to created template file
    - `commands: List[str]` - List of extracted curl commands
    - `cmd: str` - Individual command from commands list
  - **Flow:**
    1. Parse command-line arguments
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

---

## Complete Application Flow

```
User runs: curlpad
    ↓
cli.main()
    ↓
Parse arguments → Set DEBUG flag
    ↓
Handle --help/--version/--install (exit if set)
    ↓
check_dependencies() → verify curl installed
    ↓
create_template_file() → create .sh file with examples
    ↓
open_editor() → launch nvim/vim with autocomplete
    ↓
User edits commands in editor
    ↓
extract_commands() → parse file and extract curl commands
    ↓
format_json_with_jq() → format JSON (optional, if jq available)
    ↓
validate_command() → check each command is valid
    ↓
confirm_execution() → prompt user for confirmation
    ↓
run_command() → execute each curl command
    ↓
Display results → cleanup_temp_files() on exit
```

---

## Global State Management

### `temp_files: List[str]`
- **Purpose:** Track all temporary files for cleanup
- **Modified by:** `templates.py`, `editor.py`
- **Cleaned by:** `utils.cleanup_temp_files()`
- **Lifecycle:** Files added when created, removed on exit

### `DEBUG: bool`
- **Purpose:** Enable verbose logging
- **Set by:** `cli.py` when `--debug` flag provided
- **Used by:** All modules via `debug_print()`
- **Lifecycle:** False by default, True when `--debug` flag used

---

## Module Dependencies

```
cli.py
├── constants.py (__version__)
├── utils.py (DEBUG, debug_print)
├── output.py (print_error, print_warning, print_info)
├── dependencies.py (check_dependencies, install_deps, get_editor)
├── templates.py (create_template_file)
├── editor.py (open_editor)
└── commands.py (extract_commands, format_json_with_jq, validate_command, run_command)

editor.py
├── dependencies.py (get_editor)
├── templates.py (create_curl_dict)
├── utils.py (temp_files, debug_print, DEBUG)
└── output.py (print_error)

commands.py
├── constants.py (Colors)
├── dependencies.py (check_command)
├── utils.py (debug_print)
└── output.py (print_error, print_warning)

templates.py
├── utils.py (temp_files, debug_print, DEBUG)
└── output.py (print_error)

dependencies.py
├── utils.py (debug_print)
└── output.py (print_error, print_info, print_success)

output.py
├── constants.py (Colors)
└── utils.py (cleanup_temp_files)

utils.py
└── constants.py (Colors)
```

