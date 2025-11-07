"""
Template file creation for curlpad.

This module handles creation of template files and dictionaries:
    - create_template_file(): Creates a temporary shell script template with curl examples
    - create_curl_dict(): Creates a dictionary file for Vim/Neovim autocomplete

Functions:
    create_template_file() -> str
        Create temporary file with curl command template
        
    create_curl_dict() -> str
        Create temporary dictionary file for Vim completion with curl options

Flow:
    1. create_template_file() creates a .sh file with commented curl examples
    2. create_curl_dict() creates a .dict file with curl options for autocomplete
    3. Both files are added to temp_files list for cleanup
    4. File paths are returned for use by editor module
"""

import os
import tempfile

from curlpad.utils import temp_files, debug_print, DEBUG
from curlpad.output import print_error


def create_template_file() -> str:
    """
    Create temporary file with curl command template in secure temp directory.

    Creates a temporary shell script file with commented curl examples.
    The file is created in a private temp directory with proper permissions.
    The file is automatically added to temp_files list for cleanup on exit.

    Returns:
        Path to the created template file

    Raises:
        SystemExit: If file creation fails

    Template Content:
        - Shebang line (#!/bin/bash)
        - Header comments with author and license info
        - Commented curl example command
        - Empty line at end (where cursor will be positioned)

    Flow:
        1. Create temporary directory with secure permissions
        2. Create temporary file in the secure directory
        3. Add file path to temp_files list
        4. Write template content to file
        5. Return file path
    """
    template = """#!/bin/bash
# curlpad - scratchpad for curl.
# AUTHOR - Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# curl -X POST "https://api.example.com" \\
#   -H "Content-Type: application/json" \\
#   -d '{"key":"value"}'

"""

    # Create temporary directory with secure permissions
    with tempfile.TemporaryDirectory() as tdir:
        # mode 0o700 by default on most systems; enforce if needed:
        os.chmod(tdir, 0o700)

        # Create temporary file in secure directory
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False, dir=tdir) as f:
            tmpfile = f.name

            # Add template file to temp_files list for automatic cleanup on exit
            # This ensures the file is deleted even if program crashes
            temp_files.append(tmpfile)
            debug_print(f"Created template file at: {tmpfile}")

            try:
                # Write template content to file
                f.write(template)
            except OSError as e:
                # If file write fails, print error and exit
                print_error(f"Failed to create template file: {e}")

            return tmpfile


def create_curl_dict() -> str:
    """
    Create temporary dictionary file for Vim/Neovim autocomplete in secure temp directory.

    Creates a dictionary file containing curl options, HTTP methods,
    common headers, and URLs. This dictionary is used by Vim/Neovim
    for autocomplete when editing curl commands.

    Returns:
        Path to the created dictionary file

    Raises:
        SystemExit: If file creation fails

    Dictionary Content:
        - HTTP methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
        - curl options: -X, -H, -d, --header, --data, etc.
        - Common headers: Content-Type:, application/json, etc.
        - Common URLs: https://, http://, localhost, 127.0.0.1

    Flow:
        1. Create temporary file in secure directory
        2. Add file path to temp_files list
        3. Write curl options (one per line) to file
        4. Verify file content if DEBUG mode is enabled
        5. Return file path
    """
    # curl_options: List of curl-related keywords for autocomplete
    # This list contains all the words that will be available for autocomplete in the editor
    # Includes:
    #   - HTTP methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
    #   - curl flags: -X, -H, -d, --header, --data, etc.
    #   - Common headers: Content-Type:, application/json, etc.
    #   - Common URLs: https://, http://, localhost, 127.0.0.1
    # Each option is written as a separate line in the dictionary file
    curl_options = [
        '-X', 'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS',
        '-H', '--header', 'Content-Type:', 'application/json', 'application/xml', 'text/plain',
        '-d', '--data', '--data-raw', '--data-binary', '--data-urlencode',
        '--url', '-i', '--include', '-v', '--verbose', '-s', '--silent',
        '-o', '--output', '-L', '--location', '-k', '--insecure',
        '--connect-timeout', '--max-time', '-u', '--user', '-x', '--proxy',
        '--cert', '--key', '--cacert', '-A', '--user-agent',
        '-b', '--cookie', '-c', '--cookie-jar', '-e', '--referer',
        '-f', '--fail', '-I', '--head', '-m', '--max-redirs',
        '--compressed', '--digest', '--negotiate', '--ntlm',
        'curl', 'https://', 'http://', 'localhost', '127.0.0.1'
    ]

    # Create temporary directory with secure permissions
    with tempfile.TemporaryDirectory() as tdir:
        # mode 0o700 by default on most systems; enforce if needed:
        os.chmod(tdir, 0o700)

        # Create temporary dictionary file in secure directory
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dict", delete=False, dir=tdir) as f:
            dict_tmp = f.name

            # Add dictionary file to temp_files list for automatic cleanup on exit
            temp_files.append(dict_tmp)
            debug_print(f"Created curl dictionary at: {dict_tmp} with {len(curl_options)} entries")

            try:
                # Write each curl option to the dictionary file (one per line)
                # Vim/Neovim dictionary format: one word per line
                for option in curl_options:
                    f.write(f"{option}\n")

                # If DEBUG mode is enabled, verify dictionary file was created correctly
                if DEBUG:
                    # lines: List of all lines in the dictionary file
                    # Used to verify file was written correctly
                    with open(dict_tmp, 'r') as f:
                        lines = f.readlines()
                        # Output first 5 lines for verification
                        debug_print(f"Dictionary file verified: {len(lines)} lines, first 5: {[l.strip() for l in lines[:5]]}")
            except OSError as e:
                # If file write fails, print error and exit
                print_error(f"Failed to create dictionary file: {e}")

            return dict_tmp

