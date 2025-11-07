"""
curlpad - A simple curl editor for the command line

This package provides a modular CLI tool for editing and executing curl commands
with Vim/Neovim autocomplete support.

Package Structure:
    - constants: Application constants (version, colors, etc.)
    - utils: Utility functions (debug, cleanup, temp file management)
    - output: Output formatting and user messages
    - dependencies: Dependency checking and installation
    - templates: Template file creation for curl commands
    - editor: Editor configuration and launching
    - commands: Command extraction, validation, and execution
    - cli: Command-line interface and argument parsing

Usage:
    from curlpad import main
    main()
"""

__version__ = "1.0.0"
__author__ = "Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>"
__license__ = "GPL-3.0-or-later"

# Import main entry point for easy access
from curlpad.cli import main

__all__ = ["main", "__version__", "__author__", "__license__"]

