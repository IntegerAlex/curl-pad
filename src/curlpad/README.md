# curlpad Package Documentation

This directory contains the modular curlpad package. Each module has a specific responsibility and is well-documented.

## Package Structure

```
src/curlpad/
├── __init__.py          # Package initialization and exports
├── __main__.py          # Entry point for `python -m curlpad`
├── constants.py         # Application constants (version, colors, metadata)
├── utils.py            # Utility functions (debug, cleanup, temp files)
├── output.py           # Output formatting (print_error, print_warning, etc.)
├── dependencies.py     # Dependency management (check, install)
├── templates.py        # Template file creation
├── editor.py           # Editor configuration and launching
├── commands.py         # Command extraction, validation, execution
└── cli.py              # Command-line interface and main orchestration
```

## Module Documentation

### `constants.py`
**Purpose:** Application-wide constants and configuration

**Variables:**
- `__version__: str` - Application version string (e.g., "1.0.0")
- `__author__: str` - Author name and email
- `__license__: str` - License identifier (GPL-3.0-or-later)
- `Colors: class` - ANSI color codes for terminal output
  - `RED: str` - Red text color (used for errors)
  - `GREEN: str` - Green text color (used for success messages)
  - `YELLOW: str` - Yellow text color (used for warnings)
  - `BLUE: str` - Blue text color (used for info messages)
  - `MAGENTA: str` - Magenta text color (used for debug messages)
  - `CYAN: str` - Cyan text color (used for status messages)
  - `RESET: str` - Reset to default terminal color
  - `BOLD: str` - Bold text formatting

**Usage:**
```python
from curlpad.constants import Colors, __version__
print(f"{Colors.GREEN}Success{Colors.RESET}")
```

### `utils.py`
**Purpose:** Utility functions and global state management

**Global Variables:**
- `temp_files: List[str]` - Tracks all temporary files created during execution
  - **Purpose:** Used for cleanup on exit or error
  - **Modified by:** `templates.py`, `editor.py`
  - **Cleaned by:** `cleanup_temp_files()` function
  - **Lifecycle:** Files added when created, removed on exit
  
- `DEBUG: bool` - Global debug flag that enables verbose logging
  - **Purpose:** Controls whether debug messages are printed
  - **Set by:** `cli.py` when `--debug` CLI flag is provided
  - **Used by:** All modules via `debug_print()` function
  - **Default:** False
  - **When True:** All `debug_print()` calls output messages with timestamps

**Functions:**
- `debug_print(message: str) -> None` - Print debug message with timestamp when DEBUG is enabled
- `cleanup_temp_files() -> None` - Remove all tracked temporary files
- `signal_handler(signum, frame) -> None` - Handle SIGINT/SIGTERM signals and cleanup

**Flow:**
1. Application starts → `temp_files` is empty, `DEBUG` is False
2. User runs with `--debug` flag → `DEBUG` is set to True in `cli.py`
3. Functions create temp files → added to `temp_files` list
4. On exit (normal or signal) → `cleanup_temp_files()` removes all temp files

### `output.py`
**Purpose:** User-facing output formatting

**Functions:**
- `print_error(message: str) -> None` - Print error (red) and exit with code 1
  - **Flow:** Print message → Clean up temp files → Exit program
- `print_warning(message: str) -> None` - Print warning (yellow), continues execution
- `print_success(message: str) -> None` - Print success (green)
- `print_info(message: str) -> None` - Print info (blue)

**Usage:**
```python
from curlpad.output import print_error, print_warning
print_error("Something went wrong")  # Exits program
print_warning("This is a warning")   # Continues execution
```

### `dependencies.py`
**Purpose:** Dependency checking and installation

**Functions:**
- `check_command(command: str) -> bool` - Check if command exists in PATH
  - **Args:** `command` - Command name to check (e.g., 'curl', 'vim', 'nvim')
  - **Returns:** True if command found, False otherwise
  - **Uses:** `shutil.which()` to search PATH
  
- `get_editor() -> str` - Detect available editor (prefers nvim over vim)
  - **Returns:** 'nvim' or 'vim'
  - **Raises:** SystemExit if neither editor is found
  - **Flow:** Check nvim → Check vim → Error if neither found
  
- `check_dependencies() -> None` - Verify curl is installed
  - **Raises:** SystemExit if curl not found
  
- `install_deps() -> None` - Install vim/jq using package managers
  - **Supports:** Linux (apt-get, dnf, yum), macOS (brew)
  - **Flow:** Detect platform → Detect package manager → Install packages

### `templates.py`
**Purpose:** Template file creation

**Functions:**
- `create_template_file() -> str` - Create shell script template with curl examples
  - **Returns:** Path to created template file
  - **Creates:** Temporary .sh file with commented curl examples
  - **Flow:** Create temp file → Write template content → Add to temp_files → Return path
  
- `create_curl_dict() -> str` - Create dictionary file for Vim autocomplete
  - **Returns:** Path to created dictionary file
  - **Creates:** Temporary .dict file with curl options (one per line)
  - **Content:** HTTP methods, curl flags, headers, common URLs
  - **Flow:** Create temp file → Write curl options → Add to temp_files → Return path

