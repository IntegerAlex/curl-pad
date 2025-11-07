"""
Output formatting and user messages for curlpad.

This module provides functions for displaying formatted messages to the user
with appropriate colors and formatting. All output functions use the Colors
class from constants.py for consistent styling.

Functions:
    print_error(message: str) -> None
        Print error message in red and exit with code 1
        
    print_warning(message: str) -> None
        Print warning message in yellow (non-fatal)
        
    print_success(message: str) -> None
        Print success message in green
        
    print_info(message: str) -> None
        Print informational message in blue

Flow:
    - Error messages: Red text with ❌ emoji, exits program
    - Warning messages: Yellow text with ⚠ emoji, continues execution
    - Success messages: Green text with ✅ emoji
    - Info messages: Blue text with ℹ emoji
"""

import sys

from curlpad.constants import Colors
from curlpad.utils import cleanup_temp_files


def print_error(message: str) -> None:
    """
    Print error message in red and exit the program.
    
    This function is used for fatal errors that prevent the program
    from continuing. It prints the message in red with an error emoji,
    cleans up temporary files, and exits with code 1.
    
    Args:
        message: Error message to display
        
    Flow:
        1. Print red error message with ❌ emoji to stderr
        2. Clean up all temporary files
        3. Exit program with code 1
        
    Usage:
        print_error("curl is not installed. Please install curl first.")
    """
    print(f"{Colors.RED}❌ {message}{Colors.RESET}", file=sys.stderr)
    cleanup_temp_files()
    sys.exit(1)


def print_warning(message: str) -> None:
    """
    Print warning message in yellow (non-fatal).
    
    This function is used for warnings that don't prevent execution
    but inform the user of potential issues. The program continues
    after displaying the warning.
    
    Args:
        message: Warning message to display
        
    Usage:
        print_warning("No uncommented command found. Exiting.")
    """
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}", file=sys.stderr)


def print_success(message: str) -> None:
    """
    Print success message in green.
    
    This function is used to indicate successful operations.
    
    Args:
        message: Success message to display
        
    Usage:
        print_success("Dependencies installed.")
    """
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """
    Print informational message in blue.
    
    This function is used for general informational messages
    that provide context to the user.
    
    Args:
        message: Info message to display
        
    Usage:
        print_info("Installing missing dependencies...")
    """
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

