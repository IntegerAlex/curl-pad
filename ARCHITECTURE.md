# curlpad Architecture

This document describes the modular architecture of curlpad.

## Directory Structure

```
curlpad/
├── src/
│   └── curlpad/          # Main package directory
│       ├── __init__.py   # Package initialization and exports
│       ├── __main__.py   # Entry point for `python -m curlpad`
│       ├── constants.py  # Constants (version, colors, metadata)
│       ├── utils.py      # Utility functions (debug, cleanup, temp files)
│       ├── output.py     # Output formatting (print_error, print_warning, etc.)
│       ├── dependencies.py # Dependency management (check, install)
│       ├── templates.py  # Template file creation
│       ├── editor.py     # Editor configuration and launching
│       ├── commands.py   # Command extraction, validation, execution
│       └── cli.py        # Command-line interface and main flow
├── curlpad.py            # Backward-compatible entry point
├── curlpad.spec          # PyInstaller spec file
├── pyproject.toml        # Python project configuration
├── requirements.txt      # Python dependencies
├── scripts/              # Build and release scripts
└── README.md             # User documentation
```

## Module Overview

### `constants.py`
**Purpose:** Application-wide constants and configuration

**Variables:**
- `__version__`: Application version string
- `__author__`: Author information
- `__license__`: License identifier
- `Colors`: ANSI color codes for terminal output

**Usage:** Imported by all modules that need constants or colors.

### `utils.py`
**Purpose:** Utility functions and global state management

**Global Variables:**
- `temp_files: List[str]`: Tracks temporary files for cleanup
- `DEBUG: bool`: Global debug flag (set via --debug CLI flag)

**Functions:**
- `debug_print(message: str)`: Print debug messages with timestamps
- `cleanup_temp_files()`: Remove all tracked temporary files
- `signal_handler(signum, frame)`: Handle SIGINT/SIGTERM signals

**Flow:**
1. Application starts → `temp_files` is empty, `DEBUG` is False
2. User runs with `--debug` → `DEBUG` is set to True
3. Modules create temp files → added to `temp_files` list
4. On exit → `cleanup_temp_files()` removes all temp files

### `output.py`
**Purpose:** User-facing output formatting

**Functions:**
- `print_error(message: str)`: Print error (red) and exit
- `print_warning(message: str)`: Print warning (yellow)
- `print_success(message: str)`: Print success (green)
- `print_info(message: str)`: Print info (blue)

**Flow:** All user messages go through these functions for consistent formatting.

### `dependencies.py`
**Purpose:** Dependency checking and installation

**Functions:**
- `check_command(command: str) -> bool`: Check if command exists in PATH
- `get_editor() -> str`: Detect available editor (nvim/vim)
- `check_dependencies() -> None`: Verify curl is installed
- `install_deps() -> None`: Install vim/jq using package managers

**Flow:**
1. `check_dependencies()` verifies curl is installed
2. `get_editor()` detects nvim or vim
3. `install_deps()` can install vim/jq if `--install` flag is used

### `templates.py`
**Purpose:** Template file creation

**Functions:**
- `create_template_file() -> str`: Create shell script template with curl examples
- `create_curl_dict() -> str`: Create dictionary file for Vim autocomplete

**Flow:**
1. `create_template_file()` creates `.sh` file with commented curl examples
2. `create_curl_dict()` creates `.dict` file with curl options
3. Both files added to `temp_files` for cleanup
4. File paths returned for use by editor module

### `editor.py`
**Purpose:** Editor configuration and launching

**Functions:**
- `create_editor_config(target_file: str) -> str`: Create Vim/Neovim config
- `open_editor(tmpfile: str) -> None`: Launch editor with template

**Flow:**
1. `get_editor()` detects editor (nvim preferred)
2. `create_editor_config()` creates editor-specific config file
3. `open_editor()` launches editor with config and template
4. User edits commands
5. Editor closes, control returns to main flow

### `commands.py`
**Purpose:** Command extraction, validation, and execution

**Functions:**
- `extract_commands(tmpfile: str) -> List[str]`: Parse template and extract curl commands
- `format_json_with_jq(commands: List[str]) -> List[str]`: Format JSON in commands
- `validate_command(command: str) -> bool`: Validate curl command syntax
- `run_command(command: str) -> None`: Execute curl command and display results

**Flow:**
1. `extract_commands()` reads template and extracts curl commands
2. `format_json_with_jq()` formats JSON (if jq available)
3. `validate_command()` checks each command is valid
4. `run_command()` executes each command and displays results

### `cli.py`
**Purpose:** Command-line interface and main orchestration

**Functions:**
- `confirm_execution(commands: List[str]) -> bool`: Prompt for confirmation
- `show_help() -> None`: Display help message
- `show_version() -> None`: Display version
- `main() -> None`: Main entry point

**Flow:**
1. Parse command-line arguments
2. Handle `--help`, `--version`, `--install` flags
3. Check dependencies (curl)
4. Create template file
5. Open editor with autocomplete
6. Extract commands from edited file
7. Format JSON (if jq available)
8. Validate commands
9. Prompt for confirmation
10. Execute commands

## Data Flow

```
User runs: curlpad
    ↓
cli.main()
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
format_json_with_jq() → format JSON (optional)
    ↓
validate_command() → check each command
    ↓
confirm_execution() → prompt user for confirmation
    ↓
run_command() → execute each curl command
    ↓
Display results
```

## Global State

### `temp_files: List[str]`
- **Purpose:** Track all temporary files for cleanup
- **Modified by:** `templates.py`, `editor.py`
- **Cleaned by:** `utils.cleanup_temp_files()`
- **Lifecycle:** Files added when created, removed on exit

### `DEBUG: bool`
- **Purpose:** Enable verbose logging
- **Set by:** `cli.py` when `--debug` flag is provided
- **Used by:** All modules via `debug_print()`
- **Lifecycle:** False by default, True when `--debug` flag used

## Module Dependencies

```
cli.py
├── constants.py (version)
├── utils.py (DEBUG, debug_print)
├── output.py (print_* functions)
├── dependencies.py (check_dependencies, install_deps)
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

1. **`curlpad.py`**: Backward-compatible entry point
   - Adds `src/` to PYTHONPATH
   - Imports and calls `cli.main()`

2. **`src/curlpad/__main__.py`**: Module entry point
   - Allows `python -m curlpad`
   - Imports and calls `cli.main()`

3. **`src/curlpad/cli.py`**: Main entry point
   - Contains `main()` function
   - Orchestrates entire application flow

## Build Process

1. **PyInstaller** reads `curlpad.spec`
2. **Entry point** is `curlpad.py` (which imports from `src/curlpad`)
3. **PyInstaller** auto-detects all imports from `src/curlpad` package
4. **Binary** is created with all dependencies bundled

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

