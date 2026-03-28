"""
Command history support for curlpad.

This module handles saving and loading command history from
~/.curlpad/history. The history file stores the last 20 commands
(one per line) in chronological order (newest last).

Functions:
    get_history_dir() -> str
        Return the path to the curlpad data directory (~/.curlpad)

    get_history_path() -> str
        Return the path to the history file (~/.curlpad/history)

    load_history() -> List[str]
        Load command history from the history file

    save_history(commands: List[str]) -> None
        Append commands to the history file, keeping the last 20

Flow:
    1. After successful command execution, save_history() appends commands
    2. On next run, load_history() provides previous commands
    3. Editor config maps ↑ arrow to recall from history register
"""

import os
import stat
from typing import List

from curlpad.utils import debug_print

MAX_HISTORY = 20


def get_history_dir() -> str:
    """
    Return the path to the curlpad data directory.

    Returns:
        Absolute path to ~/.curlpad
    """
    return os.path.join(os.path.expanduser('~'), '.curlpad')


def get_history_path() -> str:
    """
    Return the path to the curlpad history file.

    Returns:
        Absolute path to ~/.curlpad/history
    """
    return os.path.join(get_history_dir(), 'history')


def _ensure_history_dir() -> None:
    """Create ~/.curlpad directory if it doesn't exist."""
    history_dir = get_history_dir()
    if not os.path.isdir(history_dir):
        debug_print(f"Creating history directory: {history_dir}")
        os.makedirs(history_dir, mode=0o700, exist_ok=True)


def load_history() -> List[str]:
    """
    Load command history from the history file.

    Returns:
        List of previous curl commands (newest last), up to MAX_HISTORY.
        Empty list if history file doesn't exist or can't be read.
    """
    history_path = get_history_path()
    if not os.path.isfile(history_path):
        debug_print("No history file found")
        return []

    debug_print(f"Loading history from: {history_path}")
    try:
        with open(history_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        debug_print(f"Loaded {len(lines)} history entries")
        return lines[-MAX_HISTORY:]
    except OSError as e:
        debug_print(f"Error reading history file: {e}")
        return []


def save_history(commands: List[str]) -> None:
    """
    Append commands to the history file, keeping the last MAX_HISTORY entries.

    Args:
        commands: List of curl commands to save
    """
    if not commands:
        return

    debug_print(f"Saving {len(commands)} command(s) to history")
    _ensure_history_dir()
    history_path = get_history_path()

    # Load existing history
    existing = load_history()
    combined = existing + commands
    # Keep only the last MAX_HISTORY entries
    trimmed = combined[-MAX_HISTORY:]

    try:
        # Use os.open with restrictive permissions from the start and avoid
        # following symlinks where the platform supports O_NOFOLLOW.
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(history_path, flags, 0o600)
        try:
            with os.fdopen(fd, 'w') as f:
                for cmd in trimmed:
                    f.write(cmd + '\n')
        except Exception:
            os.close(fd)
            raise
        # Secure the file (for existing files that may have broader perms)
        try:
            os.chmod(history_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        debug_print(f"History saved: {len(trimmed)} entries in {history_path}")
    except OSError as e:
        debug_print(f"Error saving history: {e}")
