# Contributing to curlpad

## Development Setup

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup

```bash
# Clone the repository
git clone https://github.com/IntegerAlex/curl-pad.git
cd curl-pad

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

### Key Modules

- **`src/curlpad/constants.py`**: Application constants (version, colors)
- **`src/curlpad/utils.py`**: Utility functions (debug, cleanup, temp files)
- **`src/curlpad/output.py`**: Output formatting (print_error, print_warning, etc.)
- **`src/curlpad/dependencies.py`**: Dependency management
- **`src/curlpad/templates.py`**: Template file creation
- **`src/curlpad/editor.py`**: Editor configuration and launching
- **`src/curlpad/commands.py`**: Command extraction, validation, execution
- **`src/curlpad/cli.py`**: Command-line interface and main flow

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Document all functions with docstrings
- Explain variable purposes in comments

### Adding New Features

1. **Identify the appropriate module**
   - Constants → `constants.py`
   - Utilities → `utils.py`
   - Output → `output.py`
   - Editor-related → `editor.py`
   - Command-related → `commands.py`
   - CLI-related → `cli.py`

2. **Add documentation**
   - Module-level docstring explaining purpose
   - Function docstrings with Args, Returns, Flow
   - Variable comments explaining purpose

3. **Update tests** (if applicable)
   - Add tests for new functionality
   - Ensure existing tests still pass

4. **Update documentation**
   - Update ARCHITECTURE.md if structure changes
   - Update README.md if user-facing changes

### Variable Naming

- Use descriptive names
- Add comments explaining purpose
- Document in module docstring

Example:
```python
# temp_files: List of temporary file paths tracked for cleanup
#             Files are added when created, removed on exit
temp_files: List[str] = []
```

### Function Documentation

Each function should have:
- Purpose description
- Args documentation
- Returns documentation
- Flow documentation (if complex)

Example:
```python
def create_template_file() -> str:
    """
    Create temporary file with curl command template.
    
    Creates a temporary shell script file with commented curl examples.
    The file is created in the system temp directory with .sh extension.
    The file is automatically added to temp_files list for cleanup on exit.
    
    Returns:
        Path to the created template file
        
    Flow:
        1. Create temporary file with .sh suffix
        2. Add file path to temp_files list
        3. Write template content to file
        4. Return file path
    """
```

## Building

### Development Build

```bash
# Build binary
./scripts/build_curlpad.sh  # Linux/macOS
.\scripts\build_curlpad.ps1  # Windows

# Binary will be in dist/
```

### Release Build

```bash
# Create release
./scripts/release.sh  # Linux/macOS
.\scripts\release.ps1  # Windows
```

## Testing

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

## Code Review Checklist

- [ ] Code follows PEP 8
- [ ] Type hints are used
- [ ] Functions are documented
- [ ] Variables have explanatory comments
- [ ] Module docstring explains purpose
- [ ] No breaking changes (or documented)
- [ ] Tests pass (if applicable)
- [ ] Documentation updated

