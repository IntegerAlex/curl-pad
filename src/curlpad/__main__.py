"""
Entry point for running curlpad as a module.

This allows running curlpad with: python -m curlpad

Usage:
    python -m curlpad [OPTIONS]
    python -m curlpad --help
    python -m curlpad --version
"""

from curlpad.cli import main

if __name__ == '__main__':
    main()

