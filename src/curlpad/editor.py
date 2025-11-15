"""
Editor configuration and launching for curlpad.

This module handles editor-related functionality:
    - create_editor_config(): Creates Vim/Neovim configuration files
    - open_editor(): Launches the editor with the template file

Functions:
    create_editor_config(target_file: str) -> str
        Create temporary vimrc/lua file with curl completion settings
        
    open_editor(tmpfile: str) -> None
        Launch editor (nvim/vim) with template file and autocomplete config

Flow:
    1. get_editor() detects available editor (nvim preferred over vim)
    2. create_editor_config() creates editor-specific config file
    3. open_editor() launches editor with config and template file
    4. User edits commands in editor
    5. Editor closes, control returns to main flow
"""

import os
import subprocess
import tempfile

from curlpad.dependencies import get_editor
from curlpad.output import print_error
from curlpad.templates import create_curl_dict
from curlpad.utils import temp_files, debug_print, DEBUG


def sanitize_lua_string(s: str) -> str:
    """
    Escape string for safe Lua interpolation.
    
    Prevents Lua code injection by escaping special characters.
    
    Args:
        s: String to sanitize
        
    Returns:
        Sanitized string safe for Lua string literals
    """
    # Escape backslashes first
    s = s.replace('\\', '\\\\')
    # Escape Lua string terminators
    s = s.replace(']]', ']]..[[')
    return s


def sanitize_vim_string(s: str) -> str:
    """
    Escape string for safe Vimscript interpolation.
    
    Prevents Vimscript injection by escaping special characters.
    
    Args:
        s: String to sanitize
        
    Returns:
        Sanitized string safe for Vimscript string literals
    """
    # Escape backslashes first
    s = s.replace('\\', '\\\\')
    # Escape double quotes
    s = s.replace('"', '\\"')
    # Escape single quotes
    s = s.replace("'", "\\'")
    return s


