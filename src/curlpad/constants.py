"""
Constants and configuration for curlpad.

This module contains all application-wide constants including:
    - Version information
    - ANSI color codes for terminal output
    - Application metadata
    - Default configuration values

Variables:
    __version__: Application version string (e.g., "1.0.0")
    __author__: Author name and email
    __license__: License identifier (GPL-3.0-or-later)
    Colors: Class containing ANSI escape codes for colored terminal output
        - RED: Red text color
        - GREEN: Green text color
        - YELLOW: Yellow text color
        - BLUE: Blue text color
        - MAGENTA: Magenta text color (used for debug messages)
        - CYAN: Cyan text color
        - RESET: Reset color to default
        - BOLD: Bold text formatting
"""

__version__ = "1.3.1"
__author__ = "Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>"
__license__ = "GPL-3.0-or-later"


class Colors:
    """
    ANSI color codes for terminal output.
    
    These constants are used throughout the application to provide
    colored output in the terminal. They use ANSI escape sequences
    that work on most modern terminals.
    
    Usage:
        print(f"{Colors.RED}Error message{Colors.RESET}")
        print(f"{Colors.GREEN}Success message{Colors.RESET}")
    """
    RED = '\033[91m'      # Red text - used for errors
    GREEN = '\033[92m'    # Green text - used for success messages
    YELLOW = '\033[93m'   # Yellow text - used for warnings
    BLUE = '\033[94m'     # Blue text - used for info messages
    MAGENTA = '\033[95m'  # Magenta text - used for debug messages
    CYAN = '\033[96m'     # Cyan text - used for status messages
    RESET = '\033[0m'     # Reset to default terminal color
    BOLD = '\033[1m'      # Bold text formatting

