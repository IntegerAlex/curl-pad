"""
Dependency management for curlpad.

This module handles checking for and installing required dependencies:
    - curl: Required for executing HTTP requests
    - vim/nvim: Required for editing commands
    - jq: Optional, used for JSON formatting

Functions:
    check_command(command: str) -> bool
        Check if a command exists in the system PATH
        
    get_editor() -> str
        Detect and return available editor (prefers nvim over vim)
        
    check_dependencies() -> None
        Verify that required dependencies (curl) are installed
        
    install_deps() -> None
        Install missing dependencies (vim, jq) using platform-specific package managers

Flow:
    1. check_dependencies() verifies curl is installed
    2. get_editor() detects nvim or vim
    3. install_deps() can install vim/jq if --install flag is used
"""

import platform
import shutil
import subprocess

from curlpad.output import print_error, print_info, print_success
from curlpad.utils import debug_print


def check_command(command: str) -> bool:
    """
    Check if a command exists in the system PATH.
    
    Uses shutil.which() to search for the command in PATH.
    Logs the result when DEBUG mode is enabled.
    
    Args:
        command: Command name to check (e.g., 'curl', 'vim', 'nvim')
                 This is the base command name without path or extension
                 
    Returns:
        True if command is found in PATH, False otherwise
        
    Variables:
        path: Full path to the command executable, or None if not found
              Returned by shutil.which() which searches PATH environment variable
              
    Flow:
        1. Call shutil.which(command) to search PATH
        2. Log result if DEBUG mode enabled
        3. Return True if path is not None, False otherwise
        
    Usage:
        if check_command('curl'):
            print("curl is installed")
    """
    # path: Full path to command executable, or None if command not found in PATH
    # shutil.which() searches the PATH environment variable for the command
    # On Windows, also checks .exe, .cmd, .bat extensions automatically
    path = shutil.which(command)
    debug_print(f"Check command '{command}': {'found at ' + path if path else 'not found'}")
    return path is not None


def get_editor() -> str:
    """
    Detect and return available editor (prefers nvim over vim).
    
    Checks for editors in order of preference:
        1. nvim (Neovim) - preferred for better Lua support
        2. vim (Vim) - fallback option
        
    Returns:
        Editor name as string ('nvim' or 'vim')
        
    Raises:
        SystemExit: If neither editor is found
        
    Flow:
        1. Check for 'nvim' in PATH
        2. If not found, check for 'vim' in PATH
        3. If neither found, print error and exit
    """
    if check_command('nvim'):
        debug_print("Selected editor: nvim")
        return 'nvim'
    elif check_command('vim'):
        debug_print("Selected editor: vim")
        return 'vim'
    else:
        print_error("Neither nvim nor vim is installed.\nRun 'python3 curlpad.py --install' to install dependencies.")


def check_dependencies() -> None:
    """
    Verify that required dependencies are installed.
    
    Currently only checks for 'curl' as it's the only hard requirement.
    Other dependencies (vim/nvim, jq) are checked when needed.
    
    Raises:
        SystemExit: If curl is not installed
        
    Flow:
        1. Check if 'curl' command exists in PATH
        2. If not found, print error and exit
    """
    if not check_command('curl'):
        print_error("curl is not installed. Please install curl first.")


def install_deps() -> None:
    """
    Install missing dependencies (vim, jq) using platform-specific package managers.
    
    Supports multiple platforms and package managers:
        - Linux: apt-get (Debian/Ubuntu), dnf (Fedora), yum (RHEL/CentOS)
        - macOS: Homebrew
        
    Raises:
        SystemExit: If platform is unsupported or installation fails
        
    Variables:
        system: Operating system name in lowercase ('linux', 'darwin', 'windows', etc.)
                Detected via platform.system().lower()
                Used to determine which package manager to use
        
    Flow:
        1. Detect platform (linux/darwin)
        2. Detect package manager (apt-get/dnf/yum/brew)
        3. Run package manager commands to install vim and jq
        4. Print success message
        
    Usage:
        Called via --install CLI flag
    """
    print_info("Installing missing dependencies...")

    # system: Operating system name in lowercase
    # platform.system() returns: 'Linux', 'Darwin', 'Windows', etc.
    # .lower() converts to lowercase for case-insensitive comparison
    # Used to determine which package manager and installation commands to use
    system = platform.system().lower()
    debug_print(f"Detected platform: {system}")
    
    if system == "linux":
        # Try different package managers
        if check_command('apt-get'):
            # Debian/Ubuntu
            debug_print("Using apt-get for installation")
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'vim', 'jq'], check=True)
        elif check_command('dnf'):
            # RHEL/CentOS/Fedora
            debug_print("Using dnf for installation")
            subprocess.run(['sudo', 'dnf', 'install', '-y', 'vim', 'jq'], check=True)
        elif check_command('yum'):
            # Older RHEL/CentOS
            debug_print("Using yum for installation")
            subprocess.run(['sudo', 'yum', 'install', '-y', 'vim', 'jq'], check=True)
        else:
            print_error("Cannot auto-install: unsupported package manager.\nPlease install vim and jq manually:\n  Ubuntu/Debian: sudo apt install vim jq\n  RHEL/CentOS: sudo yum install vim jq")
    elif system == "darwin":
        # macOS
        if check_command('brew'):
            debug_print("Using Homebrew for installation")
            subprocess.run(['brew', 'install', 'vim', 'jq'], check=True)
        else:
            print_error("Cannot auto-install: Homebrew not found.\nPlease install Homebrew and run: brew install vim jq")
    else:
        print_error(f"Unsupported platform: {system}")

    print_success("Dependencies installed.")