def create_editor_config(target_file: str) -> str:
    """
    Create temporary vimrc/lua file with curl completion settings.
    
    Creates editor-specific configuration files with secure path handling:
        - Neovim: Lua configuration file (.lua)
        - Vim: Vimscript configuration file (.vimrc)
    
    The configuration enables:
        - Dictionary-based autocomplete for curl options
        - Syntax highlighting
        - Proper indentation settings
        - Keyboard shortcuts (Ctrl+Space or Ctrl+X Ctrl+K for completion)
    
    Security:
        - Validates target_file is under temp directory
        - Sanitizes paths to prevent code injection
        - Escapes special characters in Lua/Vimscript strings
    
    Args:
        target_file: Path to the template file being edited
                    Must be under system temp directory
        
    Returns:
        Path to the created configuration file
        
    Raises:
        SystemExit: If config file creation fails
        ValueError: If target_file path is invalid
        
    Flow:
        1. Validate target_file path
        2. Create curl dictionary file for autocomplete
        3. Detect editor type (nvim or vim)
        4. Sanitize paths for safe interpolation
        5. Generate editor-specific config content
        6. Create temporary config file (.lua or .vimrc)
        7. Add file to temp_files list
        8. Return config file path
    """
    debug_print(f"create_editor_config called with target_file: {target_file}")
    
    # Validate target_file is under temp directory (prevent path traversal)
    target_file_abs = os.path.abspath(target_file)
    temp_dir = tempfile.gettempdir()
    debug_print(f"Target file absolute path: {target_file_abs}")
    debug_print(f"Temp directory: {temp_dir}")
    
    if not target_file_abs.startswith(temp_dir):
        debug_print(f"SECURITY ERROR: Path traversal attempt detected!")
        debug_print(f"  Target: {target_file_abs}")
        debug_print(f"  Temp dir: {temp_dir}")
        raise ValueError(f"Invalid target file path: {target_file_abs} (not under temp directory)")
    
    debug_print(f"Path validation passed: {target_file_abs}")
    
    # Create curl dictionary file
    debug_print("Creating curl dictionary file...")
    dict_file = create_curl_dict()
    debug_print(f"Dictionary file created: {dict_file}")
    
    # Detect editor
    debug_print("Detecting available editor...")
    editor = get_editor()
    debug_print(f"Selected editor: {editor}")

    if editor == 'nvim':
        # Neovim Lua configuration with sanitized paths
        debug_print("Sanitizing paths for Lua interpolation...")
        dict_file_safe = sanitize_lua_string(dict_file)
        target_file_safe = sanitize_lua_string(target_file_abs)
        debug_print(f"Sanitized dict_file: {len(dict_file_safe)} chars")
        debug_print(f"Sanitized target_file: {len(target_file_safe)} chars")
        
        debug_print("Generating Neovim Lua configuration...")
        config_content = f'''-- Neovim Lua configuration for curl completion
local dict_file = [[{dict_file_safe}]]
local target_path = [[{target_file_safe}]]

-- Enable syntax highlighting
vim.cmd('syntax on')

-- Basic UI/options
vim.o.number = true
vim.o.autoindent = true
vim.o.tabstop = 2
vim.o.shiftwidth = 2
vim.o.expandtab = true
vim.o.backspace = 'indent,eol,start'

-- Enable truecolor and try to apply a builtin colorscheme
vim.o.termguicolors = true
pcall(vim.cmd, 'colorscheme elflord')

-- Enable filetype detection, plugins, indent
vim.cmd('filetype plugin indent on')

-- Function to setup buffer
local function setup_buffer(buf)
  vim.bo[buf].filetype = 'sh'
  -- Clear and set dictionary
  vim.opt_local.dictionary = {{ dict_file }}
  vim.opt_local.complete:append('k')
  vim.opt_local.completeopt = {{ 'menu', 'menuone', 'preview' }}
  -- Map Ctrl-Space to trigger dictionary completion for this buffer
  pcall(vim.keymap.set, 'i', '<C-Space>', '<C-x><C-k>', {{ buffer = buf, noremap = true, silent = true }})
  -- Debug: verify settings
  local dict_setting = vim.opt_local.dictionary:get()
  local complete_setting = vim.opt_local.complete:get()
  vim.api.nvim_echo({{
    {{ 'Curl autocomplete: Ctrl+Space or Ctrl+X Ctrl+K', 'Normal' }},
    {{ '  Dictionary: ' .. (dict_setting[1] or 'not set'), 'Comment' }},
    {{ '  Complete: ' .. table.concat(complete_setting, ','), 'Comment' }}
  }}, true, {{}})
end

-- Apply to current buffer immediately
vim.schedule(function()
  local current_buf = vim.api.nvim_get_current_buf()
  setup_buffer(current_buf)
end)

-- Also setup on buffer events
vim.api.nvim_create_autocmd({{ 'BufEnter', 'BufWinEnter' }}, {{
  callback = function(args)
    setup_buffer(args.buf)
  end,
  once = false,
}})
'''
        suffix = '.lua'
    else:
        # Vimscript configuration with sanitized paths
        debug_print("Sanitizing paths for Vimscript interpolation...")
        dict_file_safe = sanitize_vim_string(dict_file)
        debug_print(f"Sanitized dict_file: {len(dict_file_safe)} chars")
        
        debug_print("Generating Vimscript configuration...")
        config_content = f'''set nocompatible
syntax on
filetype plugin indent on
set filetype=sh
set number
set autoindent
set tabstop=2
set shiftwidth=2
set expandtab
set backspace=indent,eol,start

" Enable dictionary completion for curl commands
set dictionary={dict_file_safe}
set complete+=k
set completeopt=menu,menuone,preview

" Show helpful message
echo "Curl autocomplete available: Press Ctrl+X Ctrl+K in insert mode for completion"
'''
        suffix = '.vimrc'

    # Create temporary config file
    # fd: File descriptor (integer) for the opened file
    # config_tmp: Path to the created temporary config file
    # suffix: File extension (.lua for Neovim, .vimrc for Vim)
    debug_print(f"Creating temporary config file with suffix: {suffix}")
    fd, config_tmp = tempfile.mkstemp(suffix=suffix)
    debug_print(f"Created temp config file: {config_tmp} (fd: {fd})")
    
    # Add config file to temp_files list for automatic cleanup on exit
    temp_files.append(config_tmp)
    debug_print(f"Added config file to cleanup list (total temp files: {len(temp_files)})")
    debug_print(f"Created editor config at: {config_tmp} (editor={editor}, suffix={suffix})")

    try:
        # Write config content to file
        # os.fdopen(): Convert file descriptor to file object
        # 'w': Write mode (text mode)
        debug_print(f"Writing config content ({len(config_content)} bytes) to file...")
        with os.fdopen(fd, 'w') as f:
            bytes_written = f.write(config_content)
            debug_print(f"Wrote {bytes_written} bytes to config file")
        
        # If DEBUG mode is enabled, output config file content for debugging
        if DEBUG:
            # lines: List of lines from config content (split by newline)
            lines = config_content.split('\n')
            debug_print(f"Config file content ({len(config_content)} bytes, {len(lines)} lines):")
            # Output first 20 lines with line numbers
            for i, line in enumerate(lines[:20], 1):
                debug_print(f"  {i:3d}: {line}")
            total_lines = len(lines)
            if total_lines > 20:
                remaining_lines = total_lines - 20
                debug_print(f"  ... ({remaining_lines} more lines)")
    except OSError as e:
        debug_print(f"ERROR: Failed to create config file: {type(e).__name__}: {e}")
        print_error(f"Failed to create config file: {e}")

    debug_print(f"Editor config file created successfully: {config_tmp}")
    return config_tmp


