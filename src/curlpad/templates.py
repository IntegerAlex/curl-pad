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
import stat
import tempfile

from curlpad.utils import temp_files, debug_print, DEBUG
from curlpad.output import print_error


def create_template_file() -> str:
    """
    Create temporary file with curl command template in secure temp directory.

    Creates a temporary shell script file with commented curl examples.
    The file is created atomically with proper permissions to prevent TOCTOU attacks.
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
        1. Set secure umask atomically
        2. Create temporary directory (automatically has 0o700 permissions)
        3. Create temporary file with 0o600 permissions
        4. Write template content atomically
        5. Verify permissions
        6. Add to temp_files list
        7. Return file path
    """
    # Platform-specific curl command (curl.exe on Windows, curl on Unix)
    curl_cmd = "curl.exe" if os.name == 'nt' else "curl"
    
    template = f"""#!/bin/bash
# curlpad - scratchpad for curl.
# AUTHOR - Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# curl -X POST "https://api.example.com" \\
#   -H "Content-Type: application/json" \\
#   -d '{{"key":"value"}}'
{curl_cmd} 
"""

    debug_print("Creating template file with secure permissions")
    debug_print(f"Template content length: {len(template)} bytes")
    
    # Set secure umask to ensure 0o700 directory and 0o600 file permissions
    old_umask = os.umask(0o077)
    debug_print(f"Set secure umask: 0o077 (old umask was: {oct(old_umask)})")
    
    try:
        # Create temporary directory with secure permissions (0o700 due to umask)
        debug_print("Creating temporary directory")
        tdir = tempfile.mkdtemp()
        debug_print(f"Created temp directory: {tdir}")
        
        # Verify directory permissions
        dir_stat = os.stat(tdir)
        dir_mode = stat.S_IMODE(dir_stat.st_mode)
        debug_print(f"Directory permissions: {oct(dir_mode)} (expected: 0o700)")
        if dir_mode != 0o700:
            # Force correct permissions if umask didn't work
            debug_print(f"Forcing secure permissions on temp directory: {tdir}")
            os.chmod(tdir, 0o700)
            debug_print(f"Forced secure permissions on temp directory: {tdir}")
        
        # Create temporary file with secure permissions atomically
        debug_print(f"Creating temporary file in directory: {tdir}")
        fd, tmpfile = tempfile.mkstemp(suffix=".sh", dir=tdir)
        debug_print(f"Created temp file: {tmpfile} (fd: {fd})")
        
        try:
            # Set file permissions to 0o600 (owner read/write only)
            debug_print(f"Setting file permissions to 0o600")
            os.fchmod(fd, 0o600)
            
            # Write template content atomically via file descriptor
            debug_print(f"Writing template content ({len(template)} bytes) to file")
            with os.fdopen(fd, 'w') as f:
                bytes_written = f.write(template)
                debug_print(f"Wrote {bytes_written} bytes to template file")
            
            # Verify file permissions after write
            file_stat = os.stat(tmpfile)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            debug_print(f"File permissions after write: {oct(file_mode)} (expected: 0o600)")
            if file_mode != 0o600:
                debug_print(f"WARNING: File permissions mismatch! Expected 0o600, got {oct(file_mode)}")
                print_error(f"Failed to set secure permissions on template file: {tmpfile}")
            
            # Add to cleanup list AFTER successful write
            temp_files.append(tmpfile)
            debug_print(f"Added template file to cleanup list (total temp files: {len(temp_files)})")
            debug_print(f"Created secure template file at: {tmpfile} (mode: 0o600)")
            
            return tmpfile
            
        except OSError as e:
            # Clean up file on error
            try:
                os.unlink(tmpfile)
            except OSError:
                pass
            print_error(f"Failed to create template file: {e}")
            
    finally:
        # Restore original umask
        os.umask(old_umask)


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
        1. Set secure umask
        2. Create temporary directory atomically
        3. Create temporary file with secure permissions
        4. Write curl options atomically
        5. Verify permissions and content
        6. Return file path
    """
    # curl_options: List of curl-related keywords for autocomplete
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
        'curl', 'curl.exe', 'https://', 'http://', 'localhost', '127.0.0.1'
    ]

    debug_print(f"Creating curl dictionary with {len(curl_options)} entries")
    
    # Set secure umask
    old_umask = os.umask(0o077)
    debug_print(f"Set secure umask: 0o077 (old umask was: {oct(old_umask)})")
    
    try:
        # Create temporary directory with secure permissions
        debug_print("Creating temporary directory for dictionary")
        tdir = tempfile.mkdtemp()
        debug_print(f"Created temp directory: {tdir}")
        
        # Verify directory permissions
        dir_stat = os.stat(tdir)
        dir_mode = stat.S_IMODE(dir_stat.st_mode)
        debug_print(f"Directory permissions: {oct(dir_mode)} (expected: 0o700)")
        if dir_mode != 0o700:
            debug_print(f"Forcing secure permissions on dict temp directory: {tdir}")
            os.chmod(tdir, 0o700)
            debug_print(f"Forced secure permissions on dict temp directory: {tdir}")
        
        # Create temporary dictionary file atomically
        debug_print(f"Creating temporary dictionary file in directory: {tdir}")
        fd, dict_tmp = tempfile.mkstemp(suffix=".dict", dir=tdir)
        debug_print(f"Created temp dictionary file: {dict_tmp} (fd: {fd})")
        
        try:
            # Set file permissions to 0o600
            debug_print(f"Setting dictionary file permissions to 0o600")
            os.fchmod(fd, 0o600)
            
            # Write dictionary content atomically via file descriptor
            debug_print(f"Writing {len(curl_options)} dictionary entries to file")
            total_bytes = 0
            with os.fdopen(fd, 'w') as f:
                for option in curl_options:
                    bytes_written = f.write(f"{option}\n")
                    total_bytes += bytes_written
            debug_print(f"Wrote {total_bytes} bytes ({len(curl_options)} entries) to dictionary file")
            
            # Verify file permissions
            file_stat = os.stat(dict_tmp)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            debug_print(f"Dictionary file permissions after write: {oct(file_mode)} (expected: 0o600)")
            if file_mode != 0o600:
                debug_print(f"WARNING: Dictionary file permissions mismatch! Expected 0o600, got {oct(file_mode)}")
                print_error(f"Failed to set secure permissions on dictionary file: {dict_tmp}")
            
            # Add to cleanup list AFTER successful write
            temp_files.append(dict_tmp)
            debug_print(f"Added dictionary file to cleanup list (total temp files: {len(temp_files)})")
            debug_print(f"Created secure curl dictionary at: {dict_tmp} with {len(curl_options)} entries (mode: 0o600)")
            
            # Verify content if DEBUG enabled
            if DEBUG:
                debug_print("Verifying dictionary file content...")
                with open(dict_tmp, 'r') as vf:
                    lines = vf.readlines()
                    debug_print(f"Dictionary file verified: {len(lines)} lines, first 5: {[l.strip() for l in lines[:5]]}")
            
            return dict_tmp
            
        except OSError as e:
            # Clean up file on error
            try:
                os.unlink(dict_tmp)
            except OSError:
                pass
            print_error(f"Failed to create dictionary file: {e}")
            
    finally:
        # Restore original umask
        os.umask(old_umask)

