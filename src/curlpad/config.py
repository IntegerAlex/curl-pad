"""
Configuration file support for curlpad.

This module handles loading user configuration from ~/.curlpadrc.
The config file uses a simple KEY=value format (one setting per line).
Lines starting with '#' are treated as comments.

Supported settings:
    DEFAULT_URL: Base URL to pre-populate in the curl template
    AUTO_FORMAT_JSON: Whether to auto-format JSON output (true/false)

Functions:
    get_config_path() -> str
        Return the path to the config file (~/.curlpadrc)

    load_config() -> dict
        Load and parse the config file, returning a dict of settings

Flow:
    1. get_config_path() returns ~/.curlpadrc path
    2. load_config() reads and parses the file
    3. Settings are returned as a dict with string values
    4. Caller applies settings as needed
"""

import os

from curlpad.utils import debug_print


def get_config_path() -> str:
    """
    Return the path to the curlpad config file.

    Returns:
        Absolute path to ~/.curlpadrc
    """
    return os.path.join(os.path.expanduser('~'), '.curlpadrc')


def load_config() -> dict:
    """
    Load and parse the curlpad config file.

    Reads ~/.curlpadrc and returns a dict of settings. The file uses
    a simple KEY=value format. Lines starting with '#' are comments.
    Missing or unreadable files are silently ignored.

    Returns:
        Dict of config settings (keys are uppercase strings).
        Empty dict if config file doesn't exist or can't be read.

    Example config file::

        # ~/.curlpadrc
        DEFAULT_URL=https://api.example.com
        AUTO_FORMAT_JSON=true
    """
    config_path = get_config_path()
    config = {}

    if not os.path.isfile(config_path):
        debug_print(f"Config file not found: {config_path}")
        return config

    debug_print(f"Loading config from: {config_path}")
    try:
        with open(config_path, 'r') as f:
            for lineno, raw_line in enumerate(f, 1):
                line = raw_line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    debug_print(f"Config line {lineno}: skipping (no '='): {line}")
                    continue
                key, _, value = line.partition('=')
                key = key.strip().upper()
                value = value.strip()
                config[key] = value
                debug_print(f"Config: {key}={value}")
    except OSError as e:
        debug_print(f"Error reading config file: {e}")

    debug_print(f"Loaded {len(config)} config setting(s)")
    return config