def open_editor(tmpfile: str) -> None:
    """
    Launch editor (nvim/vim) with template file and autocomplete configuration.
    
    Opens the editor with the template file and applies the autocomplete
    configuration. The editor is launched with the cursor positioned at
    line 8 (where the empty line is in the template) in insert mode.
    
    Args:
        tmpfile: Path to the template file to edit
        
    Raises:
        SystemExit: If editor launch fails or editor not found
        
    Flow:
        1. Get available editor (nvim or vim)
        2. Create editor configuration file
        3. Build editor command with config and template file
        4. Launch editor as subprocess
        5. Wait for editor to close
        6. Clean up config file
    """
    debug_print(f"open_editor called with tmpfile: {tmpfile}")
    
    # editor: Editor name ('nvim' or 'vim')
    # Detected by get_editor() in dependencies.py
    debug_print("Getting available editor...")
    editor = get_editor()
    debug_print(f"Editor selected: {editor}")
    
    # config_tmp: Path to editor configuration file
    # Created by create_editor_config() with curl autocomplete settings
    # Contains editor-specific config (Lua for Neovim, Vimscript for Vim)
    debug_print("Creating editor configuration file...")
    config_tmp = create_editor_config(tmpfile)
    debug_print(f"Editor config created: {config_tmp}")

    try:
        if editor == 'nvim':
            # Neovim command with Lua config
            # cmd: List of command arguments to launch Neovim
            # --clean: Start with clean environment (no user config)
            # -u NONE: Don't load any user config files
            # tmpfile: Template file to edit
            # -c 'luafile {config_tmp}': Execute Lua config file after loading
            # -c 'doautocmd BufEnter': Trigger BufEnter event (applies buffer settings)
            # +8: Go to line 8 (where curl/curl.exe is)
            # -c 'normal $': Move cursor to end of line (after curl/curl.exe)
            # +startinsert: Start in insert mode
            debug_print("Building Neovim command with Lua config")
            cmd = [editor, '--clean', '-u', 'NONE', tmpfile, '-c', f'luafile {config_tmp}', '-c', 'doautocmd BufEnter', '+8', '-c', 'normal $', '+startinsert']
        else:
            # Vim command with vimrc
            # cmd: List of command arguments to launch Vim
            # -u {config_tmp}: Use config file as vimrc
            # +8: Go to line 8 (where curl/curl.exe is)
            # -c 'normal $': Move cursor to end of line (after curl/curl.exe)
            # +startinsert: Start in insert mode
            # tmpfile: Template file to edit
            debug_print("Building Vim command with vimrc config")
            cmd = [editor, '-u', config_tmp, '+8', '-c', 'normal $', '+startinsert', tmpfile]
        
        debug_print(f"Editor command: {' '.join(cmd)}")
        debug_print(f"Launching editor as subprocess (will block until editor closes)...")
        
        # result: CompletedProcess object from subprocess.run()
        # check=True: Raise exception if editor exits with non-zero code
        # This blocks until editor closes (user saves and quits)
        result = subprocess.run(cmd, check=True)
        debug_print(f"Editor closed with returncode: {result.returncode}")
    except subprocess.CalledProcessError as e:
        # Editor exited with error (non-zero exit code)
        debug_print(f"Editor exited with error: returncode={e.returncode}, cmd={e.cmd}")
        print_error(f"Editor exited with error: {e}")
    except FileNotFoundError:
        # Editor executable not found in PATH
        debug_print(f"Editor '{editor}' not found in PATH")
        print_error(f"Editor '{editor}' not found.")
    finally:
        # Clean up config file
        # Always remove config file, even if editor launch failed
        # This prevents leaving temporary files behind
        try:
            debug_print(f"Cleaning up editor config file: {config_tmp}")
            os.unlink(config_tmp)  # Delete config file
            temp_files.remove(config_tmp)  # Remove from temp_files list
            debug_print(f"Editor config file removed (remaining temp files: {len(temp_files)})")
        except OSError as e:
            debug_print(f"Error removing editor config file: {e} (may already be deleted)")
            pass  # Ignore errors (file may already be deleted)

