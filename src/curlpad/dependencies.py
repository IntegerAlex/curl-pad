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

from curlpad.output import print_error, print_info, print_success, print_warning
from curlpad.utils import debug_print

# Trusted absolute paths for package managers (security: prevent PATH hijacking)
TRUSTED_BINARIES = {
    'apt-get': '/usr/bin/apt-get',
    'dnf': '/usr/bin/dnf',
    'yum': '/usr/bin/yum',
    'brew': '/usr/local/bin/brew',
    'sudo': '/usr/bin/sudo'
}


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


def verify_binary(name: str) -> str:
    """
    Verify binary is in expected trusted location.
    
    Prevents PATH hijacking attacks by ensuring package managers
    are in their standard system locations.
    
    Args:
        name: Binary name to verify (e.g., 'apt-get', 'dnf', 'sudo')
        
    Returns:
        Absolute path to the verified binary
        
    Raises:
        RuntimeError: If binary not found or in unexpected location
    """
    expected_path = TRUSTED_BINARIES.get(name)
    if not expected_path:
        raise ValueError(f"Unknown binary: {name}")
    
    actual_path = shutil.which(name)
    
    if not actual_path:
        raise RuntimeError(f"Binary '{name}' not found in PATH")
    
    if actual_path != expected_path:
        print_warning(f"Binary {name} found at unexpected location:")
        print_warning(f"  Expected: {expected_path}")
        print_warning(f"  Found:    {actual_path}")
        print_warning("This could indicate a PATH hijacking attempt.")
        
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            raise RuntimeError("Installation aborted by user due to unexpected binary location")
        
        debug_print(f"User approved non-standard binary location for {name}")
    
    return actual_path


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
    Install missing dependencies (vim, jq) using verified package managers.
    
    Supports multiple platforms and package managers with security verification:
        - Linux: apt-get (Debian/Ubuntu), dnf (Fedora), yum (RHEL/CentOS)
        - macOS: Homebrew
        
    Security:
        - Verifies package manager binaries are in trusted locations
        - Uses absolute paths to prevent PATH hijacking
        - Validates binary locations before execution
        
    Raises:
        SystemExit: If platform is unsupported or installation fails
        RuntimeError: If binary verification fails
        
    Flow:
        1. Detect platform (linux/darwin)
        2. Detect and verify package manager location
        3. Run package manager with absolute path
        4. Print success message
        
    Usage:
        Called via --install CLI flag
    """
    print_info("Installing missing dependencies...")

    system = platform.system().lower()
    debug_print(f"Detected platform: {system}")
    
    try:
        if system == "linux":
            # Try different package managers
            if check_command('apt-get'):
                # Debian/Ubuntu - verify binaries before use
                debug_print("Using apt-get for installation")
                sudo_path = verify_binary('sudo')
                apt_path = verify_binary('apt-get')
                
                print_info("Running: sudo apt-get update")
                subprocess.run([sudo_path, apt_path, 'update'], check=True)
                
                print_info("Running: sudo apt-get install -y vim jq")
                subprocess.run([sudo_path, apt_path, 'install', '-y', 'vim', 'jq'], check=True)
                
            elif check_command('dnf'):
                # RHEL/CentOS/Fedora
                debug_print("Using dnf for installation")
                sudo_path = verify_binary('sudo')
                dnf_path = verify_binary('dnf')
                
                print_info("Running: sudo dnf install -y vim jq")
                subprocess.run([sudo_path, dnf_path, 'install', '-y', 'vim', 'jq'], check=True)
                
            elif check_command('yum'):
                # Older RHEL/CentOS
                debug_print("Using yum for installation")
                sudo_path = verify_binary('sudo')
                yum_path = verify_binary('yum')
                
                print_info("Running: sudo yum install -y vim jq")
                subprocess.run([sudo_path, yum_path, 'install', '-y', 'vim', 'jq'], check=True)
            else:
                print_error("Cannot auto-install: unsupported package manager.\nPlease install vim and jq manually:\n  Ubuntu/Debian: sudo apt install vim jq\n  RHEL/CentOS: sudo yum install vim jq")
                
        elif system == "darwin":
            # macOS
            if check_command('brew'):
                debug_print("Using Homebrew for installation")
                brew_path = verify_binary('brew')
                
                print_info("Running: brew install vim jq")
                subprocess.run([brew_path, 'install', 'vim', 'jq'], check=True)
            else:
                print_error("Cannot auto-install: Homebrew not found.\nPlease install Homebrew and run: brew install vim jq")
        else:
            print_error(f"Unsupported platform: {system}")
        
        print_success("Dependencies installed.")
        
    except RuntimeError as e:
        print_error(f"Installation failed: {e}")
    except subprocess.CalledProcessError as e:
        print_error(f"Package manager command failed: {e}")

