"""
Utility functions for curlpad.

This module provides utility functions for:
    - Debug logging with timestamps
    - Temporary file management and cleanup
    - Signal handling for graceful shutdown
    - Global state management (DEBUG flag, temp_files list)

Global Variables:
    temp_files: List[str] - Tracks all temporary files created during execution
                          Used for cleanup on exit or error
    DEBUG: bool - Global debug flag that enables verbose logging
                 Set via --debug CLI flag

Functions:
    debug_print(message: str) -> None
        Print debug message with timestamp when DEBUG is enabled
        
    cleanup_temp_files() -> None
        Remove all tracked temporary files
        
    signal_handler(signum, frame) -> None
        Handle SIGINT/SIGTERM signals and cleanup before exit

Flow:
    1. Application starts, temp_files list is empty, DEBUG is False
    2. User runs with --debug flag -> DEBUG is set to True
    3. Functions create temp files -> added to temp_files list
    4. On exit (normal or signal) -> cleanup_temp_files() removes all temp files
"""

import atexit
import os
import signal
import sys
from datetime import datetime
from typing import List

from curlpad.constants import Colors

# Global state variables
# temp_files: Tracks all temporary files created during execution for cleanup
#             Each module that creates temp files should append to this list
temp_files: List[str] = []

# DEBUG: Global debug flag that enables verbose logging
#        Set to True via --debug CLI flag in cli.py
#        When True, debug_print() will output messages with timestamps
DEBUG = False


def debug_print(message: str) -> None:
    """
    Print debug message with timestamp when DEBUG is enabled.
    
    This function only outputs when the global DEBUG flag is True.
    Messages are prefixed with [DEBUG timestamp] and colored magenta
    for easy identification in terminal output.
    
    Args:
        message: Debug message to print
        
    Usage:
        debug_print("Creating template file at: /tmp/file.sh")
        # Output (if DEBUG=True): [DEBUG 2023-11-06 14:30:45] Creating template file at: /tmp/file.sh
    """
    if DEBUG:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"{Colors.MAGENTA}[DEBUG {ts}] {message}{Colors.RESET}")


def cleanup_temp_files() -> None:
    """
    Remove all tracked temporary files.
    
    This function iterates through the global temp_files list and
    attempts to delete each file. Errors during deletion are silently
    ignored to prevent cleanup failures from masking real errors.
    
    Called automatically on:
        - Normal program exit (via atexit.register)
        - SIGINT/SIGTERM signals (via signal_handler)
        - Error conditions (via print_error in output.py)
        
    Flow:
        1. Iterate through temp_files list
        2. Check if file exists
        3. Attempt to delete (os.unlink)
        4. Ignore errors (file may already be deleted)
    """
    debug_print(f"Cleanup starting for {len(temp_files)} temp file(s)")
    if not temp_files:
        debug_print("No temp files to clean up")
        return
    
    for i, temp_file in enumerate(temp_files, 1):
        try:
            if os.path.exists(temp_file):
                debug_print(f"Removing temp file {i}/{len(temp_files)}: {temp_file}")
                os.unlink(temp_file)
                debug_print(f"Successfully removed: {temp_file}")
            else:
                debug_print(f"Temp file {i}/{len(temp_files)} already deleted: {temp_file}")
        except OSError as e:
            debug_print(f"Error removing temp file {i}/{len(temp_files)}: {temp_file} - {e}")
            pass  # Ignore cleanup errors
    
    debug_print(f"Cleanup complete: {len(temp_files)} temp file(s) processed")


def signal_handler(signum, frame) -> None:
    """
    Handle signals (SIGINT/SIGTERM) and cleanup before exit.
    
    This function is registered as a signal handler for SIGINT (Ctrl+C)
    and SIGTERM (termination signal). It ensures temporary files are
    cleaned up before the program exits.
    
    Args:
        signum: Signal number (not used, but required by signal handler signature)
        frame: Current stack frame (not used, but required by signal handler signature)
        
    Flow:
        1. User presses Ctrl+C or process receives SIGTERM
        2. signal_handler() is called
        3. cleanup_temp_files() removes all temp files
        4. sys.exit(1) terminates the program
    """
    signal_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else f"signal {signum}"
    debug_print(f"Signal handler called: {signal_name} (signum={signum})")
    debug_print("Cleaning up temp files before exit...")
    cleanup_temp_files()
    debug_print("Exiting due to signal")
    sys.exit(1)


# Register cleanup function to run on normal exit
# This ensures temp files are removed even if program exits normally
atexit.register(cleanup_temp_files)
if DEBUG:
    debug_print("Registered atexit handler for temp file cleanup")

# Register signal handlers for graceful shutdown
# SIGINT: Interrupt signal (Ctrl+C)
# SIGTERM: Termination signal (kill command)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
if DEBUG:
    debug_print("Registered signal handlers: SIGINT, SIGTERM")