### `editor.py`
**Purpose:** Editor configuration and launching

**Functions:**
- `create_editor_config(target_file: str) -> str` - Create Vim/Neovim config file
  - **Args:** `target_file` - Path to template file being edited
  - **Returns:** Path to created config file
  - **Creates:** 
    - Neovim: Lua config file (.lua) with dictionary completion
    - Vim: Vimscript config file (.vimrc) with dictionary completion
  - **Flow:** Create dict file → Detect editor → Generate config → Create temp file → Return path
  
- `open_editor(tmpfile: str) -> None` - Launch editor with template and config
  - **Args:** `tmpfile` - Path to template file to edit
  - **Flow:** Get editor → Create config → Build command → Launch subprocess → Wait for exit → Clean up config

### `commands.py`
**Purpose:** Command extraction, validation, and execution

**Functions:**
- `extract_commands(tmpfile: str) -> List[str]` - Parse template and extract curl commands
  - **Args:** `tmpfile` - Path to template file
  - **Returns:** List of extracted curl commands
  - **Handles:** Multiline commands, continuation lines, comments, empty lines
  - **Flow:** Read file → Filter comments/empty lines → Identify curl commands → Collect continuations → Join lines → Return commands
  
- `format_json_with_jq(commands: List[str]) -> List[str]` - Format JSON in commands
  - **Args:** `commands` - List of curl command strings
  - **Returns:** Commands with JSON formatted (if jq available)
  - **Flow:** Check jq available → For each command → Find JSON in -d flag → Format with jq → Replace JSON
  
- `validate_command(command: str) -> bool` - Basic validation of curl command
  - **Args:** `command` - Curl command string to validate
  - **Returns:** True if command appears valid
  - **Checks:** Command starts with 'curl'
  
- `run_command(command: str) -> None` - Execute curl command and display results
  - **Args:** `command` - Curl command string to execute
  - **Platform Handling:**
    - Windows: Uses `shlex.split()` or `cmd.exe` fallback
    - Unix: Uses `bash -c` for execution
  - **Flow:** Parse command → Execute via subprocess → Capture output → Pretty-print JSON if detected → Display results

### `cli.py`
**Purpose:** Command-line interface and main orchestration

**Functions:**
- `confirm_execution(commands: List[str]) -> bool` - Prompt user for confirmation
  - **Args:** `commands` - List of curl commands to be executed
  - **Returns:** True if user confirms, False if cancelled
  - **Flow:** Try stdin → Try Windows MessageBox → Proceed without confirmation
  
- `show_help() -> None` - Display help message
- `show_version() -> None` - Display version information
- `main() -> None` - Main entry point for the application

**Main Flow:**
1. Parse command-line arguments (`--help`, `--version`, `--install`, `--debug`)
2. Set `DEBUG` flag if `--debug` provided
3. Handle `--help`, `--version`, `--install` flags (exit early)
4. Check curl is installed (`check_dependencies()`)
5. Create template file (`create_template_file()`)
6. Open editor with autocomplete (`open_editor()`)
7. Extract curl commands from edited file (`extract_commands()`)
8. Format JSON in commands (`format_json_with_jq()`)
9. Validate commands (`validate_command()`)
10. Display commands to user
11. Prompt for confirmation (`confirm_execution()`)
12. Execute commands one by one (`run_command()`)

## Data Flow Diagram

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

## Global State Management

### `temp_files: List[str]`
- **Purpose:** Track all temporary files for cleanup
- **Modified by:** `templates.py` (template file, dict file), `editor.py` (config file)
- **Cleaned by:** `utils.cleanup_temp_files()` on exit
- **Lifecycle:** 
  1. File created → Added to list
  2. File used during execution
  3. On exit → All files removed

### `DEBUG: bool`
- **Purpose:** Enable verbose logging throughout application
- **Set by:** `cli.py` when `--debug` flag provided
- **Used by:** All modules via `debug_print()` function
- **Lifecycle:**
  1. Default: False
  2. User runs with `--debug` → Set to True
  3. All `debug_print()` calls output messages with timestamps

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

## Entry Points

1. **`curlpad.py`** (project root)
   - Backward-compatible entry point
   - Adds `src/` to PYTHONPATH
   - Imports and calls `cli.main()`

2. **`src/curlpad/__main__.py`**
   - Allows `python -m curlpad`
   - Imports and calls `cli.main()`

3. **`src/curlpad/cli.py`**
   - Contains `main()` function
   - Orchestrates entire application flow

## Testing

To test the modular structure:

```bash
# Test version
python curlpad.py --version

# Test help
python curlpad.py --help

# Test as module
python -m curlpad --version

# Test with debug
python curlpad.py --debug
```

## Backward Compatibility

The `curlpad.py` file maintains backward compatibility:
- Same command-line interface
- Same behavior
- Same entry point for PyInstaller
- Imports from new modular structure
