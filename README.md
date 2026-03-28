## curlpad

A tiny terminal scratchpad for crafting and running `curl` commands with Vim/Neovim autocomplete.

### Install

**Windows (PowerShell):**

```powershell
# Quick install (recommended)
irm curlpad-installer.gossorg.in/install.ps1 | iex

# Or download and inspect first
Invoke-WebRequest -Uri curlpad-installer.gossorg.in/install.ps1 -OutFile install.ps1
.\install.ps1
```

**Linux/macOS (Bash):**

```bash
# Quick install (recommended)
curl -fsSL curlpad-installer.gossorg.in/install.sh | bash

# Or download and inspect first
curl -fsSL curlpad-installer.gossorg.in/install.sh -o install.sh
chmod +x install.sh
./install.sh
```

**From source:**

```bash
# Linux/macOS
./scripts/install_curlpad.sh           # user install (~/.local/bin)
./scripts/install_curlpad.sh --sudo    # system-wide (/usr/local/bin)

# Windows
.\scripts\install_curlpad.ps1
```

**PATH setup:**

- **Linux/macOS:** If `~/.local/bin` is not on PATH:
  ```bash
  export PATH="$HOME/.local/bin:$PATH"
  ```

- **Windows:** The installer will prompt you to add to PATH automatically.

### Build from source

```bash
make build
# or
./scripts/build_curlpad.sh
```

Artifacts are placed in `dist/`.

### Usage

```bash
curlpad           # open editor at a scratch file with curl completions
curlpad --help    # options
curlpad --version # version
curlpad --dry-run # edit commands, then show without running
```

Inside the editor:
- Autocomplete triggers automatically as you type (2+ characters)
- Press Tab / Shift+Tab to navigate completion suggestions (Tab still inserts normal indentation when no completion is available)
- Ctrl+Space or Ctrl+X Ctrl+K for manual completion trigger
- Press Up / Down arrows to recall previous commands from history
- Uncomment/edit example lines, then save and exit to run

### Config file

Create `~/.curlpadrc` to set defaults:

```bash
# ~/.curlpadrc
DEFAULT_URL=https://api.example.com
AUTO_FORMAT_JSON=true
```

| Setting | Description |
|---------|-------------|
| `DEFAULT_URL` | Pre-populate the curl template with this URL |
| `AUTO_FORMAT_JSON` | Auto-format JSON output with jq (`true`/`false`, default: `true`) |

CLI flags (`--url`, etc.) override config file values.

### History

curlpad saves the last 20 executed commands to `~/.curlpad/history`.
Use the Up / Down arrows in the editor to recall them.

### Requirements

- **Windows:** PowerShell 5.0+, `curl` (required), `vim` or `nvim` (one required)
- **Linux/macOS:** `curl` (required), `vim` or `nvim` (one required)
- `jq` (optional, for JSON formatting)

### License

GPL-3.0-or-later. See SPDX identifier in source files.

### Author

Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>