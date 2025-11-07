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


def create_editor_config(target_file: str) -> str:
    """
    Create temporary vimrc/lua file with curl completion settings.
    
    Creates editor-specific configuration files:
        - Neovim: Lua configuration file (.lua)
        - Vim: Vimscript configuration file (.vimrc)
    
    The configuration enables:
        - Dictionary-based autocomplete for curl options
        - Syntax highlighting
        - Proper indentation settings
        - Keyboard shortcuts (Ctrl+Space or Ctrl+X Ctrl+K for completion)
    
    Args:
        target_file: Path to the template file being edited
                    Used for buffer-specific configuration
        
    Returns:
        Path to the created configuration file
        
    Raises:
        SystemExit: If config file creation fails
        
    Flow:
        1. Create curl dictionary file for autocomplete
        2. Detect editor type (nvim or vim)
        3. Generate editor-specific config content
        4. Create temporary config file (.lua or .vimrc)
        5. Add file to temp_files list
        6. Return config file path
    """
    # dict_file: Path to dictionary file containing curl options for autocomplete
    # Created by create_curl_dict() in templates.py
    # Contains curl options, HTTP methods, headers, etc. (one per line)
    dict_file = create_curl_dict()
    
    # editor: Editor name ('nvim' or 'vim')
    # Detected by get_editor() in dependencies.py
    # Prefers nvim over vim for better Lua support
    editor = get_editor()

    if editor == 'nvim':
        # Neovim Lua configuration
        # Uses Lua API for better integration with Neovim
        config_content = f'''-- Neovim Lua configuration for curl completion
local dict_file = [[{dict_file}]]
local target_path = [[{target_file}]]

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
        # Vimscript configuration for regular Vim
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
set dictionary={dict_file}
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
    fd, config_tmp = tempfile.mkstemp(suffix=suffix)
    
    # Add config file to temp_files list for automatic cleanup on exit
    temp_files.append(config_tmp)
    debug_print(f"Created editor config at: {config_tmp} (editor={editor}, suffix={suffix})")

    try:
        # Write config content to file
        # os.fdopen(): Convert file descriptor to file object
        # 'w': Write mode (text mode)
        with os.fdopen(fd, 'w') as f:
            f.write(config_content)
        
        # If DEBUG mode is enabled, output config file content for debugging
        if DEBUG:
            # lines: List of lines from config content (split by newline)
            lines = config_content.split('\n')
            debug_print(f"Config file content ({len(config_content)} bytes):")
            # Output first 20 lines with line numbers
            for i, line in enumerate(lines[:20], 1):
                debug_print(f"  {i:3d}: {line}")
            total_lines = len(lines)
            if total_lines > 20:
                remaining_lines = total_lines - 20
                debug_print(f"  ... ({remaining_lines} more lines)")
    except OSError as e:
        print_error(f"Failed to create config file: {e}")

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
    # editor: Editor name ('nvim' or 'vim')
    # Detected by get_editor() in dependencies.py
    editor = get_editor()
    
    # config_tmp: Path to editor configuration file
    # Created by create_editor_config() with curl autocomplete settings
    # Contains editor-specific config (Lua for Neovim, Vimscript for Vim)
    config_tmp = create_editor_config(tmpfile)

    try:
        if editor == 'nvim':
            # Neovim command with Lua config
            # cmd: List of command arguments to launch Neovim
            # --clean: Start with clean environment (no user config)
            # -u NONE: Don't load any user config files
            # tmpfile: Template file to edit
            # -c 'luafile {config_tmp}': Execute Lua config file after loading
            # -c 'doautocmd BufEnter': Trigger BufEnter event (applies buffer settings)
            # +8: Go to line 8 (empty line in template)
            # +startinsert: Start in insert mode
            cmd = [editor, '--clean', '-u', 'NONE', tmpfile, '-c', f'luafile {config_tmp}', '-c', 'doautocmd BufEnter', '+8', '+startinsert']
        else:
            # Vim command with vimrc
            # cmd: List of command arguments to launch Vim
            # -u {config_tmp}: Use config file as vimrc
            # +8: Go to line 8 (empty line in template)
            # +startinsert: Start in insert mode
            # tmpfile: Template file to edit
            cmd = [editor, '-u', config_tmp, '+8', '+startinsert', tmpfile]
        
        debug_print(f"Launching editor with command: {' '.join(cmd)}")
        
        # result: CompletedProcess object from subprocess.run()
        # check=True: Raise exception if editor exits with non-zero code
        # This blocks until editor closes (user saves and quits)
        result = subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        # Editor exited with error (non-zero exit code)
        print_error(f"Editor exited with error: {e}")
    except FileNotFoundError:
        # Editor executable not found in PATH
        print_error(f"Editor '{editor}' not found.")
    finally:
        # Clean up config file
        # Always remove config file, even if editor launch failed
        # This prevents leaving temporary files behind
        try:
            debug_print(f"Removing editor config: {config_tmp}")
            os.unlink(config_tmp)  # Delete config file
            temp_files.remove(config_tmp)  # Remove from temp_files list
        except OSError:
            pass  # Ignore errors (file may already be deleted)

